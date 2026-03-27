#@PydevCodeAnalysisIgnore
from csmp import MACRO, TITLE, PARAM, CONSTANT, METHOD, TIMER, OUTPUT, PRINT
from csmp import EXP, AMIN1
from csmp import Clip
from csmp.precompiler.csmpStatements import HISTORY

TELLER = MEMORY(100, TELLER + 1)

X0 = INCON(1.)
X = INTGRL(X0, RX)
RX = 1
FN = FUNCTION(0, 0, 5, 1, 10, 0)
T = NLFGEN(FN, X)
#S = HISTORY(hTest(4, "hi"), 1)

TITLE("CSMPy-TEST")
TIMER(FINTIM = 10., DELT = 1., PRDEL = 0.5)
METHOD("RECT")
PRINT(X, RX, T, TELLER)
RENAME(TIME = "Distance", DELT = "step")