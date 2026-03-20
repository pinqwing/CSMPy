# -- encoding: utf-8 ---
from csmp import MACRO, TITLE, PARAM, CONSTANT, METHOD, TIMER, OUTPUT, PRINT
from csmp import EXP, AMIN1
from csmp import Clip

TITLE("DRY MATTER PRODUCTION")

MACRO("""
    X, DXDT  = EXPONENTIAL(X0, A, B)
    X        = INTGRL(X0, DXDT)
    RATE     = A * (X - B)
    DXDT     = RATE
    """)

# --- INITIAL ---"
T = 0 # t to test initial segment

# --- DYNAMIC ---    
TWT     = WSH + WRT
WSH     = INTGRL(WSHI, GSH)
WRT     = INTGRL(WRTI, GRT)
WSHI    = INCON(50.)
WRTI    = INCON(50.)
GSH     = 0.7 * GTW
# COMMENTAAR
GRT     = 0.3 * GTW
GTW     = (GPHOT - MAINT) * CVF
MAINT   = (WSH + WRT) * 0.015
GPHOT   = GPHST * (1. - EXP(-0.7 * LAI))
LAI     = AMIN1(WSH / 500.,  5.)
EX1, R1 = EXPONENTIAL(10., 0.1, 5) 
EX2, R2 = EXPONENTIAL(WRTI, CVF, GPHST / 5.) 
REDFT   = FUNCTION(0.,1.,0.2,1.,0.25,0.,0.5,0.)
REDF    = AFGEN(REDFT,LAI*4 - R1, extra=Clip)
REDF1    = AFGEN(REDFT,LAI*4 - R1, extra=Clip)
REDF2    = MEMORY(AFGEN(REDFT,LAI*4 - R1, extra=Clip), 0)
rgr      = PARAM(0.123)

PARAM(
    CVF = 0.7, 
    GPHST = 400.,
    PPI = PI    
    )
c   = CONSTANT(123)
CONSTANT(
    PI = 3.141592,
    PI2 = 2 * PI,
    )      

TIMER(FINTIM = 100., DELT = 1., PRDEL = 5., OUTDEL = 5.)
METHOD("RECT")
PRINT(TWT, WSH, WRT, GTW)
OUTPUT(TWT)
