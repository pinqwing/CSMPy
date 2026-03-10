import ast, inspect
from abc import ABC, abstractmethod
from itertools import zip_longest

from csmp.rts.csmpFunction import Csmp_AfGen, Csmp_Function, Csmp_NlfGen
from csmp.rts.model import Timer, Printer
from csmp.rts.integrator import Rect, StateVariable


class NormalFinish(StopIteration):
    def __init__(self, reason):
        super().__init__(f"$$$ Simulation halted for finish condition {reason}")
                

        
class CSMP_Model(ABC):

    @abstractmethod
    def defineConstants(self):      return {}
    
    @abstractmethod
    def defineParameters(self):     return {}
    
    @abstractmethod
    def initial(self):              return {}
        
    @abstractmethod
    def loop(self, time):           return
        
    @abstractmethod
    def final(self):                return
        

    
    def __init__(self):
        self.title          = 'simulation'
        self.timer          = Timer()
        self.globals        = {}
        self.functionBlocks = {} # by both index & name
        self.funcGenerators = {} # by both index & name
        self.stateVars      = {} # by index
        self.stateNames     = {} # by name
        self.integrator     = Rect(self)
        self.printer        = Printer()
        self.finished       = False
        
    stateVariables = property(lambda m: m.stateVars.values())
                
    
    def run(self):
        # self.endConditions.append(EndCondition("RES", 450, ">="))
        def findVariable(name, loopVars: dict, notFound = -99999):
            result = self.stateNames.get(name)
            if result is not None: return result.value
            result = loopVars.get(name)
            if result is not None: return result
            result = self.globals.get(name)
            if result is not None: return result
            return notFound

        print(self.title)
        self.timer.start()
        self.printer.printHeader()
        
        try:
            while True:
                v = self.loop(self.timer.time)
                
                if self.timer.printRequired():
                    prVars = dict([(name, findVariable(name, v)) for name in self.printer.varNames])
                    self.printer.print(self.timer.time, prVars)
                
                if self.finished:
                    raise NormalFinish(self.finished)
                
                self.integrator.run()
                
                if not self.timer.setTimeStep():
                    raise NormalFinish(f"time >= {self.timer.finTim}")
                
        except NormalFinish as e:
            print(e)
        

    def _addElement(self, element, itemDict, elementCatName, index = None, name = None):
        def doAdd(dictIndex):
            if dictIndex is None: return 
            if dictIndex in itemDict:
                raise Exception(f"attempt to redefine {elementCatName} with index {index} ('{name}')")
            itemDict[dictIndex] = element
            
        doAdd(index)
        doAdd(name)
        return element
    
    
    def createCsmpFunction(self, index, name, *args):
        # not just *a* function, but FUNCTION 
        newFunction = Csmp_Function(*args)
        return self._addElement(newFunction, self.functionBlocks, "function", index, name)
    
    
    def createCsmpAFGEN(self, index, function, **kwargs):
        newGenerator = Csmp_AfGen(self.functionBlocks[function], **kwargs)
        return self._addElement(newGenerator, self.funcGenerators, "function generator", index)
    
    
    def createCsmpNLFGEN(self, index, function, **kwargs):
        newGenerator = Csmp_NlfGen(self.functionBlocks[function], **kwargs)
        return self._addElement(newGenerator, self.funcGenerators, "function generator", index)
    
    
    def createStateVariable(self, index, name, initialValue):
        newState = StateVariable(name, initialValue)
        self._addElement(newState, self.stateVars,  "state variable", index)
        self._addElement(newState, self.stateNames, "state variable", name = name)
        return newState
    
    
    def getState(self, index):
        return self.stateVars[index].value
    
    
    def setCurrentRate(self, index, rate):
        self.stateVars[index].rate = rate
        
        
    def setTimer(self, **params):
        try:
            self.timer.changeParameters(**params)
        except RuntimeError as rte:
            rte.args = ("%s in setTimer() (%s)" % rte.args,)
            raise 
    
            
    def setMethod(self, integrationMethod):
        pass
    
    
    def setPrint(self, *varNames):
        self.printer = Printer(varNames)
    
    
    def setOutput(self, *varnames):
        pass
    
    
    def setTitle(self, title):
        self.title = title
    

    def checkEndConditions(self, *args):
        
        def unIndent(lines):
            ldsp  = 0xff                # number of leading spaces
            for line in lines:
                if not line.strip():    
                    continue            # skip no-code lines
                ldsp = min(ldsp, len(line) - len(line.lstrip(" ")))
                if ldsp == 0:           
                    return lines    # code block not indented
            
            return [line[ldsp:] for line in lines]
        
        def getArgSource():
            frame = inspect.currentframe().f_back.f_back
            try:
                src, start  = inspect.getsourcelines(frame)
                target      = frame.f_lineno - start + 1     # = relative line nr
                tree        = ast.parse("".join(unIndent(src)))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and node.lineno == target:
                        return [ast.unparse(arg) for arg in node.args]
                else:
                    return ["not found!"]
            except Exception as e:
                return [str(e)]
            
        if any(args):
            aSrc = getArgSource()
            # get call argument for flagged end condition:
            matches = [s for a, s in zip_longest(args, aSrc, fillvalue = "??)") if a]
            self.finished = ", ".join(matches)

    
    
    