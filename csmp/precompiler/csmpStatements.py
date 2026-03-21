"""
This modue defines the CSMP statements, i.e. statements, that require some action to be taken that
includes more than only returning a function result.

The Statement's class structure takes a leaf from the book of ast: The methods they define determine
to which categories (StatementLabels) they pertain. Such methods conform the naming format

def transformLabelname(self): ...

"""

# from csmp.customTypes import IntegrationMethod
import lib.ast_comments as ast
from lib.smallUtilities import dump, walkSmarter

from csmp.precompiler.statementBase import Statement, StatementStatus, StatementLabels, ConstantDeclaration,\
    AssigningStatement, Varlist, BasicStatement, ExecutionControl
from csmp.precompiler.lister import Lister
from csmp import errors
from unicodedata import category

def symbols():
    return [n for n in globals() if n == n.upper() and not n.startswith("_") ]


class CONSTANT(ConstantDeclaration):
    cat = StatementLabels.constants

class PARAM(ConstantDeclaration):
    cat = StatementLabels.parameters

class INCON(ConstantDeclaration):
    cat = StatementLabels.incons



class INTGRL(AssigningStatement):

    def __init__(self, node):
        super().__init__(node)
        init, rate = self.args[:2]
        self.transformations = {
            StatementLabels.initStates:
                self._nodeFromString(f"self.createStateVariable({self.index}, '{self.name}', {init}, {rate})"),

            StatementLabels.restoreValues:
                self._nodeFromString(f"{self.name} = self.getState({self.index})"),
        
            StatementLabels.update:
                self._nodeFromString(f"self.setCurrentRate({self.index}, {rate})")
                }
        
        
class FUNCTION(AssigningStatement):

    def __init__(self, node):
        super().__init__(node)
        self.transformations = {
            StatementLabels.functions:
                self._nodeFromString(f"self.createCsmpFunction({self.index}, '{self.name}', {self._allArgs()})")}



        
class FunctionGenerator(AssigningStatement):        
    # syntax: ... = AFGEN(<function>, <value>, **kwargs)
    # formally these are not statements but functions. But they behave like statements
    # in that they have to be predefined. Also they got to be linked to their FUNCTION
    # objects before writing the runnable model.
    astClasses  = [ast.Call] # supported classes to create from

    def __init__(self, node: ast.AST):
        super().__init__(node, -1)
        self.linkedFunction = -1
        self.transformations = {StatementLabels.generators: None}


    def link(self, functions):
        functionName = self.args[0]
        self.linkedFunction = functions.get(functionName, -99999)
        
    
    def transform(self, category: StatementLabels):
        # transformation not valid before link is set
        if category == StatementLabels.generators:
            args = self._kwdList() 
            return self._nodeFromString(f"self.create{self.className(1)}({self.index}, function = {self.linkedFunction}, {args})")

        
    def transformInplace(self):
        arg = self.args[1] 
        return self._nodeFromString(f"self.funcGenerators[{self.index}].getValue({arg})").value


class AFGEN(FunctionGenerator):        
    pass
        
class NLFGEN(AFGEN):        
    # formally this is not a statement but a function. But it behaves like a statement
    # in that it has to be predefined. Also it's got to be linked to its FUNCTION
    # object before writing the runnable model.
    pass
    
    
    

class TABLE(Statement):
    ...


class OVERLAY(Statement):
    status  = StatementStatus.not_supported



# CONTROL statements:
class RENAME(Statement):
    ...
    

class FIXED(Statement):
    status  = StatementStatus.obsolete



class MEMORY(AssigningStatement):
    '''
    CSMPy syntax:
    
    MEMORY(<function call>, <initial values>)
    '''
    
    def __init__(self, node, *args, **kwargs):
        super().__init__(node)
        declaration = self._createObject() 
        self.transformations = {
            StatementLabels.memoryObjects:
                self._nodeFromString(declaration)
                }
        
        
    def _createObject(self):
        if len(self.args) == 2:
            initVal = self.args[1]
            initSize = len(initVal.split(","))
            if initSize != len(self.targets):
                self.addRemark(f"{self.className()}: invalid number of initial values ({initSize})")
        else:
            self.addRemark(f"{self.className()}: invalid number of arguments")
            return "#"
        
        call    = f"self.create{self.className(1)}Function"
        return f"{call}({self.index}, call = {self.args[0]}, initial = {self.args[1]})"

        
    def transformInplace(self):
        call = f"self.{self.className(2)}Function"
        return self._nodeFromString(f"{call}[{self.index}]({self._argList()})").value



class HISTORY(MEMORY):
    pass



class STORAGE(Statement):
    status  = StatementStatus.obsolete



class DECK(Statement):
    status  = StatementStatus.not_supported


class __OherStatement__(Statement):
    status  = StatementStatus.other
class MACRO(__OherStatement__): pass 
class INITIAL(__OherStatement__): pass 
class DYNAMIC(__OherStatement__): pass 
class TERMINAL(__OherStatement__): pass 
class SORT(__OherStatement__): pass 
class NOSORT(__OherStatement__): pass 


class END(Statement):
    status  = StatementStatus.ignored


class CONTINUE(Statement):
    status  = StatementStatus.not_supported


class PROCEDURE(Statement):
    status  = StatementStatus.obsolete


class STOP(Statement):
    status  = StatementStatus.ignored


class ENDJOB(Statement):
    status  = StatementStatus.ignored


# ENDJOB STACK
class COMMON(Statement):
    status  = StatementStatus.undecided


# COMMON MEM  
class DATA(Statement):
    status  = StatementStatus.obsolete


class TIMER(ExecutionControl):
    pass

class FINISH(ExecutionControl):
    pass

class RELERR(Statement):
    ...

class ABSERR(Statement):
    ...


class METHOD(ExecutionControl):
    pass


class TITLE(ExecutionControl):
    pass

# Output control statements:
class PRINT(Varlist):
    pass

class OUTPUT(Statement):
    pass

class PREPARE(Statement):
    ...

class PRTPLOT(Statement):
    ...

class LABEL(Statement):
    ...

class RANGE(Statement):
    ...

class RESET(Statement):
    status  = StatementStatus.not_supported


# ----------------------------------------------------------------------------------------------

def registerAndInitializeStatements(): 
    for n, c in globals().items(): 
        if n == n.upper() and not n.startswith("_") and issubclass(c, Statement):
            c.initialize()

registerAndInitializeStatements()

# ----------------------------------------------------------------------------------------------


if __name__ == '__main__':
    import re, inspect
    
    for c in Statement.classes.values():
        print("%-10s" % c.className(1), "-->", c.status.name)
        
    