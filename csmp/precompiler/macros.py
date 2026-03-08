import ast
import copy

try:
    from .nodeWraps import NodeWrap
    from ..errors import MacroError, PrecompilerError
    from .nodeCollector import NodeCollector
    from .lister import Lister
except:
    from csmp.precompiler.nodeWraps import NodeWrap
    from csmp.errors import MacroError, PrecompilerError
    from csmp.precompiler.nodeCollector import NodeCollector
    from csmp.precompiler.lister import Lister

"""
usage:
    macros = MacroDeclarationCollector().run(tree)
    macros = dict([(m.name, m) for m in macros])
    MacroExpansionCollector().run(tree, macros)
"""        


class MacroWrap(NodeWrap):
    '''
    common code for both macr wraps
    '''

    def __init__(self, node):
        super().__init__(node)
        self.inputs     = []
        self.outputs    = []
        self.name       = self._extractFunctionName(node)


    def list(self):
        return "%04d:%04d %s (%s)" % (self.getStart(), self.getEnd(), self.name, type(self).__name__)


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
        return self.__extractArgumentNames(node, node.targets[0].elts) 
    
     
    def _extractInputNames(self, node):
        # use with care and only in declarations! 
        # Inputs can be any kind of expression in calls.
        return self.__extractArgumentNames(node, node.value.args)

    
    def __extractArgumentNames(self, node, collectibles):
        assert isinstance(node.value, ast.Call)
        result = [n.id for n in collectibles if isinstance(n, ast.Name)]
        if (len(result) > len(set(result))):
            raise Exception("duplicate arguments")
        return result
    
        
        
        

# =====================================================================================================
#        DECLARATION
# =====================================================================================================

class MacroDeclarationWrap(MacroWrap):
    ''' MacroDeclarationWrap
    
    Generated from a MACRO("...")-call where the macro itself is in the 
    multiline string argument. This string is parsed as a new ast-tree.
    The in and out going macro arguments are extracted from the declaration:
    
    out1, out2, ..., outn = MACRO(in1, in2, ..., inn)
    
    Before injection, these placeholder names are replaced with the 
    invoking arguments.
    '''

    def __init__(self, node):
        super().__init__(node)
        self.name       = "<macro>"
        self.code       = ast.parse("#")
        try:
            if len(node.value.args) != 1:
                raise MacroError("MACRO should have exactly one (string-type) argument")
            self.source     = self.unIndent(node.value.args[0].value)
            self.code       = ast.parse(self.source)
            declaration     = self.code.body.pop(0) # i.e. the first line
            self.name       = self._extractFunctionName(declaration)
            self.inputs     = self._extractInputNames(declaration)
            self.outputs    = self._extractOutputNames(declaration)
        except SyntaxError as e:
            self.addRemark(PrecompilerError.rewriteSyntaxError(e, "error in MACRO:"))


    def unIndent(self, codeBlock):
        lines = [line.replace("\t", "    ") for line in codeBlock.split("\n")]
        ldsp  = 0xff                # number of leading spaces
        for line in lines:
            if not line.strip():    
                continue            # skip no-code lines
            ldsp = min(ldsp, len(line) - len(line.lstrip(" ")))
            if ldsp == 0:           
                return codeBlock    # code block not indented
        
        return "\n".join([line[ldsp:] for line in lines])
        
    
class MacroDeclarationCollector(NodeCollector):
    '''
    collect all MACRO-declarations from an ast tree
    '''
    wrapperClass = MacroDeclarationWrap
    
    def run(self, tree):
        self.visit_Expr     = self._processNode_
        items = super().run(tree)
        # self.checkMultipleDefinitions(items)
        return items 

    
    def _processNode_(self, node):
        if isinstance(node.value, ast.Call) and (node.value.func.id == "MACRO"):
            return self.accept(node)
        return node
        

# =====================================================================================================
#        EXPANSION
# =====================================================================================================


class MacroInjectorWrap(MacroWrap):
    '''
    create sequence of nodes with renamed variables
    taking the structure from the MACRO declaration
    and names from the insertion request
    '''
    


    def __init__(self, node):
        super().__init__(node)
        self.inputs     = self._extractArguments(node)
        self.outputs    = self._extractOutputNames(node)
        
        
    def injection(self, macro):
        
        class transformer(ast.NodeTransformer):
            # replace placeholder names with actual names 
            def visit_Name(self, node):
                subst = names.get(node.id, node)
                if isinstance(subst, ast.AST):
                    return subst
                else: 
                    node.id = subst
                    return node
        
        # make name-dictionary with inputs and outpus:
        names  = dict(zip(macro.inputs,  self.inputs))
        names.update(dict(zip(macro.outputs, self.outputs)))
        # replace applicable names:
        node = transformer().visit( copy.deepcopy(macro.code) )
        # pin inserted nodes to the location of the insertion request:
        for n in node.body:
            ast.copy_location(n, self.node)
        # ast allows to insert a list of nodes at once:
        return node.body



class MacroExpansionCollector(NodeCollector):
    '''
    create an injector node for each function call
    whose name is in the codebook (s. __init__)
    '''
    wrapperClass = MacroInjectorWrap
    
    def run(self, tree, codeBook = {}):
        '''
        args:
            tree: ast parsed tree
            codeBook: dict (name: Macrodeclaration)
        '''
        self.codeBook       = codeBook
        self.extract        = False
        self.visit_Assign   = self._processNode_
        items = super().run(tree)
        return items 

    
    def _processNode_(self, node):
        if isinstance(node.value, ast.Call):
            # if this function bears the name of a known MACRO:
            macro = self.codeBook.get(node.value.func.id, False)
            if macro:
                self.accept(node)
                # we're allowed to replace our extracted node 
                # with a list of nodes that have been translated
                # fom the expanded macro:
                return self.nodes[-1].injection(macro)
        return node
        




if __name__ == '__main__':
    source = '''
MACRO(
        """
        TWT, LAI = GROWTH(TWTI,MC,CVF, LAR, ALU)
        TWT      = INTGRL(TWTI,GTW)
        GTW      = (GPHOT - MC*TWT)*CVF
        GPHOT    = ALU*AVIS
        AVIS     = IVIS*(1.- EXP(- 0.7*LAIT))*0.9*LAI/LAIT
        LAI      = TWT*LAR
        """)
        
TWT1, LAI1 = GROWTH(TWTI1,MC,CVF, LAR, ALU)        
TWT2, LAI2 = GROWTH(TWTI2,MC,CVF, LAR, ALU)        
    '''

    Lister().start()
    Lister().addInfo("final message", Lister.FINAL, "me")
    tree = ast.parse(source)
    r = MacroDeclarationCollector().run(tree)
    print(r)
    if not True:
        growth = r[0]
        print(growth.name, growth.outputs, growth.inputs)
        Lister().report(growth.source, reportAll=True)
        
        source = "out1, out2 = GROWTH(p1, 2*p2, int(p3), 4, 5+6)"
        
        tree = ast.parse(source)
        
        i = MacroInjectorWrap(tree.body[0])
        print(i, i.outputs, i.inputs, "\n\n\n")
        i.injection(r[0])
        
    else:
        d = dict([(m.name, m) for m in r])
        print(d)
        s = MacroExpansionCollector().run(tree, d)
        print(s)

        print(ast.unparse(tree))
        
        
    for o in sorted(NodeWrap.objects, key=lambda o: str(o)):
        print(o)    