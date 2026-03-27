from collections import defaultdict
from pathlib import Path

import lib.ast_comments as ast
from lib.ast_tools import setParentage
from csmp.errors import PrecompilerError, SegmentationError
from csmp.precompiler.lister import Lister, WARNING
from csmp.precompiler.loader import ModelLoader
from csmp.precompiler.macros import MacroSubstituter
from csmp.precompiler.nodeCollector import ImportCollector, StatementCollector
from csmp.precompiler.nodeWraps import NodeWrap
from csmp.precompiler.output import PrecompilerOutput
from csmp.precompiler.segment import ModelSegments
from csmp.precompiler.sorter import Sorter
from csmp.precompiler.statementBase import StatementCategory, Statement


class CSMP_Source(ModelLoader):
    
    def __init__(self, sourceFile: str | Path):
        super().__init__(sourceFile)
        self.imports        = []
        self.init           = []
        self.segments       = ModelSegments(ast.parse("#"))
        self.statements     = defaultdict(list)
        
    consts  = property(lambda p: p.statements[StatementCategory.constants])
    params  = property(lambda p: p.statements[StatementCategory.parameters])
    incons  = property(lambda p: p.statements[StatementCategory.incons])
    states  = property(lambda p: p.statements[StatementCategory.initStates])
    memobs  = property(lambda p: p.statements[StatementCategory.memoryObjects]) 
    funobs  = property(lambda p: p.statements[StatementCategory.functions]) 
    
        

class Precompiler:

    def __init__(self, options):
        self.options  = options
        self.reset()

    
    def compile(self, sourceFile):
        self.reset()
        self.model      = CSMP_Source(sourceFile)
        self.fileHelper = PrecompilerOutput(self.options, self.model)
        
        self.processCode()
        
        self.fileHelper.writeListfile("model.list")  
        self.fileHelper.writeSummary("summary.txt")
        self.results    = Lister().count()
        self.succes     = (self.results[0] == 0)
        self.fileHelper.writeSummary()
        
        
    def reset(self):
        Lister().start()
        self.ast            = ast.parse("")
        self.succes         = False
        self.results        = 99999, 99999
        self.readOnly       = {}
        

    def processCode(self):
        try:
            self.ast = self.model.getSyntaxTree()
            self.macroExpansion()
            setParentage(self.ast) # after macroSubstitution
            self.collectDeclarations()
            self.modelSegmentation()
            self.distributeRemainingStatements()
            self.fileHelper.writeCurrentSource("unsorted.lst")
            self.sort()
            self.fileHelper.writeCurrentSource("sorted.lst")
            self.fileHelper.writeRunnable(self.model.runnable.name)
            
            return True
        except PrecompilerError:
            Lister().addError("parsing of the source code failed", Lister.FINAL, "processCode")
            return False
        except SyntaxError as e:
            Lister().addSyntaxErrorError(e, "the model contains syntax errors and could not be parsed", Lister.FINAL, "processCode")
            return False

    
    @Lister.withContextError
    def macroExpansion(self):
        MacroSubstituter().run(self.ast)
        
        
    @Lister.withContextError
    def modelSegmentation(self):
        self.model.segments = ModelSegments(self.ast)
    
            
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
                     
        # imports are important to resolve external symbols:
        self.model.imports = ImportCollector().run(self.ast)
        
        # collect all statements from the model in a single list:
        allKwdNodes  = StatementCollector().run(self.ast)
            
        # redistribute all statements by SatementLabels:
        for node in allKwdNodes:
            for cat in node.transformations:
                self.model.statements[cat].append(node)
                
        # define selected assiggments as read-only after declaration:
        addReadOnly(self.model.statements[StatementCategory.initStates])
        addReadOnly(self.model.statements[StatementCategory.constants])
        addReadOnly(self.model.statements[StatementCategory.parameters])
        addReadOnly(self.model.statements[StatementCategory.incons])
        addReadOnly(self.model.statements[StatementCategory.functions])

        # link functino generators to their functions:
        functions = dict([(f.name, f.index) for f in self.model.funobs])
        for gen in self.model.statements[StatementCategory.generators]:
            gen.link(functions)
        
    
    def _validateStatement(self, statement):
        memos = dict([(f.name, f.index) for f in self.model.memobs])
        
        node = statement.node
        if isinstance(node, ast.Assign):
            for n in ast.walk(node.targets[0]):
                if isinstance(n, ast.Name): 
                    mutant = self.readOnly.get(n.id, False)
                    if mutant:
                        statement.addRemark(f"'{n.id}' is immutable while it has been declared {mutant.className()}", 
                                            originator = "validate")

    @Lister.withContextError
    def distributeRemainingStatements(self):
        for node in self.ast.body:
            statement = NodeWrap(node)
            line      = statement.getLineNumber()
            for segment in self.model.segments:
                if isinstance(node, ast.Comment):
                    break
                if segment.contains(line):
                    segment.appendStatement(statement)
                    self._validateStatement(statement)
                    break
            else: # if not assigned ...
                if line < self.model.segments.initial.start:
                    self.init.append(statement) # into the black hole ...
                else:
                    statement.addRemark("spurious line", WARNING)
                    raise SegmentationError("line %d could not be assigend to a model segment" % line)


    @Lister.withContextError
    def sort(self):
        consts, params, incons, states, fundefs, memobs = [self.model.statements[l]for l in (
                                                    StatementCategory.constants, StatementCategory.parameters,
                                                    StatementCategory.incons,    StatementCategory.initStates,
                                                    StatementCategory.functions, StatementCategory.memoryObjects)] 
        
        codeSorter  = Sorter()
        codeSorter.useImports(self.model.imports)
        codeSorter.sort(consts, blockID = "sorter: constant section")
        codeSorter.sort(params, blockID = "sorter: parameter section")
        # codeSorter.sort(incons, blockID = "sorter: initial constants")
         
        for s in states:    codeSorter.addSymbol(s.name)                
        for s in fundefs:   codeSorter.addSymbol(s.name)
        for s in memobs:   codeSorter.addSymbol(s.name)
        
        for segment in self.model.segments:
            segment.sort(codeSorter)
            
            
        
        
    def debugSegmentation(self):
        try:
            self.model.segments.debug()
        except:
            print("*** segmentation incomplete")
            
