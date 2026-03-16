# from csmp.customTypes import IntegrationMethod
import lib.ast_comments as ast
from lib.smallUtilities import dump


from csmp.precompiler.keywordsBase import Keyword, KeywordStatus, KeywordLabels
from csmp.precompiler.lister import Lister

def symbols():
    return [n for n in globals() if n == n.upper() and not n.startswith("_") ]



# class KeywordAction(Enum):
#     keep    = 0
#     extract = 1
#     modify  = 2




# class MetaFunction(type):
#     @classmethod
#     def __call__(cls, *args, **kwargs):
#         return cls.__execute__(*args, **kwargs)
#
#     name = property(lambda c: c.__name__)

class ConstantDeclaration(Keyword):
    @staticmethod
    def __execute__(**assigments): return

    def _keywordArgsToAssignments(self):
        # # compund syntax: CONSTANT(a = 1, b = 2...)
        # condition_a = ("args"     in self._base_._fields) and bool(self._base_.args)
        # condition_k = ("keywords" in self._base_._fields) and bool(self._base_.keywords)
        #
        # if condition_k and not condition_a: # deprecated
        #     src = [ast.unparse(kw) for kw in self._base_.keywords]
        #     return [ast.parse(s).body[0] for s in src]
        #
        
        # atomic sonstant: syntax: c = CONSTANT(123)
        # if condition_a and not condition_k:
        if (len(self._base_.args) == 1) and self.name:
            value = ast.unparse(self._base_.args[0])
            return self._nodeFromString(f"{self.name} = {value}")
            
        # status = confused ...
        if Lister.exists():  # @UndefinedVariable
            self.addRemark(f"invalid {self.className()}-declaration")
        return self.node
        
        
    def toString(self): # NOT __str__ !!
        return self.list()

    def getValue(self):
        return ast.unparse(self._base_.args[0])
    
    
    def getName(self):
        return ast.unparse(self._base_.targets[0].id)
    
    
    def list(self):
        return ast.unparse(self._keywordArgsToAssignments())
        return f"{self.name} = {self.toString()})"


                        
    
class CONSTANT(ConstantDeclaration):
    def transformConstants(self):
        return self._keywordArgsToAssignments()


class PARAM(ConstantDeclaration):
    def transformParameters(self):
        return self._keywordArgsToAssignments()


class INCON(ConstantDeclaration):
    def transformIncons(self):
        return self._keywordArgsToAssignments()



class INTGRL(Keyword):
    declaration = "createStateVariable"

    def transformInitStates(self):
        args = self._getArgs() 
        return self._nodeFromString(f"self.{self.declaration}({self.index}, '{self.name}', {args})")

        
    def transformRestoreValues(self):
        return self._nodeFromString(f"{self.name} = self.getState({self.index})")
        
        
    def transformUpdate(self):
        rate = ast.unparse(self._base_.args[1])
        return self._nodeFromString(f"self.setCurrentRate({self.index}, {rate})")
        
        

class FUNCTION(Keyword):
    declaration = "createCsmpFunction"

    @staticmethod
    def __execute__(*xyPairs): return

    def transformFunctions(self):
        args = self._getArgs() 
        return self._nodeFromString(f"self.{self.declaration}({self.index}, '{self.name}', {args})")

        
class AFGEN(Keyword):        
    # formally this is not a keyword but a function. But it behaves like a keyword
    # in that it has to be predefined. Also it's got to be linked to its FUNCTION
    # object before writing the runnable model.
    declaration = "createCsmpAFGEN"
    
    def __init__(self, node: ast.AST, name: str, **kwargs):
        super().__init__(node, name, **kwargs)
        self.linkedFunction = -1

    def link(self, functions):
        functionName = self._base_.args[0].id
        self.linkedFunction = functions.get(functionName, -99999)
        
    
    def transformGenerators(self):
        args = self._getKwds() 
        return self._nodeFromString(f"self.{self.declaration}({self.index}, function = {self.linkedFunction}, {args})")

        
    def transformInplace(self):
        # e.g.: REDF = self.funcGenerators[0].getValue(LAI * 4 - R1)
        arg = ast.unparse(self._base_.args[1]) 
        return self._nodeFromString(f"{self.name} = self.funcGenerators[{self.index}].getValue({arg})")

        
    

