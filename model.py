from importlib import util
from pathlib import Path
import ast
import inspect
from nodeCollector import ConstantCollector, ImportCollector, SectionCollector,\
    IntegralCollector, VarType, VarlistCollector
from segment import SegmentLabel, ModelSegment, Section, SegmentationError,\
    ModelSegments
from nodeWraps import NodeWrap, CSMPWrap
from template import TemplateBuilder
from sorter import Sorter
from templates.simulationModelTemplate import SimulationModelTemplate
import keywords
from keywords import CSMP_Function
from lister import Lister
import sys
import traceback
import copy
import macros
from macros import MacroCollector, MacroExpander
from errors import PrecompilerError

class ModelLoader:
    
    def __init__(self, fileName):
        path = Path(fileName)
        name = path.stem.replace(".", "_")
        spec = util.spec_from_file_location(name, path)
        self.file    = path
        self.module  = util.module_from_spec(spec)
        try:    spec.loader.exec_module(self.module)
        except: pass
        

    def getGlobals(self, filtered = True):
        result = vars(self.module)
        return result if not filtered else dict([(k, v) for k, v in result.items() if not k.startswith("_")])


    def getSource(self):
        return inspect.getsource(self.module)
        
        
    def saveList(self, file = None):
        
        def write(f):
            Lister().report(self.getSource(), file = f)
            print("\n\n%8d error(s)\n%8d warning(s)" % Lister().count(), file = f)
            
        if file is None:
            path = self.file.with_suffix(".lst")
            with path.open("w") as f:
                write(f)
        else:
            write(file)
            
                    
    def getSyntaxTree(self):
        return ast.parse(self.getSource())
        



