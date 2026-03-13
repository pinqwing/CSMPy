CSMPy language definition and translation
=========================================

Data statements
-----------------------------------------

Data statements are used to assign numeric values to the. parameters, 
constants, initial conditions, and table entries associated with the 
model. They can be used to assign numeric values to those variables that 
are to be fixed during a given run. The advan- tage of assigning 
variable names and using data statements to specify numeric values is 
that the latter can be changed, automatically, between successive runs 
of the same model structure. 

CONSTANT                                                                          
--------

* CSMP::

    CONSTANT    CON7 =17.95, VEL = 8.7E5
    
* CSMPy::

    CONSTANT(CON7 = 17.95, VEL = 8.7E5)                                          
    
The only obligate difference is that the parameter lists are enclosed in brackets.
The part between the brackets may extend multiple lines::

    CONSTANT(
        CON7 = 17.95, 
        VEL = 8.7E5
        )                                          
        
Alternatively a single-constant syntax is acceptable::

    PI = CONSTANT(3.141592)
    
The constant declarations are sorted and they may refer to each other::

    CYCLE = PARAM(2 * PI)
    
PARAM
---------
* CSMP::

    PARAMETER PARI = 4.98, X=(5.0, 5.5, 3*2.0)                         
    
* CSMPy::

    PARAMETER(PARI = 4.98, X=(5.0, 5.5, 3*2.0))
    
The only obligate difference is that the parameter lists are enclosed in brackets.
The part between the brackets may extend multiple lines::

    PARAMETER(
        PARI = 4.98,            # photo-radiation in [umol/s]
        X=(5.0, 5.5, 3*2.0)     # intrinsic set-off [angstrom/wk]
        )
        
Alternatively a single-parameter syntax is acceptable::

    RGR = PARAM(0.15)
    
Parameters get their value after the CONSTANTs and parameter sections are sorted. 
They  may refer to constants and to each other::

    CYCLE = PARAM(2 * PI)
    
INCON
---------
* CSMP::

    INCON       IC = 9.92, AA = -1.2, AS = 1.79E-3                        
    
* CSMPy::

    INCON(IC = 9.92, AA = -1.2, AS = 1.79E-3)
    
The only obligate difference is that the parameter lists are enclosed in brackets.
The part between the brackets may extend multiple lines::

    INCON(
        IC = 9.92, 
        AA = -1.2, 
        AS = 1.79E-3
        )
        
Alternatively a single-constant syntax is acceptable::

    IC = INCON(0.15)
    
Initial constants get their value after the CONSTANTs and PARAMS. Therefore, they  may refer to either::

    CYCLE = PARAM(2 * PI)
    
FUNCTION
--------
*CSMP::

    FUNCTION REDFT=0.,1.,0.2,1.,0.25,0.,0.5,0
    
*CSMPy::

    REDFT = FUNCTION(0., 1., 0.2, 1., 0.25, 0., 0.5, 0)
    REDFT = FUNCTION((0., 1.), (0.2, 1.), (0.25, 0.), (0.5, 0))
    
FUNCTION defines a data table that is used by AFGEN and NLFGEN functions::

    REDF = AFGEN(REDFT, RESL)
    
    

OVERLAY
--------
As to date, OVERLAY has not yet been implemented.

TABLE
--------
As to date, TABLE has not yet been implemented.


        

Control statements
-----------------------------------------
Control statements are used to specify certain operations associated 
with the translation, execution, and output segments of the program. 
Examples are to specify a certain variable as an integer instead of a 
real (floating-point) number, to specify the finish time for the run, or 
to specify the names of the variables to be printed. The control 
statements may be changed as readily as the data statements. Most of the 
control statements may appear in any order and may be intermixed with 
structure and data statements 


======================================== ========================================
keyword                                     status
======================================== ========================================
RENAME      TIME = DISP, DELT = DELTX
FIXED       K, COUNT, NUMBER                obsolete in Python
MEMORY      RHO(9), PHI(3), GADGET
HISTORY     PARI(4), PAR7(13)
STORAGE     IC( 6), PARAMS(30)              probably obsolete
DECK
MACRO       Xl, X2 = FCN(INI, IN2, IN3)     implemented
    ...
ENDMAC
INITIAl                                     implemented
DYNAMIC                                     implemented
TERMINAL                                    implemented
END                                         ignored by the precompiler
CONTINUE
SORT                                        implemented            
NOSORT                                      implemented
PROCEDURE   X,Y = FUNCT(A, B, X)            use normap python function instead
    ...
ENDPRO
STOP                                        ignored by the precompiler
ENDJOB                                      ignored by the precompiler
ENDJOB STACK                                probably obsolete
COMMON                                      obsolete
COMMON MEM                                  ???
DATA                                        possibly obsolete
    ...
ENDDATA
======================================== ========================================

Execution control 
-----------------------------------------
Execution control statements are used to specify certain items relating to the actual 
simulation run -- for example, run time, integration interval, and 
relative error. 

======================================== ========================================
keyword                                     status
======================================== ========================================
TIMER       DELT=.02, FINTIM=10.0           partly implemented
FINISH      ALT=0.0, X=5000.0, X=Y          implemented
RELERR      XDOT=5.0E-5, X=1.5E-4
ABSERR      X2DOT=4.0E-3
METHOD      MILNE                            a number of methods are operational
======================================== ========================================
    
    
====================================================================== ==========
new syntax
====================================================================== ==========
TIMER(DELT=.02, FINTIM=10.0) # PRDEL, OUTDEL, FINTIM, DELT, DELMIN
FINISH(ALT=0.0, X=5000.0, X=Y)
RELERR(XDOT=5.0E-5, X=1.5E-4)
ABSERR(X2DOT=4.0E-3)
METHOD(MILNE)
====================================================================== ==========
    
    

Output control
-----------------------------------------    
Output control statements are used to specify such
items as the variables to be printed and/or print-plotted.

======================================== ========================================
keyword                                     status
======================================== ========================================
PRINT       X, XDOT, ALT                    implemented
TITLE       PROBLEM DESCRIPTION             implemented
PREPARE     DIST, VELOC
PRTPLOT     X(YI,Y2), Z(3.0, 4.0, Y3), W    * undecided *
LABEL       PRINT PLOT PAGE HEADING
RANGE       ALT, DIST
RESET       PRINT, PRTPLOT, FINISH          * not supported *
======================================== ========================================
    
    
======================================== ========================================
new syntax
======================================== ========================================
PRINT(X, XDOT, ALT)
TITLE("PROBLEM DESCRIPTION")
PREPARE(DIST, VELOC)
PRTPLOT(...)
LABEL("PRINT PLOT PAGE HEADING")
RANGE(ALT, DIST)
======================================== ========================================

