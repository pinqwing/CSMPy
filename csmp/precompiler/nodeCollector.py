import ast
from collections import defaultdict
from enum import Enum

from ..customTypes import VarType
from .nodeWraps import NodeWrap, IntegralDecl, ConstantDecl, LabelDecl
from .segment import SegmentLabel
from csmp.precompiler.nodeWraps import FunctionDecl


class NodeCollector(ast.NodeTransformer):

    wrapperClass = NodeWrap
     
    def __init__(self):
        self.nodes   = []
        self.extract = True

    
    def run(self, tree):
        self.visit(tree)
        return self.nodes


    def accept(self, node, *args, **kwargs):
        self.nodes.append(self.wrapperClass(node, *args, **kwargs))
        return None if self.extract else node
    
    
    def _processNode_(self, node):
        return None 
        

    
class ImportCollector(NodeCollector):
    # wrapperClass = ImportDecl
    
    def run(self, tree):
        self.visit_Import       = self._processNode_
        self.visit_ImportFrom   = self._processNode_
        return super().run(tree)
    
    
    def _processNode_(self, node):
        return self.accept(node)


class DeclarationCollector(NodeCollector):

    def __init__(self):
        super().__init__()
        self.originator = type(self).__name__
        
        
    def checkMultipleDefinitions(self, items):
        itemDict = defaultdict(list)
        for item in items: 
            itemDict[item.name].append(item)
        if len(itemDict) < len(items):
            for name, wraps in itemDict.items():
                if len(wraps) > 1:
                    for item in wraps[1:]:
                        item.addRemark("redefinition of immutable variable '%s'" % name, originator = self.originator)

                        
    def run(self, tree):
        self.visit_Assign = self._processNode_
        items = super().run(tree)
        self.checkMultipleDefinitions(items)
        return items 
    
    
class FundefCollector(DeclarationCollector):        
    ''' function declaration collector
    
    Collects FUNCTION-statements.
    
    note:
        AFGEN & NLFGEN are not pre-collected by any Collector.
        Instead, they are dealt with like with any csmp-statement,
        only the FunctionGeneratorWraps make themselves known
        to their FunctionDecl-s so they can hitch hike along
        to get their declaration lines inserted.
    '''
    wrapperClass = FunctionDecl
    
    def run(self, tree):
        self.originator = "functionDeclarationCheck"
        return super().run(tree)
    
    @staticmethod
    def matches(node):    
        return isinstance(node.value, ast.Call) and node.value.func.id == "FUNCTION"
    
    
    def _processNode_(self, node):
        if self.matches(node):
            return self.accept(node)
        return node


        
class IntegralCollector(DeclarationCollector):        
    wrapperClass = IntegralDecl
    
    def run(self, tree):
        self.originator = "stateVarCheck"
        return super().run(tree)
    
    @staticmethod
    def matches(node):    
        return isinstance(node.value, ast.Call) and node.value.func.id == "INTGRL"
    
    
    def _processNode_(self, node):
        if self.matches(node):
            return self.accept(node)
        return node


        
class SectionCollector(NodeCollector):        
    wrapperClass = LabelDecl
    
    def run(self, tree):
        self.visit_Expr = self._processNode_
        return super().run(tree)
    
    
    def _processNode_(self, node):
        if isinstance(node.value, ast.Constant) and node.value.value in dir(SegmentLabel):
            return self.accept(node)
        return node


        
class ConstantCollector(DeclarationCollector):        
    '''
    collects constant declarations in the format NAME = VVVVV(<value>)
    where VVVVV is one of CONSTANT, PARAM or INCON.
    '''
    wrapperClass = ConstantDecl
    
    def run(self, tree, varType: VarType):
        self.varType    = varType
        self.originator = "%sCheck" % varType.name.capitalize()
        return super().run(tree)
    
    
    def _processNode_(self, node):
        if isinstance(node.value, ast.Call) and node.value.func.id == self.varType.name:
            # cut the middle man (func):
            node.value = node.value.args[0] # for now, only 1-element constants allowed
            return self.accept(node, varType = self.varType)
        return node


        
class VarlistCollector(NodeCollector):
    '''
    collects constant declarations in the format VVVVV(NAME = <value>, ...)
    where VVVVV is one of CONSTANT, PARAM or INCON.
    '''
    wrapperClass = ConstantDecl
    
    def run(self, tree, varType: VarType):
        self.varType        = varType
        self.visit_Expr     = self._processNode_
        items = super().run(tree)
        return items 
    
    def _processNode_(self, node):
        if isinstance(node.value, ast.Call) and node.value.func.id == self.varType.name:
            s = "\n".join([ast.unparse(k) for k in node.value.keywords])
            for n in ast.parse(s).body:
                self.accept(n, varType = self.varType, lines = (node.lineno, node.end_lineno))
            return None
        return node
    