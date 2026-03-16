import sys
import itertools
import importlib.util
from collections import defaultdict
from pathlib import Path

import lib.ast_comments as ast
from lib.smallUtilities import flatten, dump

from csmp.customTypes import VarType
from csmp.errors import PrecompilerError, SegmentationError
from csmp.keywords import CSMP_Function
from csmp.precompiler.lister import Lister, WARNING
from csmp.precompiler.loader import ModelLoader
from csmp.precompiler.nodeCollector import ImportCollector, KeywordCollector
from csmp.precompiler.nodeWraps import CSMPKeywordWrap, NodeWrap, FunctionGeneratorWrap
from csmp.precompiler.segment import ModelSegments, SegmentLabel
from csmp.precompiler.sorter import Sorter
from csmp.precompiler.template import TemplateBuilder
from csmp.precompiler.keywordsBase import KeywordLabels
from csmp.precompiler.macros import MacroSubstituter
from templates.simulationModelTemplate import SimulationModelTemplate



class Precompiler:

    def __init__(self, options):
        self.options  = options
        self.template = SimulationModelTemplate
        self.reset()

    
    consts  = property(lambda p: p.keywordNodes[KeywordLabels.constants])
    params  = property(lambda p: p.keywordNodes[KeywordLabels.parameters])
    incons  = property(lambda p: p.keywordNodes[KeywordLabels.incons])
    states  = property(lambda p: p.keywordNodes[KeywordLabels.initStates])
    fundefs = property(lambda p: p.keywordNodes[KeywordLabels.functions])
        
        
    def compile(self, sourceFile):
        self.reset()
        self.loader     = ModelLoader(sourceFile)
        self.processCode()
        self.results    = Lister().count()
        self.succes     = (self.results[0] == 0)
        
        
    def reset(self):
        Lister().start()
        self.ast            = ast.parse("")
        self.succes         = False
        self.results        = 99999, 99999
        self.readOnly       = {}
        self.imports        = []
        self.init           = []
        self.segments       = ModelSegments(ast.parse("#"))
        self.keywordNodes   = defaultdict(list)
        

    def processCode(self):
        try:
            self.ast = self.loader.getSyntaxTree()
        except SyntaxError as e:
            Lister().addSyntaxErrorError(e, "the model contains syntax errors and could not be parsed", Lister.FINAL, "processCode")
            return
        
        try:
            self.macroExpansion()
            self.collectDeclarations()
            self.modelSegmentation()
            self.assignStatements()
            self.writeCurrentSource(sorted = False)
            self.sort()
            self.writeCurrentSource(sorted = True)
            return True
        except PrecompilerError:
            Lister().addError("parsing of the source code failed", Lister.FINAL, "processCode")
            return False

    
    @Lister.withContextError
    def macroExpansion(self):
        MacroSubstituter().run(self.ast)
        
        
    @Lister.withContextError
    def modelSegmentation(self):
        self.segments = ModelSegments(self.ast)
    
            
    @Lister.withContextError
    def collectDeclarations(self):
        
        def addReadOnly(source):
            for decl in source:
                name = decl.name
                peer = self.readOnly.get(name, False)
                if peer:
                    tail = f"conflicts with {peer.className()} '{peer.name}'"
                    decl.addRemark(f"redefinition of {decl.className()} '{name}' {tail}" )
                else:
                    self.readOnly[name] = decl
                     
        self.imports = ImportCollector().run(self.ast)
        allKwdNodes  = KeywordCollector().run(self.ast)
            
        for node in allKwdNodes:
            for cat in node.categories:
                self.keywordNodes[cat].append(node)
                
        addReadOnly(self.keywordNodes[KeywordLabels.initStates])
        addReadOnly(self.keywordNodes[KeywordLabels.constants])
        addReadOnly(self.keywordNodes[KeywordLabels.parameters])
        addReadOnly(self.keywordNodes[KeywordLabels.incons])
        addReadOnly(self.keywordNodes[KeywordLabels.functions])

        functions = dict([(f.name, f.index) for f in self.keywordNodes[KeywordLabels.functions]])
        for gen in self.keywordNodes[KeywordLabels.generators]:
            gen.link(functions)
        
    
    def _validateStatement(self, statement):
        node = statement.node
        if isinstance(node, ast.Assign):
            for n in ast.walk(node.targets[0]):
                if isinstance(n, ast.Name): 
                    keyword = self.readOnly.get(n.id, False)
                    if keyword:
                        statement.addRemark(f"'{n.id}' is immutable while it has been declared {keyword.className()}", 
                                            originator = "validate")
                 
                    
    @Lister.withContextError
    def assignStatements(self):
        for node in self.ast.body:
            statement = NodeWrap(node)
            line      = statement.getLineNumber()
            for segment in self.segments:
                if segment.contains(line):
                    if isinstance(node, ast.Comment):
                        dump(node)
                    segment.appendStatement(statement)
                    self._validateStatement(statement)
                    break
            else: # if not assigned ...
                if line < self.segments.initial.start:
                    self.init.append(statement)
                else:
                    statement.addRemark("spurious line", WARNING)
                    raise SegmentationError("line %d could not be assigend to a model segment" % line)


    @Lister.withContextError
    def sort(self):
        consts, params, incons, states, fundefs = [self.keywordNodes[l]for l in (
                                                    KeywordLabels.constants, KeywordLabels.parameters,
                                                    KeywordLabels.incons,    KeywordLabels.initStates,
                                                    KeywordLabels.functions)] 
        
        codeSorter  = Sorter()
        codeSorter.useImports(self.imports)
        codeSorter.sort(consts, blockID = "sorter: constant section")
        codeSorter.sort(params, blockID = "sorter: parameter section")
        codeSorter.sort(incons, blockID = "sorter: initial constants")
         
        for s in states:    codeSorter.addSymbol(s.name)                
        for s in fundefs:   codeSorter.addSymbol(s.name)
        
        for segment in self.segments:
            segment.sort(codeSorter)
            
            
    def _writeFile(self, writerProc, toScreen, toFile, fileExtension):
        if toScreen:
            writerProc(sys.stdout)
        if toFile:
            fileName = self.loader.getFilepath(fileExtension)
            with fileName.open("w") as f:
                writerProc(f)
            print(f"created file {fileName}")
            
            
    def _writeOutput(self):
        self._writeFile(self.writeSummary,  self.options.summary["scrn"],  self.options.summary["file"], ".summary")    
        self._writeFile(self.writeListFile, self.options.listFile["scrn"], self.options.listFile["file"], ".list")    
        self._writeFile(self.writeTemplate, False, True, ".py")    
            
            
    @Lister.withContextError
    def writeTemplate(self, file = sys.stdout, template = SimulationModelTemplate, builder = None):
        
        def common():
            variables = self.segments[SegmentLabel.INITIAL].getAssignments()
            s = "global %s" % ", ".join(variables) if variables else "# (nothing to do)" 
            node = ast.parse(s)
            return [node.body[0]] if node.body else []

        builder     = TemplateBuilder(template) if builder is None else builder
        builder.replace2(KeywordLabels.common, common())

        builder.replace2(KeywordLabels.initial,    [w.node for w in self.segments.initial.getItems()],  False)
        builder.replace2(KeywordLabels.dynamic,    [w.node for w in self.segments.dynamic.getItems()],  False)
        builder.replace2(KeywordLabels.terminal,   [w.node for w in self.segments.terminal.getItems()], False)

        for cat in KeywordLabels: # this loops through _all_ cats and destroys any remaining placeholders
            items       = self.keywordNodes[cat]
            transformed = flatten([item.transform(cat) for item in items])
            builder.replace2(cat, transformed, True)

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
        
        
    def writeCurrentSource(self, sorted: bool):

        def writeSource(file):                
            def output(label, items):
                print("\n"+'-'*10, label, '-'*20, file=file)
                for item in items:
                    print(item, file=file)
                
            for lbl in [KeywordLabels.functions,
                        KeywordLabels.generators,
                        KeywordLabels.initStates,
                        KeywordLabels.constants,
                        KeywordLabels.parameters,
                        KeywordLabels.systemParams,
                        KeywordLabels.incons, 
                        KeywordLabels.initial, 
                        KeywordLabels.restoreValues,
                        KeywordLabels.dynamic,
                        KeywordLabels.update,
                        KeywordLabels.terminal]:
                if   lbl == KeywordLabels.initial:
                    items = self.segments.initial.getItems()
                elif lbl == KeywordLabels.dynamic:
                    items = self.segments.dynamic.getItems()
                elif lbl == KeywordLabels.terminal:
                    items = self.segments.terminal.getItems()
                else:
                    items = [NodeWrap(w.transform(lbl)) for w in self.keywordNodes[lbl]]  
                output(lbl.value, items)        
        
        if sorted:
            self._writeFile(writeSource,  self.options.sorted["scrn"],  self.options.sorted["file"], ".sorted")
        else:    
            self._writeFile(writeSource,  self.options.unsorted["scrn"],  self.options.unsorted["file"], ".unsorted")    
        
        
    def _getConstantValues(self):
        '''
        Evaluate the hard-defined values of constants, parameters and incons.
        :return: dict
        '''
        constants = self.consts + self.params + self.incons
        tmpSource = "def dummy(): ...\n" + "\n".join([s.toString() for s in constants])
        result    = {}
        exec(tmpSource, locals = result)
        return result 
            
        
    def writeSummary(self, file = sys.stdout):
        modelFileName       = self.loader.file
        errors, warnings    = self.results
        completed           = "succesfully completed" if self.succes else "failed"
        stateVars           = ", ".join([v.name for v in sorted(self.states, key = lambda n: n.name)])
        
        print("\n\n", file = file)
        print(f"Parsing of {modelFileName} {completed} with {errors} error(s) and {warnings} warning(s).\n", file = file)
        print(f"state variables: {stateVars}\n", file = file)
        
        consts = self._getConstantValues()
        format = lambda coll: ([" %-8s = %-12s " % (k.name, consts.get(k.name, -99999)) for k in sorted(coll, key = lambda n: n.name)])
        items  = (format(self.consts), format(self.params), format(self.incons))
        
        print("   %-22s "*3 % ("CONST", "PARAM", "INCON"), file = file)
        for values in itertools.zip_longest(*items, fillvalue = " "*25):
            print(*values, file = file)
            
        self.writeListFile(file, summary = True)
        print("\n\n", file = file)
        
            
    def debugSegmentation(self):
        try:
            self.segments.debug()
        except:
            print("*** segmentation incomplete")
            
if __name__ == '__main__':
    

        
    
    
    mdl = Precompiler()
    mdl.compile("../../models/test.csm.py")
    mdl.writeSummary()
    # print("\n", '-'*80, '\n')
    # mdl.saveListFile(True)
    print("\n", '-'*80, '\n')
    # mdl.writeTemplate()
    # mdl.debugSegmentation()
    # for o in sorted(NodeWrap.objects, key=lambda o: str(o)):
    #     print(o)    