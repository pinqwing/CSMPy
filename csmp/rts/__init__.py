import inspect
from abc import ABC, abstractmethod
from itertools import zip_longest
import lib.ast_comments as ast

from csmp.rts.csmpFunction import Csmp_Afgen, Csmp_Function, Csmp_Nlfgen
from csmp.rts.integrator import StateVariable, RungeKuttaSimpson
from csmp.rts.model import Printer
from csmp.rts.timer import BaseTimer, FixedStepTimer, VariableStepTimer

from csmp.customTypes import IntegrationMethod
from lib.smallUtilities import ConservativeDict
from csmp.rts.history import MemoryFunction


class NormalFinish(StopIteration):
    def __init__(self, reason):
        super().__init__(f"\n$$$ Simulation halted for finish condition {reason}")
                

        
class CSMP_Model(ABC):

    @abstractmethod
    def setUp(self):                ...

    @abstractmethod
    def defineConstants(self):      return {}
    
    @abstractmethod
    def defineParameters(self):     return {}
    
    @abstractmethod
    def initial(self):              return {}
        
    @abstractmethod
    def loop(self, TIME, DELT, KEEP = True):           ...
        
    @abstractmethod
    def final(self):                ...
        

    
    def __init__(self):
        self.title          = 'simulation'
        self.timer          = BaseTimer(10.)
        self.setMethod(IntegrationMethod.RKS)
        self.globals        = {}
        self.functionBlocks = {} # by both index & name
        self.funcGenerators = self.functionBlocks
        self.csmpElements   = ConservativeDict() # by index
        self.ratesEtc       = {} # local variables from DYNAMIC
        self.stateVars      = {} # by index
        self.stateNames     = {} # by name
        self.aliases        = {} # inverse of printer.aliases
        self.printer        = Printer()
        self.finished       = False
        self.functionBlocks = self.csmpElements # TODO: how to organize this?
        self.funcGenerators = self.csmpElements
        
        
    stateVariables = property(lambda m: m.stateVars.values())
    memoryFunction = property(lambda m: m.csmpElements)
    historyFuncs   = property(lambda m: m.csmpElements)
                
    def getVariable(self, name, notFound = -99999, checkAliases = True):
        ''' get current value of a named variable 
        args:
            name: name of the variable or state
            notFound: default value if no variable exists with the given name
        '''
        result = self.stateNames.get(name)
        if result is not None: 
            return result.value

        result = self.ratesEtc.get(name, self.globals.get(name))
        if result is not None:
            return result
        
        if checkAliases and (name in self.aliases):
            alias = self.aliases[name]
            return self.getVariable(alias, notFound, checkAliases = False)
        
        return notFound

        
    

    def printEvent(self):
        prVars = dict([(name, self.getVariable(name, "n/a")) for name in self.printer.varNames])
        prVars["TIME"] = self.timer.time
        self.printer.print(self.timer.time, prVars)
        
        
    def commitTimestep(self):
        assert self.integrator.KEEP
        for e in self.csmpElements.values():
            if isinstance(e, MemoryFunction):
                e.commit()
    
    
    def run(self):
        # self.endConditions.append(EndCondition("RES", 450, ">="))
        self.setUp()
        self.integrator.initialize()
        self.aliases = dict([(a, n) for n, a in self.printer.aliases.items()])
        
        print(self.title + "\n")
        self.timer.start()
        self.printer.printHeader()
        self.ratesEtc.update(self.loop(self.timer.time, self.timer.delt))
        
        try:
            lastPrt = -1
            lastOut = -1
            
            while True:
                # propagate history/memory functions:
                self.commitTimestep()
                
                # print output
                if self.timer.printRequired():
                    self.printEvent()
                    lastPrt = self.timer.time

                # check finish conditions:
                if self.finished:
                    raise NormalFinish(self.finished)
                
                # check final time:    
                if self.timer.simulationComplete():                
                    raise NormalFinish(f"time >= {self.timer.finTim}")
                
                # run to next timestep:
                self.integrator.run()
                self.timer.next()
                
        except NormalFinish as e:
            if self.timer.time > lastPrt:
                self.printEvent()
            print(e)
        

    def _addElement(self, element, itemDict, elementCatName, index = None, name = None):
        def doAdd(dictIndex):
            if dictIndex is None: return 
            if dictIndex in itemDict:
                raise Exception(f"attempt to redefine {elementCatName} with index {index} ('{name}')")
                raise Exception(f"attempt to redefine {elementCatName} with index {index} ('{name}')")
            itemDict[dictIndex] = element
            
        self.csmpElements[index] = element
        # doAdd(index)
        # doAdd(name)
        return element
    
    
    def addCsmpElement(self, element, index):
        self.csmpElements[index] = element
        return element
    
    
    def createCsmpFunction(self, index, name, *args):
        # not just *a* function, but FUNCTION 
        newFunction = Csmp_Function(*args)
        return self._addElement(newFunction, self.functionBlocks, "function", index, name)
    
    
    # def createCsmpAFGEN(self, index, function, **kwargs):
    #     newGenerator = Csmp_Afgen(self.functionBlocks[function], **kwargs)
    #     return self._addElement(newGenerator, self.funcGenerators, "function generator", index)
    #
    #
    # def createCsmpNLFGEN(self, index, function, **kwargs):
    #     newGenerator = Csmp_Nlfgen(self.functionBlocks[function], **kwargs)
    #     return self._addElement(newGenerator, self.funcGenerators, "function generator", index)
    
    
    def createGenerator(self, index, genClass, function, **kwargs):
        newGenerator = genClass(self.functionBlocks[function], **kwargs)
        return self._addElement(newGenerator, self.funcGenerators, "function generator", index)
    
    
    def createMemoryFunction(self, index, initialValues):
        newGenerator = MemoryFunction(initialValues)
        return self._addElement(newGenerator, self.historyFuncs, "", index)
    
    
    def createStateVariable(self, index, name, initialValue):
        newState = StateVariable(name, initialValue)
        # self._addElement(newState, self.stateVars,  "state variable", index)
        # self._addElement(newState, self.stateNames, "state variable", name = name)
        self.stateVars[index] = newState
        self.stateNames[name] = newState
        return newState
    
    
    def getState(self, index):
        return self.stateVars[index].value
    
    
    def setCurrentRate(self, index, rate):
        self.stateVars[index].rate = rate
        
        
    def aliasTimerVariables(self, **kwargs):
        self.printer.setAliases(kwargs)
    
    
    def setTimer(self, **params):
        try:
            self.timer = type(self.timer)(**params)
        except RuntimeError as rte:
            rte.args = ("%s in setTimer() (%s)" % rte.args,)
            raise 
    
            
    def setMethod(self, integrationMethod):
        if isinstance(integrationMethod, str):
            integrationMethod = IntegrationMethod[integrationMethod]
        self.integrator =  integrationMethod.value(self)
        # new timer class:
        ntc = VariableStepTimer if self.integrator.variableTimeSteps() else FixedStepTimer
        self.timer = self.timer.clone(ntc)
    
    
    def setPrint(self, *varNames, format = (0, 0)):
        self.printer = Printer(varNames, format)
        
    
    
    def setOutput(self, *varnames):
        pass
    
    
    def setTitle(self, title):
        self.title = title
    

    def checkEndConditions(self, *args):
        
        def _unindent(lines):
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
                tree        = ast.parse("".join(_unindent(src)))
                
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

    
    
    