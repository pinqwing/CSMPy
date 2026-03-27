import inspect


class PrecompilerWarning(Warning): pass


# ----- exception Hierarchy --------------------------------------------------

class CSMPyError(Exception):        pass    # general ancestor

class ProgramError(CSMPyError):     pass    # errors likely due to this software

class ModelError(CSMPyError):       pass    # errors due to faulty precompiler ... ???

class SimulationError(ModelError):  pass    # raised during model execution

class PrecompilerError(ModelError):         # raised during pre-compilation

    def setLine(self, lineNo: int):
        self.args = ("%s (line %d)" % (self.args[0], lineNo),)

    @staticmethod
    def rewriteSyntaxError(error: SyntaxError, preambule: str = None):
        result = [preambule] if preambule is not None else []
        result.append(error.msg)   
        result.append(error.text.replace("\n", ""))   
        result.append(f"{'^':>{error.offset}}")
        return result

    @classmethod
    def fromSyntaxError(cls, error: SyntaxError, preambule: str = None):
        msg = "\n".join(cls.rewriteSyntaxError(error, preambule))
        return cls(msg)
    

# ---- specific exceptions ----------------------------------------------------

class MacroError(PrecompilerError): 
    pass


class NotYetImplementedError(PrecompilerError):
    def __init__(self, caller = None):
        if caller is None:
            caller = inspect.stack()[1][3]
        super().__init__("function '%s' has not been implemented yet" % caller)


class SegmentationError(PrecompilerError):
     pass
    
        


# DIAGNOSTIC MESSAGES
# Diagnostic messages may occur during both the translation and execution phases of the
# program and are designed to be self-explanatory. S orne of the diagnostic checks
# detect illegal characters or incorrect syntax; the symbol "$" is printed below the
# detected error prior to the associated diagnostic message. A "warning only"
# message is printed when an error is not wholly discernible in translation or does
# not destroy the "validity" of simulation. Some examples of these errors are:
# Output variable name not unique
# Control variable name not a systems variable
# Parameter value not specified
# Variable used as input to a section not available from any prior section
# Some examples of errors causing a run halt at the end of translation are:
# Incorrect structure or data statement format
# Invalid data card type
# Unspecified implicit loop
# RELERR speCification on other than an integrator output name
# Examples of errors causing a run halt during execution are:
# Failure of an integration or implicit function to meet the error criterion
# A misspelled subroutine name
# The following is a list of the diagnostic messages with their explanations and suggested
# corrections:

