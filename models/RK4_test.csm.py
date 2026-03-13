from csmp import MACRO, TITLE, PARAM, CONSTANT, METHOD, TIMER, OUTPUT, PRINT
from csmp import EXP, AMIN1
from csmp import Clip
from csmp.keywords import INCON

TITLE("RK4 INTEGRATION TEST (2)")
# dxdt = − t/x with x(0) = 1
# exact solution: t^2 + x^2 = 1 (circle)
#
# choose h = 0.1 = DELT

x    = INTGRL(1., dxdt)
t    = INTGRL(0., 1.)
dxdt = -t / x
TIMER(DELT = 0.1, FINTIM = 1.0, PRDEL = -1)

# first step:
#     k1 =   0.0
#     k2 = − 0.005
#     k3 = − 0.00501253132832
#     k4 = − 0.010 0503778338
# and t1 --> 0.1
#     x1 --> 0.994987426585
#
# expected output:
#
#     time    x
#     0,0     1,0
#     0,1     0,994987426585
#     0,2     0,979795852198
#     0,3     0,95393908717
#     0,4     0,916514893222
#     0,5     0,866024896597
#     0,6     0,799998909634
#     0,7     0,714140165921
#     0,8     0,599991210485
#     0,9     0,435832710519
#     1,0     0,0488018582123 (exact solution would have been 0.0