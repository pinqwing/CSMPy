import lib.ast_comments as ast
import inspect
from io import StringIO
from csmp.errors import ProgramError
from pathlib import Path
import itertools


class TemplateBuilder(ast.NodeTransformer):
    
    def __init__(self, template):
        ''' turn a generic model template with placeholder labels into valid source code.
        
        
        
        :param template:
        '''

        if isinstance(template, type):
            source      = inspect.getsource(template)
        elif isinstance(template, str):
            source      = template
        else:
            raise ProgramError("unsupported template of type '%s'" % (type(template).__name__))
        
        self.template           = template
        self.code               = ast.parse(source)
        # change name of class in template
        self.code.body[0].name  = self.code.body[0].name.replace("Template", "")
        
        
    
    def replace(self, label, items: list, keepLabel = True):
        # items = itertools.chain(items)
        subst = items.body if isinstance(items, ast.Module) else items             
        
        def comment(node, size = 2):
            tag = f"# --- {label.value}: ----------"
            result = [ast.Comment(value = "",  inline = False),
                      ast.Comment(value = tag, inline = False)]
            ast.copy_location(result[0], node)
            ast.copy_location(result[1], node)
            return result[:size]

            
        def replaceBranch(node):
            tag = f":{label.name}:"
            if isinstance(node.value, ast.Constant) and (node.value.value == tag):
                items = comment(node, 2 if keepLabel else 1)
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

    # extra prox to run the created program TODO: NYUsed
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
    
    
    