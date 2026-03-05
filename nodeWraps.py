import ast
import copy
from keywords import CSMP_Function
import lister
from customTypes import VarType


class NodeWrap:
    
    remarkCallback = lambda *args, **kwargs: None # one assignment to rule all
    
    def __init__(self, node: ast.AST, **kwargs):
        self.node    = node
        self.lines   = [node.lineno] 
        if node.end_lineno > node.lineno:
            self.lines.append(node.end_lineno)
            
        for n, v in kwargs.items():
            setattr(self, n, v) 
         

    
    def getStatement(self):
        return self.node
    
    statement = property(lambda w: w.getStatement())    
    
    
    def getSource(self): # DONE: renamed from source()
        return ast.unparse(self.node)
    
    
    def list(self):
        return "%04d:%04d %s (%s)" % (self.getStart(), self.getEnd(), self.getSource(), type(self).__name__)
    
    
    def getLineNumber(self):
        return self.getStart()
    
    def getStart(self):
        return self.lines[0]
    
    def getEnd(self):
        return self.lines[-1]
    
    
    def addRemark(self, msg: str, errorLvl = lister.ERROR, originator = None):
        if originator is None:
            originator = type(self).__name__
        lister.Lister().addMessage(errorLvl, msg, self.node.end_lineno, originator)
    
    
    def __repr__(self):
        return self.list()
    
    




class ConstantDecl(NodeWrap): 
    
    name    = property(lambda s: s.node.targets[0].id)
    value   = property(lambda s: ast.unparse(s.node.value)) 

    


class IntegralDecl(NodeWrap): 
    
    def __init__(self, node: ast.AST):
        super().__init__(node, varType = VarType.INTGRL)
        self.index = -1
        
    name = property(lambda s: s.node.targets[0].id)
    
    def getDeclaration(self, index):
        x0   = ast.unparse(self.node.value.args[0])
        mod  = ast.parse(f"self.createStateVariable({index}, '{self.name}', {x0})")
        self.index = index
        return mod.body[0]
    
    def getStateValue(self, index):
        assert index == self.index
        mod  = ast.parse(f"{self.name} = self.getState({index})")
        return mod.body[0]
    
    def getUpdateStatement(self, index):
        assert index == self.index
        rate = ast.unparse(self.node.value.args[1])
        mod  = ast.parse(f"self.setCurrentRate({index}, {rate})")
        return mod.body[0]
    
    
    
    
class LabelDecl(NodeWrap): 
        
    def __init__(self, node: ast.AST):
        from segment import SegmentLabel
        super().__init__(node)
        text        = node.value.value
        self.label  = SegmentLabel[text]
        
        
        
        
class CSMPWrap(NodeWrap):
    def __init__(self, node: ast.AST, status = 0, varlist = False):
        super().__init__(node)
        self.status     = status
        self.toVarList  = varlist
        
        if status == CSMP_Function.IGNORED:
            self.addRemark("CSMP statement ignored", lister.INFO)
        elif status == CSMP_Function.NOT_SUPPORTED:
            self.addRemark("CSMP statement no longer supported")
        elif status == CSMP_Function.NOT_YET:
            self.addRemark("CSMP statement not yet implemented")
        elif status == CSMP_Function.OBSOLETE:
            self.addRemark("CSMP statement obsolete")
        elif status == CSMP_Function.UNDECIDED:
            self.addRemark("CSMP statement may be implementd in the future")
            
        
    def getLineNumber(self):
        return -1 if self.status == CSMP_Function.toINIT else super().getLineNumber()  
        
    
    def getStatement(self):
        node = copy.deepcopy(self.node)
        if self.toVarList:
            s = "self.set%s(%s)" % (node.value.func.id.capitalize(),
                                    ",".join(['"%s"' % arg.id for arg in node.value.args]))
            return ast.parse(s)
        else:
            node.value.func.id = "self.set" + node.value.func.id.capitalize()
            return node
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
