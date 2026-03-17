import lib.ast_comments as ast

from csmp import errors
from csmp.precompiler.keywords import ConstantDeclaration, Keyword
from csmp.precompiler.nodeWraps import NodeWrap





class KeywordCollector(ast.NodeTransformer):
    
    def __init__(self):
        super().__init__()
        self.keywords = []
    
    def run(self, tree):
        self.visit(tree)
        return self.keywords
        
            
    def addKeyword(self, keyword: Keyword):
        self.keywords.append(keyword)
        return keyword
    
    
    def getTargetName(self, node):
        if not ("targets" in node._fields):
            raise errors.PrecompilerError("syntax not understood")
        if not isinstance(node.targets[0], ast.Name):
            raise errors.PrecompilerError("cannot unpack CSMP-statement")
        return node.targets[0].id
    

    def match(self, node):    
        if ("value" in node._fields) and isinstance(node.value, ast.Call):
            keywordClass = Keyword[node.value.func.id]
            return keywordClass

    
    def compoundKeyword(self, keyword, node):
        # compound constants cannot be sorted.
        # best to split them right away:
        for kwd in node.value.keywords:
            name    = kwd.arg
            value   = ast.unparse(kwd.value) 
            subnode = keyword._nodeFromString(f"{name} = {keyword.className()}({value})")
            self.addKeyword(type(keyword)(subnode, name))
            
            
    def visit_Expr(self, node):
        keywordClass = self.match(node)
        if keywordClass is not None:
            keyword = keywordClass(node)
            if isinstance(keyword, ConstantDeclaration):
                self.compoundKeyword(keyword, node)
            else:
                self.addKeyword(keyword)
            return keyword.inplace()
        return node
        

    def visit_Assign(self, node):
        keywordClass = self.match(node)
        if keywordClass is not None:
            name = self.getTargetName(node)
            keyword = self.addKeyword(keywordClass(node, name))
            return keyword.inplace()
        return node


class ImportCollector(ast.NodeTransformer):

    def __init__(self):
        self.nodes   = []
        self.extract = True

    
    def run(self, tree):
        self.visit_Import       = self._processNode_
        self.visit_ImportFrom   = self._processNode_
        self.visit(tree)
        return self.nodes


    def accept(self, node, *args, **kwargs):
        self.nodes.append(NodeWrap(node, *args, **kwargs))
        return None if self.extract else node
    
    
    def _processNode_(self, node):
        return self.accept(node)