class TABLE(Keyword):
    status  = KeywordStatus.toINIT
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(**data):
        return 


class OVERLAY(Keyword):
    status  = KeywordStatus.not_supported
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return




# CONTROL statements:
class RENAME(Keyword):
    status  = KeywordStatus.toINIT
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(**synonyms):
        return


class FIXED(Keyword):
    status  = KeywordStatus.obsolete
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return


class MEMORY(Keyword):
    status  = KeywordStatus.undecided
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return


class HISTORY(Keyword):
    status  = KeywordStatus.undecided
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return


class STORAGE(Keyword):
    status  = KeywordStatus.obsolete
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return


class DECK(Keyword):
    status  = KeywordStatus.not_supported
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return


class MACRO(Keyword):
    status  = KeywordStatus.OK
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return



# INITIAL
# DYNAMIC
# TERMINAL
# SORT
# NOSORT

class END(Keyword):
    status  = KeywordStatus.ignored
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return


class CONTINUE(Keyword):
    status  = KeywordStatus.not_supported
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return


class PROCEDURE(Keyword):
    status  = KeywordStatus.obsolete
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return


class STOP(Keyword):
    status  = KeywordStatus.ignored
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return


class ENDJOB(Keyword):
    status  = KeywordStatus.ignored
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return


# ENDJOB STACK
class COMMON(Keyword):
    status  = KeywordStatus.undecided
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return


# COMMON MEM  
class DATA(Keyword):
    status  = KeywordStatus.obsolete
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return




# Execution control statements:
class ExecutionControl(Keyword):

    def transformSystemParams(self):
        args = self._allArguments() 
        return self._nodeFromString(f"self.set{self.className().capitalize()}({args})")


class TIMER(ExecutionControl):
    @staticmethod
    def __execute__(PRDEL = None, OUTDEL = None, FINTIM = None, DELT = None, DELMIN = None): return


class FINISH(ExecutionControl):
    @staticmethod
    def __execute__(**conditions): return


class RELERR(Keyword):
    status  = KeywordStatus.toINIT
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(**epsila):
        return


class ABSERR(Keyword):
    status  = KeywordStatus.toINIT
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(**errors):
        return


class METHOD(ExecutionControl):
    @staticmethod
    def __execute__(method: IntegrationMethod|str): return



class TITLE(ExecutionControl):
    @staticmethod
    def __execute__(simulationTitle): return


class Varlist(Keyword):
    @staticmethod
    def __execute__(*varNames): return

    def transformSystemParams(self):
        args = self._varlist() 
        return self._nodeFromString(f"self.set{self.className().capitalize()}({args})")

# Output control statements:
class PRINT(Varlist):
    pass

class OUTPUT(Keyword):
    pass

class PREPARE(Keyword):
    status  = KeywordStatus.toINIT
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*varNames):
        return


class PRTPLOT(Keyword):
    status  = KeywordStatus.undecided
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return


class LABEL(Keyword):
    status  = KeywordStatus.toINIT
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(printPlotCaption):
        return


class RANGE(Keyword):
    status  = KeywordStatus.toINIT
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*varNames):
        return


class RESET(Keyword):
    status  = KeywordStatus.not_supported
    varList = False
    transl  = ""

    @staticmethod
    def __execute__(*args, **kwargs):
        return


def registerAndInitializeKeywords(): 
    for n, c in globals().items(): 
        if n == n.upper() and not n.startswith("_") and issubclass(c, Keyword):
            c.initialize()

registerAndInitializeKeywords()


if __name__ == '__main__':
    import re
    
    s = "CONSTANT(a=1, b=2)"
    t = ast.parse(s)
    dump(t)
    c = CONSTANT(t.body[0].value)
    print(c.toString())