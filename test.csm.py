from functions import  *
from keywords  import  *

TITLE("DRY MATTER PRODUCTION")

MACRO("""
    X, DXDT  = EXPONENTIAL(X0, A, B)
    X        = INTGRL(X0, DXTD)
    DXDT     = A * (X - B)
    """)
    
TWT     = WSH + WRT
WSH     = INTGRL(WSHI, GSH)
WRT     = INTGRL(WRTI, GRT)
WSHI    = INCON(50.)
WRTI    = INCON(50.)
GSH     = 0.7 * GTW
GRT     = 0.3 * GTW
GTW     = (GPHOT - MAINT) * CVF
MAINT   = (WSH + WRT) * 0.015
GPHOT   = GPHST * (1. - EXP(-0.7 * LAI))
LAI     = AMIN1(WSH / 500.,  5.)
# EX1, R1 = EXPONENTIAL(10., 0.1, 5) 
EX2, R2 = EXPONENTIAL(WRTI, CVF, GPHST / 5.) 
PARAM(
    CVF = 0.7, 
    GPHST = 400.
    )
CONSTANT(
    PI = 3.141592,
    PI2 = 2 * PI
    )      

TIMER(FINTIM = 100., DELT = 1., PRDEL = 5., OUTDEL = 5.)
METHOD("RECT")
PRINT(TWT, WSH, WRT, GTW)
OUTPUT(TWT)
