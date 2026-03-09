from csmp import AMIN1, AFGEN, INCON, FUNCTION, EXP, PRINT, TIMER
# based on pag. 69/70 in:
# Goudriaan, J., 19xx. Chapter 2.3: Some techniques in dynamic simulation.
# ?? Simulation of plant growth and crop production.
# Wageningen:Pudoc-III.-(Simulation Monographs)??
# https://edepot.wur.nl/172218

"INITIAL"
TITLE("RESERVES AS A STATE VARIABLE")
RESLI   = INCON(0.1)
RESI    = RESLI*TWT
"DYNAMIC"
RESL    = RES/TWT
RES     = INTGRL(RESI,GPHRED- MAINT- CGR)
MAINT   = 0.015 * TWT
CGR     = 0.1 * RES / (RESL+KRESL)
PARAM(KRESL = 0.1, TWT = 2000.) # array parameters not yet supported
GPHRED  = GPHOT*REDF
GPHOT   = GPHST*(1.- EXP(-0.7 * LAI))
REDF    = AFGEN(REDFT, RESL)
LAI     = AMIN1(WSH / 500., 5.)
WSH     = 0.7 * TWT
REDFT   = FUNCTION(0.,1.,0.2,1.,0.25,0.,0.5,0.)
GPHST   = PARAM(400.)
TIMER(FINTIM= 20., PRDEL= 1., )
PRINT(RES, RESL,GPHRED)