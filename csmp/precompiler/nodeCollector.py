import lib.ast_comments as ast

from csmp import errors
from csmp.precompiler.nodeWraps import NodeWrap
from csmp.precompiler.statementBase import Statement, ConstantDeclaration




class StatementCollector(ast.NodeTransformer):
    
    class ConstantExpander(ast.NodeTransformer):
        
        def visit_Expr(self, node):
            if ("value" in node._fields) and isinstance(node.value, ast.Call):
                statementClass = Statement[node.value.func.id]
                if (statementClass is not None) and issubclass(statementClass, ConstantDeclaration):
                    return statementClass.breakUp(node.value)
            return node
        
            
    
    
    def __init__(self):
        super().__init__()
        self.statements = []
        # marker node:
        self.delendus   = ast.parse("None").body[0]


    def visit_Call(self, node):
        return self.convertStatements(node)
        
    
    def run(self, tree):
        # convert compount constant, param, incon to simple ones:
        xpandr = self.ConstantExpander()
        xpandr.visit(tree)

        # convert Statements:
        self.visit(tree)
        
        # it is hard to remove parent nodes while in visit, so instead
        # the lines have been marked for later removal:
        linesToRemove = [b for b in tree.body if any([node is self.delendus for node in ast.walk(b)])]
        for line in linesToRemove:
            tree.body.remove(line) # TODO: won't work fiith grouping into functions
            
        return self.statements
        
    
    def convertStatements(self, node):
        self.generic_visit(node)
        statement = Statement.get(node)
        if statement is not None:
            self.statements.append(statement)
            subst = statement.inplace()
            if subst is None:
                # mark parent for removal:
                return self.delendus
            else:
                return subst
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
