import copy
from collections import defaultdict
from enum import Enum
from warnings import warn
import lib.ast_comments as ast

from csmp import errors
from csmp.precompiler.nodeWraps import NodeWrap
from lib.smallUtilities import walkSmarter, dump
import inspect


class StatementStatus(Enum):
    UNDEFINED           = 0
    OK                  = 1
    ignored             =-2
    obsolete            =-3
    not_supported       =-4
    not_yet_supported   =-5
    undecided           =-6
    other               = -999
    
    
    def humanReadable(self):
        return self.name.replace("_", " ")


class StatementLabels(Enum):    
    initial         = "INITIAL segment"
    dynamic         = "DYNAMIC segment"
    terminal        = "TERMINAL segment"
    common          = "'common block'"
    constants       = "constant definitions"
    parameters      = "parameter definitions"
    incons          = "incon definitions"
    functions       = "function definitions"
    generators      = "function generator objects"
    initStates      = "state variable creation"
    memoryObjects   = "memory object creation"        
    historyObjects  = "history object creation"        
    systemParams    = "parametrize the model"
    restoreValues   = "current values of state variables"
    update          = "update rates"

    def capitalize(self):
        # capitalize first character but leave the rest as it is:
        s = self.name
        return s[0].upper() + s[1:]


    def mainSegment(self):
        cls = type(self)
        return self in (cls.initial, cls.dynamic, cls.terminal)
    
    
    

class StatementClass(NodeWrap): # TODO doubtfully distinct from Statement
    classes   = {}                  # registered classed
    instances = defaultdict(list)   # instances per class (to generate an index)
    
    
    def __init__(self, node: ast.AST):
        super().__init__(node)
        instanceList = StatementClass.instances[self._instanceLabel()]
        instanceList.append(self)
        self.index   = instanceList.index(self)

        
    @classmethod
    def get(cls, node):
        assert isinstance(node, ast.Call)
        stmClass = cls[node.func.id]
        if stmClass is None:
            return None
        else:
            return stmClass(node)
        
    
    @classmethod    
    def __class_getitem__(cls, name):
        return cls.classes.get(name)

        
    @classmethod
    def _instanceLabel(cls):
        return cls.__name__

    
    @classmethod
    def _clear(cls):
        cls.instances[cls._instanceLabel()].clear()
        
        
    @classmethod
    def clearAll(cls):
        cls.instances.clear()
        
    
    @classmethod
    def className(cls, format = 0):
        fmt = {1: str.capitalize, 2: str.lower}
        if type(cls) != type:
            cls = cls.__class__
        
        cap = fmt.get(format, str)
        return cap(cls.__name__)    

    @classmethod
    def initialize(cls):
        # register class:
        Statement.classes[cls.__name__] = cls
        
        if cls.status == StatementStatus.UNDEFINED:
            cls.status = StatementStatus.OK if not "..." in inspect.getsource(cls)else StatementStatus.not_yet_supported 


        
    
