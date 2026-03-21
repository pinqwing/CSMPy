import lib.ast_comments as ast

from csmp import errors
from csmp.precompiler.nodeWraps import NodeWrap
from csmp.precompiler.statementBase import Statement, ConstantDeclaration




class StatementCollector(ast.NodeTransformer):
    
    def __init__(self):
        super().__init__()
        self.statements = []
        # marker node:
        self.delendus   = ast.parse("0").body[0]

    
    def run(self, tree):
        self.visit(tree)
        
        # it is hard to remove parent nodes while in vistit, so instead
        # the lines have been marked for later removal:
        linesToRemove = [b for b in tree.body if any([node is self.delendus for node in ast.walk(b)])]
        for line in linesToRemove:
            tree.body.remove(line)
            
        return self.statements
        
            
    def addStatement(self, statement: Statement):
        self.statements.append(statement)
        return statement
    
    
    def getTargetName(self, node):
        if not ("targets" in node._fields):
            raise errors.PrecompilerError("syntax not understood")
        if not isinstance(node.targets[0], ast.Name):
            raise errors.PrecompilerError("cannot unpack CSMP-statement")
        return node.targets[0].id
    
    
    def match(self, node):    
        if ("value" in node._fields) and isinstance(node.value, ast.Call):
            statementClass = Statement[node.value.func.id]
            return statementClass


    
    def breakUpCompoundStatement(self, node):
        # compound constants cannot be sorted.
        # best to split them right away:
        result    = []
        statement = Statement(node)
        stmtClass = Statement[statement.fName]
        for name, value in statement.kwargs:
            newNode = statement._nodeFromString(f"{name} = {statement.fName}({value})")
            self.addStatement(stmtClass(newNode.value))
            result.append(newNode)
        return None
            
            
    def visit_Expr(self, node):
        statementClass = self.match(node)
        if statementClass is not None:
            if  issubclass(statementClass, ConstantDeclaration):
                return self.breakUpCompoundStatement(node.value)
            else:
                statement = statementClass(node.value)
                self.addStatement(statement)
                return statement.transformInplace()
        return node
        

    def visit_Call(self, node):
        self.generic_visit(node)
        statement = Statement.get(node)
        if statement is not None:
            self.addStatement(statement)
            subst = statement.inplace()
            if subst is None:
                # mark parent for removal:
                return self.delendus
            else:
                return subst
        return node


    def removeDeleted(self, node):
        if hasattr(node, "deleted") and node.deleted == True:
            return None
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
