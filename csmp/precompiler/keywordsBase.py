import copy
from collections import defaultdict
from enum import Enum
from warnings import warn
import lib.ast_comments as ast

from csmp import errors
from csmp.precompiler.nodeWraps import NodeWrap


class KeywordStatus(Enum):
    OK                  = 0
    toINIT              = 1
    ignored             =-2
    obsolete            =-3
    not_supported       =-4
    not_yet_supported   =-5
    undecided           =-6
    
    def humanReadable(self):
        return self.name.replace("_", " ")


class KeywordLabels(Enum):    
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
    
    
    

class KeywordWrap(NodeWrap): # TODO doubtfully distinct from Keyword
    instances = defaultdict(list)
    declaration = "createXXXXXXXX"
    
    
    def __init__(self, node: ast.AST, name: str = None, **moreArgs):
        super().__init__(node, **moreArgs)
        self.name    = name
        instanceList = KeywordWrap.instances[self._instanceLabel()]
        instanceList.append(self)
        self.index   = instanceList.index(self)
        if isinstance(self.node, ast.Assign):
            self._base_ = self.node.value
        elif isinstance(self.node, ast.Expr):
            self._base_ = self.node.value
        else:
            raise Exception(type(self.node))
        
        
    @classmethod
    def _instanceLabel(cls):
        return cls.__name__

    
    @classmethod
    def _clear(cls):
        cls.instances[cls._instanceLabel()].clear()
        
        
    @classmethod
    def clearAll(cls):
        cls.instances.clear()
        
    
    def _copyNode(self):
        newNode = copy.deepcopy(self.node)
        self.sync(newNode)
        return newNode


    def _nodeFromString(self, source):
        mod    = ast.parse(source)
        result = mod.body[0]
        self.sync(result)
        return result

    
    def _getArgs(self):
        return ",".join([ast.unparse(arg) for arg in self._base_.args])

    
    def _getKwds(self):
        return ",".join([ast.unparse(arg) for arg in self._base_.keywords])

    
    def _allArguments(self):
        return ",".join([ast.unparse(arg) for arg in self._base_.args + self._base_.keywords])

    def _varlist(self):
        return ",".join([f"'{arg.id}'" for arg in self._base_.args])
    
    

class Keyword(KeywordWrap):                   
    status      = KeywordStatus.OK
    categories  = set()
    extract     = True
    classes     = {}

    @classmethod
    def className(cls):
        if type(cls) != type:
            cls = cls.__class__
        return cls.__name__    

    @classmethod    
    def __class_getitem__(cls, name):
        return cls.classes.get(name)

    @classmethod
    def initialize(cls):
        # register class:
        Keyword.classes[cls.__name__] = cls
        
        # initialize categories:
        cls.categories = set()
        for cat in KeywordLabels:
            if hasattr(cls, f"transform{cat.capitalize()}"):
                cls.categories.add(cat)
        
    
    def inplace(self):
        if self.status == KeywordStatus.not_supported:
            raise errors.PrecompilerError(f"{self.className()} is not supported in CSMPy")
        
        if self.status == KeywordStatus.ignored:
            warn(f"{self.className()} is ignored", category=SyntaxWarning)
            return None
        
        if self.status.value <= KeywordStatus.not_yet_supported.value:
            warn(f"{self.className()} has status '{self.status.humanReadable()}' in CSMPy and will not be proceessed now", category=SyntaxWarning)
            return None

        return self.transformInplace()
    
    
    def transformInplace(self):
        return None if self.extract else self.node


    def transform(self, category: KeywordLabels):
        if not category in self.categories:
            return self._errorWrap("EROR:", f"cannot transform {self.keyword.name} to {category.name}")
            # raise errors.ProgramError(f"cannot transform {self.keyword.name} to {category.name}")
        
        methodName  = f"transform{category.capitalize()}"
        method      = getattr(self, methodName, None)
        if method is None:
            raise errors.NotYetImplementedError(f"{self.className()}.{methodName}()")
        
        return method()



    