class Statement(StatementClass):                   
    status      = StatementStatus.UNDEFINED
    

    def __init__(self, node):
        super().__init__(node)
        self.fName   = node.func.id
        self.args    = [ast.unparse(n) for n in node.args]
        self.kwargs  = [(k.arg, ast.unparse(k.value)) for k in node.keywords]
        self.targets = [p.id for p in walkSmarter(node.parent.targets[0], [ast.Name])] if isinstance(node.parent, ast.Assign) else []
        self.transformations = {}
        
        
    def __str__(self):
        pre  = "%04d" % self.getLineNumber()  
        out  = (self._outList() + " = ") if self.targets else ""
        args = self._allArgs()
        return f"{pre} {out}{self.className()}({args})"

    
    @classmethod    
    def setParentage(cls, tree):       
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
    
    
    def _argList(self, asString = True):
        items = [a for a in self.args]
        return ", ".join(items) if asString else items            
                    
    def _kwdList(self, asString = True):
        items = ["%s = %s" % k for k in self.kwargs]
        return ", ".join(items) if asString else items            
                    
    def _outList(self, asString = True):
        items = [t for t in self.targets]
        return ", ".join(items) if asString else items            
                    
    def _allArgs(self, asString = True):
        items = self._argList(False) + self._kwdList(False)
        return ", ".join(items) if asString else items            
                    
                    
    def _copyNode(self):
        newNode = copy.deepcopy(self.node)
        self.sync(newNode)
        return newNode


    def _nodeFromString(self, source):
        mod    = ast.parse(source)
        result = mod.body[0]
        result.parent = self.node.parent
        self.setParentage(result)
        self.sync(result)
        return result

    
    # def _varlist(self):
    #     return ",".join([f"'{arg.id}'" for arg in self._base_.args])

    def inplace(self):
        if self.status == StatementStatus.not_supported:
            warn(f"{self.className()} is not supported in CSMPy")
            return None
        
        if self.status == StatementStatus.ignored:
            warn(f"{self.className()} is ignored", category=SyntaxWarning)
            return None
        
        if self.status.value <= StatementStatus.not_yet_supported.value:
            warn(f"{self.className()} has status '{self.status.humanReadable()}' in CSMPy and will not be proceessed now", category=SyntaxWarning)
            return None

        return self.transformInplace()
    
    
    def transformInplace(self):
        return None


    def transform(self, category: StatementLabels):
        # do not shortcut this method, for overriding allows for late transformations
        return self.transformations.get(category)

    

class BasicStatement(Statement):    
    
    def __init__(self, node):
        super().__init__(node)
        if self.targets:
            self.addRemark(f"{self.classname()} does not return a value")

           
    def transformSystemParams(self):
        args = self._argList() 
        return self._nodeFromString(f"self.set{self.className(1)}({args})")


           
class Varlist(BasicStatement):
    
    def transformSystemParams(self):
        args = self._varlist() 
        return self._nodeFromString(f"self.set{self.className(1)}({args})")



class AssigningStatement(Statement):

    def __init__(self, node, outputs = 1):
        super().__init__(node)
        t = self.targets
        if (outputs > 0) and (len(t) != outputs):
            self.addRemark(f"expected {outputs} output(s) but got {len(t)}")
        self.name = t[0] if len(t) == 1 else ""
        

    def transformInplace(self):
        return None

    def transform(self, category: StatementLabels):
        return self.transformations.get(category)
        


    
class ConstantDeclaration(AssigningStatement):
    ''' common ancestor for CONSTANT, PARAM and INCON (perhaps more in the future)
    
    This class evolved to be a bit more complex than other statements, due to the 
    facts that
    - constants can be declared in a compound syntax
    - the statements can appear as assigments or as expressions
    - the resulting code must make depencencies explicit to the sorter (and thus to Python)
    - the resulting code must make the assigned values easily accessible for evaluation
      in the precompiler phase.
    
    The compound syntax (e.g.  CONSTANT(a = 1, b = 2...)) is undesirable since it does not
    make the names and values explicit; therefore the StatementCollector immediately splits
    such statements into their atomic form (a = CONSTANT(1); b = CONSTANT(2) ...)
    '''
    cat = StatementLabels.constants
        
    def __init__(self, node):
        super().__init__(node, 1)
        # There's no in-place transformation and the call-format cannot be sorted.
        # Therefore, transform to destination right away:
        self.node = self._nodeFromString(self.toString())
        self.transformations = {self.cat: self.node}
        
        
    def toString(self): # NOT __str__ !!
        return f"{self.name} = {self.args[0]}"


    def __getValue(self):
        return self.args[0]
    
    
    def getName(self):
        return self.name
    
    

class ExecutionControl(Statement):

    def __init__(self, node):
        super().__init__(node)
        self.transformations = {
            StatementLabels.systemParams:
                self._nodeFromString(f"self.set{self.className(1)}({self._allArgs()})")
                }
            
            
            
            
            
            
            
            
            
            
            
            