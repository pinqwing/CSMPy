from csmp import MACRO, TITLE, PARAM, CONSTANT, METHOD, TIMER, OUTPUT, PRINT
from csmp import EXP, AMIN1
from csmp import Clip
from csmp.keywords import INCON

TITLE("INTEGRATION TEST")

v       = INTGRL(0., dvdt)
u       = INTGRL(2., dudt)

dudt    = v
dvdt    = -oo**2 * u

PI      = CONSTANT(3.141592)
oo      = PARAM(2.)

TIMER(FINTIM = 3., DELT = PI/20., PRDEL = -1)
METHOD("RECT")
PRINT(u, v)