CSMP_DIAGNOSTIX = (
        (100,
            '"CALL RERUN" CAN ONLY BE USED IN A TERMIN SEGMENT. PROBLEM TERMINATED.',
            ['CALL RERUN can be used only in a TERMINAL segment. If it is used elsewhere, the run terminates.',
            ]),
        
        (101,
            'CSMP STATEMENT INCORRECTLY WRITTEN',
            ['The translation phase has detected an error in the statement printed before this mes-',
             'sage. The statement should be checked carefully, including parentheses and commas.', 
             'Although translation of" the source statements will continue, the run will be termi-', 
             'nated before the execution phase.', 
            ]),
        
        (102,
            'CSMP STATEMENT OUT OF SEQUENCE',
            ['The sequence of input statements cannot be processed and the run will be terminated',
             'before the execution phase. The statement should be checked for sequence in the input', 
             'deck to see if it has been misplaced. MACRO definitions must precede all structure', 
             'statements. An INITIAL segment, when used, must precede the DYNAMIC segment.', 
             'If used, the TERMINAL segment must follow the DYNAMIC segment.', 
            ]),
        
        (103,
            'DATA HAS NOT BEEN SPECIFIED FOR AN AFGEN FUNCTION / DATA HAS NOT BEEN SPECIFIED FOR AN NLFGEN FUNCTION',
            ['An AFGEN (or NLFGEN) function generator has peen used in a structure state-',
             'ment but the corresponding data has not been specified using the FUNCTION', 
             'statement. The run will be terminated.', 
            ]),
        
        (104,
            'DYNAMIC STORAGE EXCEEDED. THIS CASE CANNOT BE RUN.',
            ['The SOOO-word limitation on simulator data storage has been exceeded. The storage',
             'in this array includes the current values of model variables, function and error tables,', 
             'central integration history, and subscripted variable values. The problem should be', 
             'analyzed to determine where equations can be combined to reduce the number of', 
             'required entries in the array.', 
            ]),
        
        (105,
            'ERROR - CENTRAL INTEGRATION ROUTINE NOT SUPPLIED',
            ['The user has used the word CENTRL for his integration method on the METHOD',
             'execution control card; however, he has not supplied the integration deck to the pro-', 
             'gram. The run will be terminated.', 
            ]),
        
        (106,
            'ERROR IN COORDINATE ENTRIES',
            ['An error has been detected in the previously printed FUNCTION data statement.',
             'There is either an odd number of entries in the data table or an improper sequence', 
             'of X-coordinate values. The run will be terminated.', 
            ]),
        
        (107,
            'ERROR IN TABLE ENTRY',
            ['In the previously printed TABLE qata statement, an error has been detected. Although',
             'reading of the data statements will continue, the run will be terminated before execution.', 
            ]),
        
        (108,
            'ERROR IN PRINT-PLOT STATEMENT',
            ['An error has been detected in the PR TPLOT output control statement. The statement',
             'should be checked for a correct number of parentheses and commas for specifying', 
             'lower and upper limits, particularly if one or the other is missing, and commas are', 
             'used to indicate this. Although the run continues, everything on the card after the', 
             'error is disregarded.', 
            ]),
        
        (109,
            'EXCEEDED MAXIMUM ITERATIONS ON IMPLICIT LOOP',
            ['One hundred iterations of the implicit loop have been run and convergence has not yet',
             'occurred. The run has been terminated. One possibility is to change the error con-', 
             'dition, so that the convergence criteria can be met.', 
            ]),
        
        (110,
            'FINTIM IS ZERO. THIS CASE CANNOT BE EXECUTED.',
            ['FINTIM either has not been specified or has been specified as being equal to zero.',
             'GENERATED STATEMENT No. @XX', 
             'The translator has detected an error during generation of statement xx of an in-', 
             'voked MACRO in the structure of the model. Carefully check the corresponding', 
             'statement of the MACRO definition for proper spelling and punctuation.', 
            ]),
        
        (111,
            'ILLEGAL CHARACTER OR DOUBLE OPERATOR',
            ['In the previously printed statement, an illegal character or double operator has been',
             'detected. Although translation of the source statements will continue, the run will', 
             'be terminated before the execution phase.', 
            ]),
        
        (112,
            'INCORRECT IMPLICIT STATEMENT',
            ['The translation phase has detected an error in the IMPL structure statement printed',
             'before this message. The statement should be checked to see that the third argument', 
             'is the output name of the last statement in the definition and that the block output', 
             'appears at least once to the right of an equal sign. Although translation of the source', 
             'statements will continue, the run will be terminated before the execution phase.', 
            ]),
        
        (113,
            'INCORRECT MACRO STATEMENT',
            ['The translation phase has detected an error in the MACRO use statement printed',
             'before this message. The statement should be checked to ensure that the number of', 
             'arguments and outputs is correct and that argument list ends with a parenthesis.', 
             'Although translation of the source statements will continue, the run will be termi-', 
             'nated before the execution phase.', 
            ]),
        
        (114,
            'INCORRECT TIMER VAR. NAME**WARNING ONLY',
            ['One of the system variable names (FINTIM, DELT, PRDEL, OUTDEL, or',
             'DELMIN) has been misspelled on the TIMER execution control card. The user should', 
             'also check the possibility that the system variable has been renamed. Although the', 
             'run will continue, the system variable misspelled will be unchanged.', 
            ]),
        
        (115,
            'INPUT NAME SAME AS OUTPUT NAME',
            ['The output variable name to the left of the equal sign has also been used as an input',
             'name on the right side of the equal sign. Except as output of a memory type functional', 
             'element, such usage is not permissible in a parallel, sorted section. The run will', 
             'be terminated.', 
            ]),
        
        (116,
            'INPUT TO FUNCTION GENERATOR nnnnnn BELOW SPECIFIED RANGE INPUT = xxxx.XXXX',
            ['The input (xxxx.xxxx) to the function generator named @NNNNNN is below the minimum',
             'specified range. The program will take the value for the minimum specified and con-', 
             'tinue. This message will be printed only once, even though the condition is reached', 
             'several times.', 
            ]),
        
        (117,
            'INPUT TO FUNCTION GENERATOR nnnnnn ABOVE SPECIFIED RANGE INPUT = xxxx.XXXX',
            ['The input (xxxx. xxxx) to the function generator named @NNNNNN is above the maximum',
             'specified range. The program will take the value for the maximum specified and', 
             'continue. This message will be printed only once, even though the condition is', 
             'reached several times.', 
            ]),
        
        (118,
            'LABEL INCORRECTLY WRITTEN',
            ['The label used in the preceding statement cannot be recognized by the program. Check',
             'for proper spelling. The statement will be disregarded; the run will continue.', 
            ]),
        
        (119,
            'MACRO xxxxxx WITHIN MACRO yyyyyy USED IN A PROCEDURAL SECTION',
            ['MACROs, separately defined, may be invoked within the definition of other MACROs',
             'if overall parallel structure is implied. Invocation of a MACRO within a PROCEDURE', 
             'within a MACRO definition is therefore not permissible. Similarly, a MACRO containing', 
             'other MACROs in its definition may not be invoked from a PROCEDURE or from a', 
             'procedural section.', 
            ]),
        
        (120,
            'MORE THAN 10 PRTPLOT STATEMENTS',
            ['More than ten PRTPLOT output control statements have been specified. Only the first',
             'ten will be used.', 
            ]),
        
        (121,
            'NUMBER EXCEEDS 12 CHARACTERS',
            ['In the previously printed statement, a number exceeding twelve characters in a',
             'MACRO argument or integrator block initial condition has been detected. Although', 
             'translation of the source statements will continue, the run will be terminated before', 
             'the execution phase.', 
            ]),
        
        (122,
            'NUMBER INCORRECTLY WRITTEN',
            ['In the previously printed statement, a number written incorrectly has been',
             'detected. If detected during the translation phase, translation of the source', 
             'statements will continue; however, the run will be terminated before the execution', 
             'phase.', 
            ]),
        
        (123,
            'ONLY FIRST 10 CONDITIONS FOR JOB END WILL BE TESTED',
            ['More than ten specifications have been given with the FINISH execution control state-',
             'ment. Although the run will continue, only the first ten specifications will be used.', 
            ]),
        
        (124,
            'ONLY FIRST 50 VALUES WILL BE USED',
            ['The multiple value form of the PARAMETER data statement has been used with',
             'more than 50 values for the parameter. A sequence of runs will be performed,', 
             'but using only the first 50 values for the parametric study.', 
            ]),
        
        (125,
            'ONLY FIRST 50 VARIABLES WILL BE PREPARED',
            ['More than 50 variables (including TIME) have been specified with PREPARE or',
             'PRTPLOT output control statements. Although the run will continue, only the', 
             'first 50 variables will be used.', 
            ]),
        
        (126,
            'ONLY FIRST 50 VARIABLES WILL BE PRINTED',
            ['More than 50 variables (including TIME) have been requested with PRINT execution',
             'control statements. Only the first 50 will be printed; others will be ignored.', 
            ]),
        
        (127,
            'ONLY FIRST 100 VARIABLES WILL BE RANGED',
            ['More than 100 variables (including TIME) have been specified with the RANGE',
             'output control statement. Although the run will continue, only the first 100', 
             'variables will be used.', 
            ]),
        
        (128,
            'ONLY LAST VALUE OF FAMILY USED FOR CONTIN RUN',
            ['A multiple-value parameter has been used with a CONTINUE card. THE CONTINUE',
             'control feature will be implemented only with the last value of the parameter. This', 
             'is a warning message; the run will continue.', 
            ]),
        
        (129,
            'OUTPUT NAME HAS ALREADY BEEN SPECIFIED',
            ['In the previously printed statement, the output variable name to the left of the equal',
             'sign has been used before as an output variable name; that is, it has occurred to', 
             'the left of the equal sign in a preceding section. The run will be continued.', 
            ]),
        
        (130,
            'PARAMETERS NOT INPUT OR OUTPUTS NOT AVAILABLE TO SORT SECTION***SET TO ZERO***',
            ['A list of variable names will be printed following this heading. The run is continued.',
             'Variables that are not parameters specified on data cards are set to zero. Output', 
             'variable names that are not available to this sort section are initially set to zero, but', 
             'may change as the problem is run.', 
            ]),
        
        (131,
            'PROBLEM CANNOT BE EXECUTED',
            ['At least one diagnostic message will have been printed among the source statements',
             'indicating the reason why the problem cannot be executed. The run will be terminated.', 
            ]),
        
        (132,
            'PROBLEM INPUT EXCEEDS TRANSLATION TABLE nn',
            ['During translation of the problem, a table has been exceeded and the run will termi-',
             'nate. The specific table is identified by nn in the following list:', 
            ]),
        
        (133,
            'PRTPLOT, PREPARE, AND RANGE VARIABLES EXCEED 100. ALL RANGE VARIABLES STARTING WITH xxxxxx HAVE BEEN DELETED.',
            ['More than 100 variables (including TIME) have been specified with PRTPLOT,',
             'PREPARE, and RANGE output control statements. Although the run will', 
             'continue, only the first 100 variables will be used for this run.', 
            ]),
        
        (134,
            'RERUN FROM TERMIN CANCELED FOR CONTIN RUN',
            ['The TERMINAL segment cannot be used to cause a rerun when a CONTINUE translation',
             'control statement started the run. The TERMINAL computation statements will be', 
             'executed but any CALL RERUN will be ignored.', 
            ]),
        
        (135,
            'SIMULATION HALTED',
            ['The run was terminated because a FINISH condition was satisfied. The variable',
             'name and its value are printed.', 
            ]),
        
        (136,
            'SIMULATION INVOLVES AN ALGEBRAIC LOOP CONTAINING THE FOLLOWING ELEMENTS',
            ['A list of output variable names will be printed following this diagnostic. The sort',
             'subprogram has been unable to find an integration or memory block in the loop', 
             'involving these variables. The run will be terminated before the execution phase.', 
            ]),
        
        (137,
            'SYMBOLIC NAME xxxxxx NOT DEFINED',
            ['An error has been detected on the PARAMETER, INC ON, CONSTANT, or TIMER',
             'card printed before this message. Although input to the execution phase will', 
             'continue, the simulation will not be roo.', 
            ]),
        
        (138,
            'SYMBOLIC NAME EXCEEDS 6 CHARACTERS',
            ['In the previously printed statement, a symbolic name exceeding six characters',
             'has been detected. Although translation of the source statements will continue,', 
             'the run will be terminated before execution.', 
            ]),
        
        (139,
            'SYMBOLIC NAME INCORRECTLY WRITTEN',
            ['In the previous statement, an incorrectly written symbolic name has been',
             'detected. The run will be terminated.', 
            ]),
        
        (140,
            'TOO MANY CONTINUATION CARDS. MAX=n',
            ['The previously printed statement has been continued on too many cards. If N = 3, a',
             'MACRO label statement has over three continuation statements. If N = 8, a structure', 
             'statement has over eight continuation statements. The user should make multiple', 
             'statements or use more columns on individual cards. Al though translation of the', 
             'source statements will continue, the run will be terminated before the execution', 
             'phase.', 
            ]),
        
        (141,
            'TOO MANY LEFT PARENTHESES / TOO MANY RIGHT PARENTHESES',
            ['Too many left (or right) parentheses have been detected in the statement printed before',
             'this diagnostic. Although the translation of the source statements will continue, the', 
             'run will be terminated before the execution phase.', 
            ]),
        
        (142,
            'VARIABLE STEP DELT LESS THAN DELMIN. SIMULATION HALT.',
            ['The simulation will not be continued because the specified DELT is less than the',
             'specified DELMIN', 
            ]),
        
        )
