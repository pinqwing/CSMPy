import ast
import inspect
import itertools
import sys
import importlib.util
from pathlib import Path

from csmp.customTypes import VarType
from csmp.errors import PrecompilerError, SegmentationError
from csmp.keywords import CSMP_Function
from csmp.precompiler.lister import Lister
from csmp.precompiler.loader import ModelLoader
from csmp.precompiler.nodeCollector import ImportCollector, ConstantCollector, \
    VarlistCollector, IntegralCollector, FundefCollector
from csmp.precompiler.nodeWraps import CSMPKeywordWrap, NodeWrap, FunctionGeneratorWrap
from csmp.precompiler.segment import ModelSegments, SegmentLabel
from csmp.precompiler.sorter import Sorter
from csmp.precompiler.template import TemplateBuilder
from templates.simulationModelTemplate import SimulationModelTemplate
from csmp.precompiler.macros import MacroDeclarationCollector,\
    MacroExpansionCollector



class Precompiler:

    def __init__(self):
        self.reset()
        
        
    def compile(self, sourceFile):
        self.reset()
        self.loader     = ModelLoader(sourceFile)
        self.processCode()
        self.results    = Lister().count()
        self.succes     = (self.results[0] == 0)
        
        
    def reset(self):
        Lister().start()
        self.ast        = ast.parse("")
        self.succes     = False
        self.results    = 99999, 99999
        self.consts     = []
        self.imports    = []
        self.incons     = []
        self.init       = []
        self.macros     = []
        self.params     = []
        self.segments   = []
        self.states     = []
        self.fundefs    = []
        

    def processCode(self):
        try:
            self.ast = self.loader.getSyntaxTree()
        except SyntaxError as e:
            Lister().addSyntaxErrorError(e, "the model contains syntax errors and could not be parsed", Lister.FINAL, "processCode")
            return
        
        try:
            self._macroExpansion()
            self._collectDeclarations()
            self._modelSegmentation()
            self._assignStatements()
            self.writeCurrentSource(extension=".unstd")
            self._sortCodeBlocks()
            self.writeCurrentSource(extension=".sort")
        except PrecompilerError:
            Lister().addError("parsing of the source code failed", Lister.FINAL, "processCode")
    
    
    @Lister.withContextError
    def _macroExpansion(self):
        self.macros = MacroDeclarationCollector().run(self.ast)
        macros = dict([(m.name, m) for m in self.macros])
        MacroExpansionCollector().run(self.ast, macros)
        
        
    @Lister.withContextError
    def _modelSegmentation(self):
        self.segments = ModelSegments(self.ast)
    
            
    @Lister.withContextError
    def _collectDeclarations(self):
        names = {}
        
        def addDeclarations(source, destination):
            for decl in source:
                name = decl.name
                vTyp = decl.varType
                peer = names.get(name, False)
                if peer:
                    tail = "not allowed" if (vTyp == peer) else "conflicts with %s '%s'" % (peer.name, name)
                    decl.addRemark("redefinition of %s '%s' %s" % (vTyp.name, name, tail))
                else:
                    names[name] = vTyp
                    destination.append(decl)
                     
        self.imports = ImportCollector().run(self.ast)
        
        # order matters below
        addDeclarations(IntegralCollector().run(self.ast), self.states)
        addDeclarations(FundefCollector().run(self.ast), self.fundefs)
        addDeclarations(ConstantCollector().run(self.ast, VarType.CONSTANT), self.consts)
        addDeclarations(VarlistCollector().run(self.ast, VarType.CONSTANT), self.consts)
        addDeclarations(ConstantCollector().run(self.ast, VarType.PARAM), self.params)
        addDeclarations(VarlistCollector().run(self.ast, VarType.PARAM), self.params)
        addDeclarations(ConstantCollector().run(self.ast, VarType.INCON), self.incons)
        addDeclarations(VarlistCollector().run(self.ast, VarType.INCON), self.incons)
        
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
            wrap = CSMPKeywordWrap(node, **info) 
            return wrap if wrap.status >= 0 else None
            # return CSMPKeywordWrap(node, **info) if info.get('status', -999) >= 0 else None
        elif (isinstance(node, ast.Assign) and 
              isinstance(node.value, ast.Call) and 
              node.value.func.id in ("AFGEN", "NLFGEN")):
            return FunctionGeneratorWrap(node, self.fundefs)
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
                
        for s in self.fundefs:
            codeSorter.addSymbol(s.name)
                
        for segment in self.segments:
            segment.sort(codeSorter)
            
            
    @Lister.withContextError
    def writeTemplate(self, file = sys.stdout, template = SimulationModelTemplate, builder = None):
        
        def common():
            variables = self.segments[SegmentLabel.INITIAL].getAssignments()
            s = "global %s" % ", ".join(variables) if variables else "# (nothing to do)" 
            node = ast.parse(s)
            return [NodeWrap(node.body[0])] if node.body else []

        generators  = itertools.chain.from_iterable([f.clients for f in self.fundefs])
        builder     = TemplateBuilder(template) if builder is None else builder
        builder.replace(":commonBlock:", common())

        builder.replace(":parameters:",     self.params, False)
        builder.replace(":constants:",      self.consts, False)
        builder.replace(":incons:",         self.incons)
        builder.replace(":systemParams:",   self.init)
        
        builder.replace(":functions:",      [NodeWrap(w.getDeclaration())     for w in self.fundefs])
        builder.replace(":generators:",     [NodeWrap(w.getDeclaration())     for w in generators])
        builder.replace(":initStates:",     [NodeWrap(w.getDeclaration())     for w in self.states])
        builder.replace(":restoreValues:",  [NodeWrap(w.getStateValue())      for w in self.states])
        builder.replace(":update:",         [NodeWrap(w.getUpdateStatement()) for w in self.states])
        
        builder.replace(":initial:",  self.segments.initial.getItems())
        builder.replace(":dynamic:",  self.segments.dynamic.getItems())
        builder.replace(":terminal:", self.segments.terminal.getItems())
        
        builder.write(file)

        
    def writeListFile(self, file = None, summary = False):
        def write(f):
            Lister().report(self.loader.getSource(), file = f, onlyMarkedLines = summary)
            print("%8d error(s)\n%8d warning(s)" % Lister().count(), file = f)
            
        if file is None:
            path = self.loader.getFilepath(".lst")
            with path.open("w") as f:
                write(f)
        else:
            write(file)
        
        
    def writeCurrentSource(self, extension = None):
        if extension is None:
            file = sys.stdout
        else:
            file = self.loader.getFilepath(extension).open("w")
            
        def output(label, items):
            print("\n"+'-'*10, label, '-'*20, file=file)
            for item in items:
                print(item, file=file)
                
        generators  = itertools.chain.from_iterable([f.clients for f in self.fundefs])
        output("functions",      [NodeWrap(w.getDeclaration())     for w in self.fundefs])
        output("generators",     [NodeWrap(w.getDeclaration())     for w in generators])
        output("initStates",     [NodeWrap(w.getDeclaration())     for w in self.states])
        output("constants",      self.consts)
        output("parameters",     self.params)
        output("systemParams",   self.init)

        output("initial",  self.segments.initial.getItems())
        output("incons",         self.incons)
        
        output("restoreValues",  [NodeWrap(w.getStateValue())      for w in self.states])
        output("dynamic",  self.segments.dynamic.getItems())
        output("update",         [NodeWrap(w.getUpdateStatement()) for w in self.states])
        
        output("terminal", self.segments.terminal.getItems())

        
        
    def _getConstantValues(self):
        '''
        Evaluate the hard-defined values of constants, parameters and incons.
        :return: dict
        '''
        constants = {
                     ":constants:":      [w for w in self.consts],
                     ":parameters:":     self.params,
                     ":incons:":         [w for w in self.incons],
                     }
        template = "def dummy(): ...\n" + "\n".join(["'%s'" % c for c in constants])
        builder  = TemplateBuilder(template)
        for label, nodes in constants.items():
            builder.replace(label, nodes)
        
        result  = {}
        exec(builder.toString(), locals = result)
        return result
        
        
    def printSummary(self, file = sys.stdout):
        modelFileName       = self.loader.file
        errors, warnings    = self.results
        completed           = "succesfully completed" if self.succes else "failed"
        stateVars           = ", ".join([v.name for v in sorted(self.states, key = lambda n: n.name)])
        
        print(f"Parsing of {modelFileName} {completed} with {errors} error(s) and {warnings} warning(s).\n", file = file)
        print(f"state variables: {stateVars}\n", file = file)
        
        consts = self._getConstantValues()
        format = lambda coll: ([" %-8s = %-12s " % (k.name, consts.get(k.name, -99999)) for k in sorted(coll, key = lambda n: n.name)])
        items  = (format(self.consts), format(self.params), format(self.incons))
        
        print("   %-22s "*3 % ("CONST", "PARAM", "INCON"))
        for values in itertools.zip_longest(*items, fillvalue = " "*25):
            print(*values, file = file)
            
        self.writeListFile(file, summary = True)
        
            
    def debugSegmentation(self):
        try:
            self.segments.debug()
        except:
            print("*** segmentation incomplete")
            
if __name__ == '__main__':
    

        
    
    
    mdl = Precompiler()
    mdl.compile("../../models/test.csm.py")
    mdl.printSummary()
    # print("\n", '-'*80, '\n')
    # mdl.saveListFile(True)
    print("\n", '-'*80, '\n')
    # mdl.writeTemplate()
    # mdl.debugSegmentation()
    # for o in sorted(NodeWrap.objects, key=lambda o: str(o)):
    #     print(o)    