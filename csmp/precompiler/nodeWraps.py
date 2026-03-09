import ast
import copy
from ..customTypes import VarType
from ..keywords import CSMP_Function
from . import lister
from _collections import defaultdict



class NodeWrap:
    objects = []
    
    remarkCallback = lambda *args, **kwargs: None # one assignment to rule all
    
    def __init__(self, node: ast.AST, **kwargs):
        self.node    = node
        self.lines   = [node.lineno] 
        if node.end_lineno > node.lineno:
            self.lines.append(node.end_lineno)
            
        for n, v in kwargs.items():
            setattr(self, n, v) 
         
        self.objects.append(self)
        
    
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
        lister.Lister().addMessage(errorLvl, msg, self.getEnd(), originator)
    
    
    def __repr__(self):
        return self.list()
    
    

class Assignment(NodeWrap):
    name    = property(lambda s: s.node.targets[0].id)


class ConstantDecl(Assignment): 
    value   = property(lambda s: ast.unparse(s.node.value)) 


class ReferencedAssignment(Assignment):
    
    instances = defaultdict(list)
    declaration = "createXXXXXXXX"
    
    def __init__(self, node: ast.AST, **kwargs):
        super().__init__(node, **kwargs)
        instanceList = ReferencedAssignment.instances[self._instanceLabel()]
        instanceList.append(self)
        self.index   = instanceList.index(self)
        
    
    @classmethod
    def _instanceLabel(cls):
        return "%s::%s" % (type(cls).__name__, cls.varType.name)
    
    @classmethod
    def _clear(cls):
        cls.instances[cls._instanceLabel()].clear()
        
    @classmethod
    def clearAll(cls):
        cls.instances.clear()
        
        
    def _getArgs(self):
        return ",".join([ast.unparse(arg) for arg in self.node.value.args])

    
    def getDeclaration(self):
        args = self._getArgs() 
        mod  = ast.parse(f"self.{self.declaration}({self.index}, '{self.name}', {args})")
        ast.increment_lineno(mod, -1)
        return mod.body[0]

    
    

class FunctionDecl(ReferencedAssignment): 
    varType     = VarType.FUNCTION
    declaration = "createCsmpFunction"
    
    def __init__(self, node: ast.AST):
        super().__init__(node, varType = self.varType)
        self.clients = []
        

    
class FunctionGeneratorWrap(ReferencedAssignment):
    varType = VarType.NONE
     
    def __init__(self, node: ast.AST, functionList: list):
        super().__init__(node)
        fName = node.value.args[0].id
        for fn in functionList:
            if fn.name == fName:
                self.function = fn
                fn.clients.append(self)
                break
        else:
            self.addRemark(f"unknown FUNCTION '{fName}'")
    
            
    def getStatement(self):
        arg = ast.unparse(self.node.value.args[1])
        mod = ast.parse(f"{self.name} = self.funcGenerators[{self.index}].getValue({arg})")
        ast.increment_lineno(mod, -1)
        return mod.body[0]
    
        
    def getDeclaration(self):
        call = self.node.value.func.id
        arg  = ast.unparse(self.node.value.args[1])
        kwds = ", ".join([ast.unparse(k) for k in self.node.value.keywords])
        mod  = ast.parse(f"self.createCsmp{call}({self.index}, function = {self.function.index}, {kwds})")
        ast.increment_lineno(mod, -1)
        return mod.body[0]

        

class IntegralDecl(ReferencedAssignment): 
    varType     = VarType.INTGRL
    declaration = "createStateVariable"
    
    def _getArgs(self):
        return ast.unparse(self.node.value.args[0])

    
    def getStateValue(self):
        mod  = ast.parse(f"{self.name} = self.getState({self.index})")
        ast.increment_lineno(mod, -1)
        return mod.body[0]
    
    
    def getUpdateStatement(self):
        rate = ast.unparse(self.node.value.args[1])
        mod  = ast.parse(f"self.setCurrentRate({self.index}, {rate})")
        ast.increment_lineno(mod, -1)
        return mod.body[0]
    
    
    
    
class LabelDecl(NodeWrap): 
        
    def __init__(self, node: ast.AST):
        from csmp.precompiler.segment import SegmentLabel
        super().__init__(node)
        text        = node.value.value
        self.label  = SegmentLabel[text]
        
        
        
        
class CSMPKeywordWrap(NodeWrap):
    def __init__(self, node: ast.AST, status = 0, varlist = False, name = "keyword", translation = "", **moreArgs):
        super().__init__(node)
        self.status     = status
        self.toVarList  = varlist
        self.translation= translation
        
        if status == CSMP_Function.IGNORED:
            self.addRemark("CSMP statement %s ignored" % name, lister.INFO)
        elif status == CSMP_Function.NOT_SUPPORTED:
            self.addRemark("CSMP statement %s no longer supported" % name)
        elif status == CSMP_Function.NOT_YET:
            self.addRemark("CSMP statement %s not yet implemented" % name)
        elif status == CSMP_Function.OBSOLETE:
            self.addRemark("CSMP statement %s obsolete" % name)
        elif status == CSMP_Function.UNDECIDED:
            self.addRemark("CSMP statement %s may be implementd in the future" % name)
            
        
    def getLineNumber(self):
        return -1 if self.status == CSMP_Function.toINIT else super().getLineNumber()  
        
    
    def getStatement(self):
        node = copy.deepcopy(self.node)
        if self.toVarList:
            s = "self.set%s(%s)" % (node.value.func.id.capitalize(),
                                    ",".join(['"%s"' % arg.id for arg in node.value.args]))
            return ast.parse(s)
        elif self.translation:
            node.value.func.id = self.translation
            return node
        else:
            node.value.func.id = "self.set" + node.value.func.id.capitalize()
            return node
        
        
    # def getStatement(self):
    #     node    = copy.deepcopy(self.node)
    #     name    = node.value.func.id.capitalize()
    #     target  = node.targets[0].id if isinstance(node, ast.Assign) else ""
    #     # note: more than 1 target should not occur
    #
    #     # simple case:
    #     if not (self.toVarList or self.translation):
    #         node.value.func.id = f"self.set{name}"  
    #         return node
    #
    #     # transliterations:
    #     if self.toVarList:
    #         args = ",".join(['"%s"' % arg.id for arg in node.value.args])
    #     else:
    #         args = ",".join([ast.unparse(arg) for arg in node.value.args])
    #
    #     s = "self.set{name}({args})" if not self.translation else self.translation 
    #
    #     return ast.parse(s.format(**locals()))
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
