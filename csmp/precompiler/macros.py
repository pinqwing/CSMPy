import lib.ast_comments as ast
import copy

from csmp.errors import MacroError
from lib.smallUtilities import unindent




class Macro:

    def __init__(self, node):
        self.baseLine = node.lineno
        if len(node.value.args) != 1:
            raise MacroError(f"MACRO should have exactly one (string-type) argument (line {self.baseLine})")
        self.source     = unindent(node.value.args[0].value)
        try:
            self.code       = ast.parse(self.source)
        except SyntaxError as e:
            text = e.text.replace("\n", "")
            line = self.__offsetLineno(e)
            raise MacroError(f"syntax error in macro-declaration (line {line}): {text}")
        
        declaration     = self.code.body.pop(0) # i.e. the first line
        self.name       = self._extractFunctionName(declaration)
        self.inputs     = self._extractInputNames(declaration)
        self.outputs    = self._extractOutputNames(declaration)


    def invoke(self, node):

        class transformer(ast.NodeTransformer):
            # replace placeholder names with actual names 
            def visit_Name(self, node):
                subst = names.get(node.id, node)
                if isinstance(subst, ast.AST):
                    return subst
                else: 
                    node.id = subst
                    return node
        
        inputs     = self._extractArguments(node)
        outputs    = self._extractOutputNames(node)
        
        # make name-dictionary with inputs and outpus:
        names      = dict(zip(self.inputs,  inputs))
        names.update(dict(zip(self.outputs, outputs)))
        # replace applicable names:
        result     = transformer().visit( copy.deepcopy(self.code) )
        for n in result.body:
            ast.copy_location(n, node)
        # ast allows to insert a list of nodes at once.
        return result.body


    def _extractFunctionName(self, node: ast.Call):
        assert isinstance(node.value, ast.Call)
        return node.value.func.id


    def _extractArguments(self, node: ast.Call): 
        '''
        Extract actual parameter used in a function call.
        See also _extractOutputNames and _extractOutputNames.
        :param node: call-node 
        '''
        assert isinstance(node.value, ast.Call)
        return [n for n in node.value.args]
    
        
    def _extractOutputNames(self, node):
        # Prabably safe in any case 
        if not "targets" in node._fields:
            line = self.__offsetLineno(node) 
            raise  MacroError(f"macro {self.name} doesn't have an output list (line {line})")
        return self.__extractArgumentNames(node, node.targets[0].elts) 
    
     
    def _extractInputNames(self, node):
        # use with care and only in declarations! 
        # Inputs can be any kind of expression in calls.
        return self.__extractArgumentNames(node, node.value.args)

    
    def __extractArgumentNames(self, node, collectibles):
        assert isinstance(node.value, ast.Call)
        result = [n.id for n in collectibles if isinstance(n, ast.Name)]
        if (len(result) > len(set(result))):
            line = self.__offsetLineno(node) 
            raise MacroError(f"duplicate arguments in macro {self.name} (line {line})")
        return result
    
    def __offsetLineno(self, node):
        return self.baseLine + node.lineno -1 
        
    
class MacroSubstituter(ast.NodeTransformer):
    '''
    Collect all MACRO-declarations from an ast tree
    and replace their invocations.
    '''
    def __init__(self):
        super().__init__()
        self.codebook = {}
        
    def run(self, tree):
        # since macros must be defined before the model,
        # both processing staps can be performed in on go:
        self.visit_Expr     = self._processDeclaration_
        self.visit_Assign   = self._processInvocation_

        self.codebook.clear()
        self.visit(tree)

    
    def _processDeclaration_(self, node):
        if isinstance(node.value, ast.Call) and (node.value.func.id == "MACRO"):
            declaration = Macro(node)
            self.codebook[declaration.name] = declaration
            return None
        return node


    def _processInvocation_(self, node):
        if isinstance(node.value, ast.Call):
            # if this function bears the name of a known MACRO:
            macro = self.codebook.get(node.value.func.id, False)
            if macro:
                # we're allowed to replace our extracted node 
                # with a list of nodes that have been translated
                # fom the expanded macro:
                return macro.invoke(node)
        return node
        





if __name__ == '__main__':
    source = '''
MACRO("""
    X, DXDT = EXPONENTIAL(X0, A, B)
    X        = INTGRL(X0, DXDT)
    RATE     = A * (X - B)
    DXDT     = RATE
    """)

EX1, R1 = EXPONENTIAL(10., 0.1, 5) 
    '''

    tree = ast.parse(source)
    macros = MacroSubstituter()
    macros.run(tree)
    
    print("macro definition:\n-----------------")
    print(ast.unparse(macros.codebook["EXPONENTIAL"].code), "\n\n")
    print("resulting code:\n---------------")
    print(ast.unparse(tree))
