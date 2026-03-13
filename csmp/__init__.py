from csmp.keywords import PARAM, CONSTANT, INCON, FUNCTION, TABLE, OVERLAY, RENAME, FIXED, MEMORY, HISTORY, STORAGE, DECK, MACRO, END, \
    CONTINUE, PROCEDURE, STOP, ENDJOB, COMMON, DATA, TIMER, FINISH, RELERR, ABSERR, METHOD, PRINT, OUTPUT, TITLE, PREPARE, PRTPLOT, LABEL, RANGE, RESET

from csmp.functions import ABS, AFGEN, ALOG, ALOG10, AMAX0, AMAX1, AMIN0, AMIN1, AND, ATAN, CMPXPL, COMPAR, COS, DEADSP, DELAY, DERIV, EOR, EQUIV, EXP, \
    FCNSW, GAUSS, HSTRSS, IABS, IMPL, IMPULS, INSW, LEDLAG, LIMIT, MAX0, MAX1, MIN0, MIN1, MODINT, NAND, NLFGEN, NOR, NOT, OUTSW, PULSE, RAMP, REALPL, \
    RNDGEN, RST, SIN, SINE, SQRT, STEP, TANH, ZHOLD

from csmp.rts.linearExtrapolators import Clip, LastSegment, Regression
from csmp.rts import CSMP_Model




import warnings,sys, inspect

def simpleWarning(message, category, filename, lineno, line=None):
    return f"{category.__name__}: {message}\n"

warnings.formatwarning = simpleWarning




IS_RELEASE = not True  # set this value to True in releases to prevent user-overload

def lessSimpleErrors(type, value, tb):
    try:
        # print(f"{type.__name__}: {value}", file = sys.stderr)
        # reduced error tracing with still some info:
        last_frame  = tb
        while last_frame.tb_next:
            last_frame = last_frame.tb_next
        instance    = last_frame.tb_frame.f_locals.get('self')
        cls         = instance.__class__
        fileName    = inspect.getfile(cls).split("/")[-1]
        print(f"{type.__name__}: {value} [{cls.__name__} in {fileName}]", file = sys.stdout)
    except:
        # if that didn't work out, call original:
        savedHook(type, value, tb)


if IS_RELEASE:
    savedHook       = sys.excepthook 
    sys.excepthook  = lessSimpleErrors
else:
    sys.tracebacklimit = 3
    