class Model:

    def __init__(self, sourceFile):
        self.loader     = ModelLoader(sourceFile)
        self.ast        = self.loader.getSyntaxTree()
        self.succes     = False
        self.processCode()
        self.results    = Lister().count()
        self.succes     = (self.results[0] == 0)
        

    def processCode(self):
        Lister().start()
        try:
            self._macroExpansion()
            self._collectDeclarations()
            self._modelSegmentation()
            self._assignStatements()
            self._sortCodeBlocks()
            self._writeTemplate()
        except PrecompilerError as e:
            Lister().addError("parsing of the source code failed", -1, "processCode")
    
    
    @Lister.withContextError
    def _macroExpansion(self):
        self.macros = MacroCollector().run(self.ast)
        macros = dict([(m.name, m) for m in self.macros])
        MacroExpander().run(self.ast, macros)
        
        
    @Lister.withContextError
    def _modelSegmentation(self):
        self.segments = ModelSegments(self.ast)
    
            
    @Lister.withContextError
    def _collectDeclarations(self):
        self.init    = []
        self.imports = ImportCollector().run(self.ast)
        self.consts  = ConstantCollector().run(self.ast, VarType.CONSTANT)
        self.incons  = ConstantCollector().run(self.ast, VarType.INCON)
        self.params  = ConstantCollector().run(self.ast, VarType.PARAM)
        self.consts += VarlistCollector().run(self.ast, VarType.CONSTANT, self.consts)
        self.incons += VarlistCollector().run(self.ast, VarType.INCON, self.incons)
        self.params += VarlistCollector().run(self.ast, VarType.PARAM, self.params)
        self.states  = IntegralCollector().run(self.ast)
        self.readOnly= dict([(wrap.name, wrap.varType)
                            for wrap in self.consts 
                                      + self.incons 
                                      + self.params
                                      + self.states])
        
    
    def _wrapNode(self, node):
        if isinstance(node.value, ast.Name):
            info = CSMP_Function.keywordInfo(node.value.id)
        elif isinstance(node.value, ast.Call):
            info = CSMP_Function.keywordInfo(node.value.func.id)
        else:
            info = {}

        if info:
            wrap = CSMPWrap(node, **info) 
            return wrap if wrap.status >= 0 else None
            # return CSMPWrap(node, **info) if info.get('status', -999) >= 0 else None
        else:   
            return NodeWrap(node)
    
        
    def _validateStatement(self, statement):
        constants = (VarType.PARAM, VarType.INCON, VarType.CONSTANT)
        node = statement.node
        if isinstance(node, ast.Assign):
            for n in ast.walk(node.targets[0]):
                if isinstance(n, ast.Name): 
                    varType = self.readOnly.get(n.id, -1)
                    if varType in constants:
                        statement.addRemark("'%s' is immutable while it has been declared %s" % (n.id, varType.name), 
                                            originator = "validate")
                    elif (varType == VarType.INTGRL) and not IntegralCollector.matches(node):
                        statement.addRemark("'%s' is immutable while it has been declared %s" % (n.id, "INTGRL"), 
                                            originator = "validate")
                 
                    
    @Lister.withContextError
    def _assignStatements(self):
        for node in self.ast.body:
            statement = self._wrapNode(node)
            if statement is None: 
                continue # ignore this one
            line    = statement.getLineNumber()
            if line < 0:
                self.init.append(statement)
            else:
                for segment in self.segments:
                    if segment.contains(line): 
                        segment.appendStatement(statement)
                        self._validateStatement(statement)
                        break
                else: # if not assigned ...
                    raise SegmentationError("line %d could not be assigend to a model segment" % line)


    @Lister.withContextError
    def _sortCodeBlocks(self):
        codeSorter  = Sorter()
        codeSorter.useImports(self.imports)
        codeSorter.sort(self.consts, blockID = "sorter: constant section")
        codeSorter.sort(self.params, blockID = "sorter: parameter section")
        codeSorter.sort(self.incons, blockID = "sorter: initial constants")
         
        for s in self.states:
            codeSorter.addSymbol(s.name)
                
        for segment in self.segments:
            segment.sort(codeSorter)
            
            
    @Lister.withContextError
    def _writeTemplate(self):
        
        def common():
            variables = self.segments[SegmentLabel.INITIAL].getAssignments()
            s = "global %s" % ", ".join(variables) if variables else "# (nothing to do)" 
            return ast.parse(s)

        builder = TemplateBuilder(SimulationModelTemplate)
        builder.replace(":commonBlock:", common())

        builder.replace(":parameters:",     [w.statement for w in self.params], False)
        builder.replace(":constants:",      [w.statement for w in self.consts], False)
        builder.replace(":incons:",         [w.statement for w in self.incons])
        builder.replace(":systemParams:",   [w.statement for w in self.init])
        
        builder.replace(":initStates:",     [w.getDeclaration(i)     for i, w in enumerate(self.states)])
        builder.replace(":restoreValues:",  [w.getStateValue(i)      for i, w in enumerate(self.states)])
        builder.replace(":update:",         [w.getUpdateStatement(i) for i, w in enumerate(self.states)])

        builder.replace(":initial:",  self.segments[SegmentLabel.INITIAL].statements())
        builder.replace(":dynamic:",  self.segments[SegmentLabel.DYNAMIC].statements())
        builder.replace(":terminal:", self.segments[SegmentLabel.TERMINAL].statements(), False)
        
        builder.write()

        
    def saveListFile(self, toFile = True):
        self.loader.saveList(None if toFile else sys.stdout)
        
        
    def printSummary(self, file = sys.stdout):
        completed = "succesfully completed" if self.succes else "failed"
        print(f"Parsing of {self.loader.file} {completed} with {self.results[0]} errors and {self.results[1]} warnings.\n", file = file)
        items = ", ".join([v.name for v in sorted(self.states, key = lambda n: n.name)])
        print(f"state variables: {items}\n", file = file)
        format = lambda coll: ([" %-8s = %-12s " % (k.name, k.value) for k in sorted(coll, key = lambda n: n.name)])
        items  = (format(self.consts), format(self.params), format(self.incons))
        import itertools
        print("   %-22s "*3 % ("CONST", "PARAM", "INCON"))
        for values in itertools.zip_longest(*items, fillvalue = " "*25):
            print(*values, file = file)
            
            
    def debugSegmentation(self):
        try:
            self.segments.debug()
        except:
            print("*** segmentation incomplete")
            
if __name__ == '__main__':
            
    mdl = Model("./test.csm.py")
    print("\n", '-'*80, '\n')
    mdl.saveListFile(False)
    print("\n", '-'*80, '\n')
    mdl.debugSegmentation()
    mdl.printSummary()