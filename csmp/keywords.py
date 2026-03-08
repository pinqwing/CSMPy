from csmp.customTypes import IntegrationMethod

def symbols():
    return [n for n in globals() if n == n.upper() and not n.startswith("_") ]


class CSMP_Function:
    OK              = 0
    toINIT          = 1
    IGNORED         =-2
    NOT_YET         =-3
    OBSOLETE        =-4
    NOT_SUPPORTED   =-5
    UNDECIDED       =-6

    @classmethod
    def keywordInfo(cls, keyword: str):
        get = getattr(cls, "get" + keyword.capitalize(), False)
        return (get() | {"name": keyword}) if get else {}
    
    @classmethod
    def getParam(cls):
        # PARAM(value)
        return dict(status = cls.OK, varlist = False)

    @classmethod
    def getConstant(cls):
        # CONSTANT(value)
        return dict(status = cls.OK, varlist = False)

    @classmethod
    def getIncon(cls):
        # INCON(value)
        return dict(status = cls.toINIT, varlist = False)

    @classmethod
    def getFunction(cls):
        # FUNCTION(*xyPairs)
        return dict(status = cls.toINIT, varlist = False)

    @classmethod
    def getTable(cls):
        # TABLE(**data)
        return dict(status = cls.toINIT, varlist = False)

    @classmethod
    def getOverlay(cls):
        # OVERLAY(*args, **kwargs)
        return dict(status = cls.NOT_SUPPORTED, varlist = False)

    @classmethod
    def getRename(cls):
        # RENAME(**synonyms)
        return dict(status = cls.toINIT, varlist = False)

    @classmethod
    def getFixed(cls):
        # FIXED(*args, **kwargs)
        return dict(status = cls.OBSOLETE, varlist = False)

    @classmethod
    def getMemory(cls):
        # MEMORY(*args, **kwargs)
        return dict(status = cls.UNDECIDED, varlist = False)

    @classmethod
    def getHistory(cls):
        # HISTORY(*args, **kwargs)
        return dict(status = cls.UNDECIDED, varlist = False)

    @classmethod
    def getStorage(cls):
        # STORAGE(*args, **kwargs)
        return dict(status = cls.OBSOLETE, varlist = False)

    @classmethod
    def getDeck(cls):
        # DECK(*args, **kwargs)
        return dict(status = cls.NOT_SUPPORTED, varlist = False)

    @classmethod
    def getMacro(cls):
        # MACRO(*args, **kwargs)
        return dict(status = cls.OK, varlist = False)

    @classmethod
    def getEnd(cls):
        # END(*args, **kwargs)
        return dict(status = cls.IGNORED, varlist = False)

    @classmethod
    def getContinue(cls):
        # CONTINUE(*args, **kwargs)
        return dict(status = cls.NOT_SUPPORTED, varlist = False)

    @classmethod
    def getProcedure(cls):
        # PROCEDURE(*args, **kwargs)
        return dict(status = cls.OBSOLETE, varlist = False)

    @classmethod
    def getStop(cls):
        # STOP(*args, **kwargs)
        return dict(status = cls.IGNORED, varlist = False)

    @classmethod
    def getEndjob(cls):
        # ENDJOB(*args, **kwargs)
        return dict(status = cls.IGNORED, varlist = False)

    @classmethod
    def getCommon(cls):
        # COMMON(*args, **kwargs)
        return dict(status = cls.UNDECIDED, varlist = False)

    @classmethod
    def getData(cls):
        # DATA(*args, **kwargs)
        return dict(status = cls.OBSOLETE, varlist = False)

    @classmethod
    def getTimer(cls):
        # TIMER(PRDEL=None, OUTDEL=None, FINTIM=None, DELT=None, DELMIN=None)
        return dict(status = cls.toINIT, varlist = False)

    @classmethod
    def getFinish(cls):
        # FINISH(**conditions)
        return dict(status = cls.toINIT, varlist = False)

    @classmethod
    def getRelerr(cls):
        # RELERR(**epsila)
        return dict(status = cls.toINIT, varlist = False)

    @classmethod
    def getAbserr(cls):
        # ABSERR(**errors)
        return dict(status = cls.toINIT, varlist = False)

    @classmethod
    def getMethod(cls):
        # METHOD(method: methods.IntegrationMethod | str)
        return dict(status = cls.toINIT, varlist = False)

    @classmethod
    def getPrint(cls):
        # PRINT(*varNames)
        return dict(status = cls.toINIT, varlist = True)

    @classmethod
    def getOutput(cls):
        # OUTPUT(*varNames)
        return dict(status = cls.toINIT, varlist = True)

    @classmethod
    def getTitle(cls):
        # TITLE(simulationTitle)
        return dict(status = cls.toINIT, varlist = False)

    @classmethod
    def getPrepare(cls):
        # PREPARE(*varNames)
        return dict(status = cls.toINIT, varlist = False)

    @classmethod
    def getPrtplot(cls):
        # PRTPLOT(*args, **kwargs)
        return dict(status = cls.UNDECIDED, varlist = False)

    @classmethod
    def getLabel(cls):
        # LABEL(printPlotCaption)
        return dict(status = cls.toINIT, varlist = False)

    @classmethod
    def getRange(cls):
        # RANGE(*varNames)
        return dict(status = cls.toINIT, varlist = False)

    @classmethod
    def getReset(cls):
        # RESET(*args, **kwargs)
        return dict(status = cls.NOT_SUPPORTED, varlist = False)

    


# DATA statements:
def PARAM(value): return value 
def CONSTANT(value): return value 
def INCON(value): return value 
def FUNCTION(*xyPairs): return
def TABLE(**data): return 
def OVERLAY(*args, **kwargs): return


# CONTROL statements:
def RENAME(**synonyms): return
def FIXED(*args, **kwargs): return
def MEMORY(*args, **kwargs): return
def HISTORY(*args, **kwargs): return
def STORAGE(*args, **kwargs): return
def DECK(*args, **kwargs): return
def MACRO(*args, **kwargs): return

# INITIAL
# DYNAMIC
# TERMINAL
# SORT
# NOSORT

def END(*args, **kwargs): return
def CONTINUE(*args, **kwargs): return
def PROCEDURE(*args, **kwargs): return
def STOP(*args, **kwargs): return
def ENDJOB(*args, **kwargs): return
# ENDJOB STACK
def COMMON(*args, **kwargs): return
# COMMON MEM  
def DATA(*args, **kwargs): return


# Execution control statements:
def TIMER(PRDEL = None, OUTDEL = None, FINTIM = None, DELT = None, DELMIN = None): return
def FINISH(**conditions): return
def RELERR(**epsila): return
def ABSERR(**errors): return
def METHOD(method: IntegrationMethod|str): return


# Output control statements:
def PRINT(*varNames): return
def OUTPUT(*varNames): return
def TITLE(simulationTitle): return
def PREPARE(*varNames): return
def PRTPLOT(*args, **kwargs): return
def LABEL(printPlotCaption): return
def RANGE(*varNames): return
def RESET(*args, **kwargs): return


    
