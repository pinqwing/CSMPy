from abc import ABC, abstractmethod
import sys
from csmp.rts.csmpFunction import Csmp_Function, Csmp_AfGen, Csmp_NlfGen
from csmp.customTypes import Comparator
import inspect
import ast
from itertools import zip_longest

class NormalFinish(StopIteration):
    def __init__(self, reason):
        super().__init__(f"$$$ Simulation halted for finish condition {reason}")
                
class StateVariable:
    
    def __init__(self, name, initialValue):        
        self.name  = name
        self.value = initialValue
        self.rate  = 0.0


class Integrator: pass

class Rect(Integrator):
    
    def __init__(self, delta = 1.):
        self.delta = delta
        
        
    def run(self, states):
        for s in states:
            s.value += s.rate * self.delta

    
    def setDeltaTime(self, delt):
        if delt > 0:
            self.delta = delt
    
# class EndCondition:
#
#     def __init__(self, varName, varValue, operator):
#         self.varName    = varName
#         self.tstValue   = varValue
#         self.text       = f"{varName} {operator} {varValue}"
#         self.comparator = lambda v: Comparator[operator](v, varValue)
#
#
#     def __call__(self, value):
#         if self.comparator(value):
#             return True, self.text
#         return False, None
     


class Printer:
    
    def __init__(self, varNames = []):
        self.varNames = varNames
    
    
    def printHeader(self):
        def printHdr(name):
            print("{:>12}".format(name), end = "")
        
        print("{:>8.4}".format("TIME"), end = "")
        for name in self.varNames:
            printHdr(name)
        print()
            
        
    def print(self, time, values):
        def printVar(name):
            x = values.get(name, -99999)
            print("{:>12.4f}".format(x), end = "")
            # print("%12g" % x, end = "")
        
        print("{:>8.4E}".format(time), end = "")
        # print("%8.4E" % time, end = "")
        for name in self.varNames:
            printVar(name)
        print()
            
    
            

class Timer:
    
    def __init__(self, time = 0.0, delt = 1.0, finTim = 10.0, prDel = 1.0, outDel = 1.0):
        self.time   = time
        self.delt   = delt
        self.finTim = finTim
        self.prDel  = prDel
        self.outDel = outDel
        
        
    def changeParameters(self, **params):
        attribs = [name for name in dir(self) if not name.startswith("_")]
        lattrib = [name.lower() for name in attribs]
        try:
            for name, value in params.items():
                i     = lattrib.index(name.lower())
                vName = attribs[i]
                setattr(self, vName, value)
        except ValueError:
            raise RuntimeError("unknown argument", name)
        
        
    def start(self):
        self.time = 0.0
        self._outTimes = [i * self.outDel for i in range(round(self.finTim/self.outDel + 2))]
        self._prnTimes = [i * self.prDel  for i in range(round(self.finTim/self.prDel  + 2))]
        
        
    def printRequired(self):
        return self.time >= self._prnTimes[0]
    
    
    def setTimeStep(self):
        while self._prnTimes[0] <= self.time:
            self._prnTimes.pop(0)
            
        self.time += self.delt
        return self.time < self.finTim
    
        
class CSMP_Model(ABC):
    
    def __init__(self):
        self.title          = 'simulation'
        self.timer          = Timer()
        self.globals        = {}
        self.functionBlocks = {} # by both index & name
        self.funcGenerators = {} # by both index & name
        self.stateVariables = {} # by index
        self.stateNames     = {} # by name
        self.integrator     = Rect()
        self.printer        = Printer()
        self.finished       = False
        
                
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
        self._addElement(newState, self.stateVariables, "state variable", index)
        self._addElement(newState, self.stateNames,     "state variable", name = name)
        return newState
    
    
    def getState(self, index):
        return self.stateVariables[index].value
    
    
    def setCurrentRate(self, index, rate):
        self.stateVariables[index].rate = rate
        
        
    def setTimer(self, **params):
        try:
            self.timer.changeParameters(**params)
            self.integrator.setDeltaTime(params.get("DELT", -1))
            # self.endConditions.append(EndCondition("time", 
            #                                        self.timer.finTim, 
            #                                        ">="))
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
        
        
