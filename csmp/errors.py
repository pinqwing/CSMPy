import inspect


# ----- exception Hierarchy --------------------------------------------------

class CSMPyError(Exception):        pass    # general ancestor

class ProgramError(CSMPyError):     pass    # errors likely due to this software

class ModelError(CSMPyError):       pass    # errors due to faulty precompiler

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


# ---- specific exceptions ----------------------------------------------------

class MacroError(PrecompilerError): 
    pass


class NotYetImplementedError(PrecompilerError):
    def __init__(self):
        caller = inspect.stack()[1][3]
        super().__init__("function '%s' has not been implemented yet" % caller)


class SegmentationError(PrecompilerError):
     pass
    
        


