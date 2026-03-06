import ast
import copy

from .lister import Lister
from .nodeCollector import NodeCollector
from .nodeWraps import NodeWrap
from ..errors import MacroError
from csmp.errors import PrecompilerError


class FunCallWrap(NodeWrap):

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
    
        

class MacroInjector(FunCallWrap):


    def __init__(self, node):
        super().__init__(node)
        self.inputs     = self._extractArguments(node)
        self.outputs    = self._extractOutputNames(node)
        
        
    def injection(self, macro):
        
        class transformer(ast.NodeTransformer):
            def visit_Name(self, node):
                subst = names.get(node.id, node)
                if isinstance(subst, ast.AST):
                    return subst
                else: 
                    node.id = subst
                    return node
            
        names  = dict(zip(macro.inputs,  self.inputs))
        names.update(dict(zip(macro.outputs, self.outputs)))
        node = transformer().visit( copy.deepcopy(macro.code) )
        return node.body
        
        

class MacroDeclaration(FunCallWrap):

    def __init__(self, node):
        super().__init__(node)
        self.name       = "<macro>"
        self.code       = ast.parse("#")
        try:
            if len(node.value.args) != 1:
                raise MacroError("MACRO should have exactly one (string-type) argument")
            self.source     = self.unIndent(node.value.args[0].value)
            self.code       = ast.parse(self.source)
            declaration     = self.code.body.pop(0)
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
        
    


class MacroCollector(NodeCollector):
    wrapperClass = MacroDeclaration
    
    def run(self, tree):
        self.visit_Expr     = self._processNode_
        items = super().run(tree)
        # self.checkMultipleDefinitions(items)
        return items 
    
    def _processNode_(self, node):
        if isinstance(node.value, ast.Call) and (node.value.func.id == "MACRO"):
            return self.accept(node)
        return node
        


class MacroExpander(NodeCollector):
    wrapperClass = MacroInjector
    
    def run(self, tree, codeBook = {}):
        self.codeBook       = codeBook
        self.extract        = False
        self.visit_Assign   = self._processNode_
        items = super().run(tree)
        return items 

    
    def _processNode_(self, node):
        if isinstance(node.value, ast.Call):
            macro = self.codeBook.get(node.value.func.id, False)
            if macro:
                self.accept(node)
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
    r = MacroCollector().run(tree)
    print(r)
    if False:
        growth = r[0]
        print(growth.name, growth.outputs, growth.inputs)
        Lister().report(growth.source, reportAll=True)
        
        source = "out1, out2 = GROWTH(p1, 2*p2, int(p3), 4, 5+6)"
        
        tree = ast.parse(source)
        
        i = MacroInjector(tree.body[0])
        print(i, i.outputs, i.inputs, "\n\n\n")
        i.injection(r[0])
        
    else:
        d = dict([(m.name, m) for m in r])
        print(d)
        s = MacroExpander().run(tree, d)
        print(s)

        print(ast.unparse(tree))
        
        