"""
This modue defines the CSMP statements, i.e. statements, that require some action to be taken that
includes more than only returning a function result.

The Statement's class structure takes a leaf from the book of ast: The methods they define determine
to which categories (StatementCategory) they pertain. Such methods conform the naming format

def transformLabelname(self): ...

"""

# from csmp.customTypes import IntegrationMethod
import lib.ast_comments as ast
from lib.smallUtilities import dump, walkSmarter

from csmp.precompiler.statementBase import Statement, StatementStatus, StatementCategory, ConstantDeclaration,\
    AssigningStatement, Varlist, BasicStatement, ExecutionControl
from csmp.precompiler.lister import Lister
from csmp import errors
from unicodedata import category
from pathlib import pwd

def symbols():
    return [n for n in globals() if n == n.upper() and not n.startswith("_") ]


class CONSTANT(ConstantDeclaration):
    # syntax: <name> = CONSTANT(<value>)
    cat = StatementCategory.constants



class PARAM(ConstantDeclaration):
    # syntax: <name> = CONSTANT(<value>)
    cat = StatementCategory.parameters



class INCON(ConstantDeclaration):
    # syntax: <name> = CONSTANT(<value>)
    cat = StatementCategory.incons



class INTGRL(AssigningStatement):
    # syntax: <name> = INTGRL(<initial>, <rate>)

    def __init__(self, node):
        super().__init__(node)
        init, rate = self.args[:2]
        self.transformations = {
            StatementCategory.initStates:
                self._nodeFromString(f"self.createStateVariable({self.index}, '{self.name}', {init})"),

            StatementCategory.restoreValues:
                self._nodeFromString(f"{self.name} = self.getState({self.index})"),
        
            StatementCategory.update:
                self._nodeFromString(f"self.setCurrentRate({self.index}, {rate})")
                }



class FUNCTION(AssigningStatement):
    # syntax: <name> = FUNCTION(<data>)

    def __init__(self, node):
        super().__init__(node)
        self.transformations = {
            StatementCategory.functions:
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
        self.transformations = {StatementCategory.generators: None}


    def link(self, functions):
        functionName = self.args[0]
        self.linkedFunction = functions.get(functionName, -99999)
        
    
    def transform(self, category: StatementCategory):
        # transformation not valid before link is set
        if category == StatementCategory.generators:
            args = self._kwdList() 
            return self._nodeFromString(f"self.create{self.className(1)}({self.index}, function = {self.linkedFunction}, {args})")

        
    def transformInplace(self):
        arg = self.args[1] 
        return self._nodeFromString(f"self.funcGenerators[{self.index}].getValue({arg})").value


class AFGEN(FunctionGenerator):        
    # syntax: ... = AFGEN(<function>, <value>, **kwargs)
    pass



class NLFGEN(AFGEN):        
    # syntax: ... = NLFGEN(<function>, <value>, **kwargs)
    # formally this is not a statement but a function. But it behaves like a statement
    # in that it has to be predefined. Also it's got to be linked to its FUNCTION
    # object before writing the runnable model.
    pass



class TABLE(Statement):
    # syntax: TABLE()
    ...



class OVERLAY(Statement):
    # syntax: OVERLAY()
    status  = StatementStatus.not_supported



class RENAME(Statement):
    # syntax: RENAME(TIME = 'TIME', DELT = 'DELT', DELMIN = 'DELMIN', FINTIM = 'FINTIM', PRDEL = 'PRDEL', OUTDEL = 'OUTDEL')
    ...



class FIXED(Statement):
    # syntax: N/S
    status  = StatementStatus.obsolete



class MEMORY(AssigningStatement):
    # syntax: <names> = MEMORY(<function>, <initial>)
    '''
    CSMPy syntax:
    
    MEMORY(<function call>, <initial values>)
    '''
    
    def __init__(self, node, *args, **kwargs):
        super().__init__(node)
        declaration = self._createObject() 
        self.transformations = {
            StatementCategory.memoryObjects:
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
    # syntax: <names> = HISTORY(<function>, <initial>)
    pass



class STORAGE(Statement):
    # syntax: (obsolete)
    status  = StatementStatus.obsolete



class DECK(Statement):
    # syntax: DECK()
    status  = StatementStatus.not_supported



class __OtherStatement__(Statement):
    status  = StatementStatus.other
class MACRO(__OtherStatement__): pass 
class INITIAL(__OtherStatement__): pass 
class DYNAMIC(__OtherStatement__): pass 
class TERMINAL(__OtherStatement__): pass 
class SORT(__OtherStatement__): pass 
class NOSORT(__OtherStatement__): pass 


class END(Statement):
    # syntax: END()
    status  = StatementStatus.ignored



class CONTINUE(Statement):
    # syntax: CONTINUE()
    status  = StatementStatus.not_supported



class PROCEDURE(Statement):
    # syntax: N/S
    status  = StatementStatus.obsolete



class STOP(Statement):
    # syntax: STOP()
    status  = StatementStatus.ignored



class ENDJOB(Statement):
    # syntax: ENDJOB()
    status  = StatementStatus.ignored



class COMMON(Statement):
    # syntax: N/S
    status  = StatementStatus.obsolete



class DATA(Statement):
    # syntax: DATA()
    status  = StatementStatus.obsolete



class TIMER(ExecutionControl):
    # syntax: TIMER(FINTIM, DELT=-1, DELMIN=-1, PRDEL=-1, OUTDEL=-1)
    pass



class FINISH(ExecutionControl):
    # syntax: FINISH(<conditions>)
    pass



class RELERR(Statement):
    # syntax: RELERR()
    ...



class ABSERR(Statement):
    # syntax: ABSERR()
    ...



class METHOD(ExecutionControl):
    # syntax: METHOD(<mehod>)
    pass



class TITLE(ExecutionControl):
    # syntax: TITLE(<string>)
    pass



class PRINT(Varlist):
    # syntax: PRINT(<varlist>)
    pass



class OUTPUT(Statement):
    # syntax: OUTPUT(<varlist>)
    pass



class PREPARE(Statement):
    # syntax: PREPARE(<varlist>)
    ...



class PRTPLOT(Statement):
    # syntax: PRTPLOT(<varlist>)
    ...



class LABEL(Statement):
    # syntax: LABEL(<string>)
    ...



class RANGE(Statement):
    # syntax: RANGE(<varlist>)
    ...



class RESET(Statement):
    # syntax: RESET()
    status  = StatementStatus.not_supported



# ----------------------------------------------------------------------------------------------

def registerAndInitializeStatements(): 
    for n, c in globals().items(): 
        if n == n.upper() and not n.startswith("_") and issubclass(c, Statement):
            c.initialize()

registerAndInitializeStatements()

# ----------------------------------------------------------------------------------------------


if __name__ == '__main__':
    
    for c in Statement.classes.values():
        print("%-10s" % c.className(1), "-->", c.status.name)
    