#@PydevCodeAnalysisIgnore
# based on Fig 17 (pag. 56) in:
# F.W.T. Penning de Vries and H.H. van Laar (eds.), 1982: 
# Simulation of plant growth and crop production.
# Wageningen:Pudoc-III.-(Simulation Monographs)

TITLE("DRY MATTER PRODUCTION")

TWT     = WSH + WRT
WSH     = INTGRL(WSHI, GSH)
WRT     = INTGRL(WRTI, GRT)
INCON(
    WSHI = 50., 
    WRTI = 50.
    )
GSH     = 0.7 * GTW
GRT     = 0.3 * GTW
GTW     = (GPHOT - MAINT) * CVF
MAINT   = (WSH + WRT) * 0.015
GPHOT   = GPHST * (1. - EXP(-0.7 * LAI))
LAI     = AMIN1(WSH / 500.,  5.)

PARAM(
    CVF = 0.7, 
    GPHST = 400.
    )

TIMER(FINTIM = 100., DELT = 1., PRDEL = 5., OUTDEL = 5.)
METHOD("RECT")
PRINT(TWT, WSH, WRT, GTW)
OUTPUT(TWT)
END