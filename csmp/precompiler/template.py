import ast
import inspect
from io import StringIO
from csmp.errors import ProgramError


class TemplateBuilder(ast.NodeTransformer):
    
    def __init__(self, template):

        if isinstance(template, type):
            source      = inspect.getsource(template)
        elif isinstance(template, str):
            source      = template
        else:
            raise ProgramError("unsupported template of type '%s'" % (type(template).__name__))
        
        self.template   = template
        self.code       = ast.parse(source)
        self.code.body[0].name = self.code.body[0].name.replace("Template", "")
        
    
    def replace(self, tag: str, items: list, keepLabel = True):
        codeObject = [item.statement for item in items]
        subst = codeObject.body if isinstance(codeObject, ast.Module) else codeObject             
        
        def replaceBranch(node):
            if isinstance(node.value, ast.Constant) and (node.value.value == tag):
                items = [node] if keepLabel else []
                for stmt in subst:
                    items.append(ast.copy_location(stmt, node))
                return items
                
            else:
                return node
        
        self.visit_Expr = replaceBranch
        self.visit(self.code)
        ast.fix_missing_locations(self.code)
            
        
    def _replace(self, tag: str, codeObject: ast.AST, keepLabel = True):
        subst = codeObject.body if isinstance(codeObject, ast.Module) else codeObject             
        
        def replaceBranch(node):
            if isinstance(node.value, ast.Constant) and (node.value.value == tag):
                items = [node] if keepLabel else []
                for stmt in subst:
                    items.append(ast.copy_location(stmt, node))
                return items
                
            else:
                return node
        
        self.visit_Expr = replaceBranch
        self.visit(self.code)
        ast.fix_missing_locations(self.code)
            
        
    def write(self, file):
        print(ast.unparse(self.code), file = file)
        
    def toString(self):
        ss = StringIO()
        self.write(ss)
        return ss.getvalue()

    # extra prox to run the created program TOTO: NYUsed
    def getClass(self, **compilerArgs):    
        obj = compile(self.code, filename="<ast>", mode="exec", **compilerArgs)
        namespace = {}
        exec(obj, namespace)
        return namespace[self.template.__name__]
        
        
    def getObject(self, *args, **kwargs):
        c = self.getClass()
        return c(*args, **kwargs)




        
        
if __name__ == '__main__':
    
    src = "a = 1\nb = 2\nc = 'character'\n"
    subst = ast.parse(src)
    b = TemplateBuilder()
    b.replace(":parameters:", subst, keepLabel=True)
    b.write()

    C = b.getObject()
    print(C.defineConstants())
    print(C.defineParameters())
    
    
    