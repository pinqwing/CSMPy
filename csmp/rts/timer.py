import numpy
from math import floor, ceil, log2
from warnings import warn
from csmp.errors import SimulationError


class WaitstateCounter:
    '''
    counter to ick away one wait state per time step.
    If ready, stepsize increment is allowed.
    '''
    
    def __init__(self, count: int):
        self.count = count
        self.value = 0
        
    def pop(self):
        if self.value > 0:
            self.value -=1 
            
    def set(self, count = -1):
        self.value = self.count if count < 0 else count
        
    def ready(self):
        return self.value == 0



class EventQueue(list):

    def __init__(self, interval = 1, finalValue = 10, overshoot = 0):
        '''queue for print and output events
        
        args:
            interval:    time between the events
            finalValue:  time of last event  
            overshoot:   number of extra items as protection against exceeding requests 
        '''
        super().__init__([i * interval for i in range(round(finalValue/interval + overshoot))])
        
            
    def get(self, default = 0.):
        ''' return the topmost time, if any
        args:
            default: returned if no events left
        '''
        if self:
            return self[0]
        return default
    
    
    def purge(self, condition = lambda event: False):
        ''' like get(), but simultaneously removing the topmost event.
        args:
            default: returned if no events left
        '''
        while self and condition(self.get()):
            self.pop(0)
        
        
# DELT. The value of DELT is the integration interval or step-size of the indepen-
# dent variable. If DELT is specified, it is automatically adjusted if necessary to be a
# submultiple of PRDEL or OUTDEL. If neither PRDEL or OUTDEL has been
# specified, DELT is adjusted to be a submultiple of FINTIM / 1OO. When DELT is
# not specified, the first integration step is 1/16th of the smaller value of PRDEL or
# OUTDEL. For either of the variable-step integration methods there is no need to
# specify a value for DELT unless the user feels that the first step-size (io of smaller
# value of PRDEL or OUTDEL) is too large.


WAITSTATES  = 5 # nr of time steps to wait between step increments
calcDelt    = lambda base, exp: base / 2**exp


class BaseTimer:
    
    def __init__(self, FINTIM, PRDEL = -1, OUTDEL = -1, DELT = -1, DELMIN = -1, TIME = 0):
        if PRDEL > FINTIM:  
            warn(f"PRDEL ({PRDEL}) > FINTIM ({FINTIM}): truncated", category=RuntimeWarning)
            PRDEL = FINTIM
        if OUTDEL > FINTIM:  
            warn(f"OUTDEL ({OUTDEL}) > FINTIM ({FINTIM}): truncated", category=RuntimeWarning)
            OUTDEL = FINTIM
            
        self._prnTimes      = EventQueue()
        self._outTimes      = EventQueue()
        
        self.time           = TIME
        self.finTim         = FINTIM
        self.delMin         = FINTIM / 1E07
        self.delMin         = DELMIN if DELMIN > 0 else self.finTim / 1E07
        
        self.prDel          = PRDEL  if PRDEL  > 0 else max(self.delMin, self.finTim / 100)        
        self.outDel         = OUTDEL if OUTDEL > 0 else self.prDel
        
        if DELMIN > self.prDel:  raise SimulationError("DELMIN > PRDEL")
        if DELMIN > self.outDel: raise SimulationError("DELMIN > OUTDEL")
        
        self._specifiedDelt = DELT
        self._currentDelt   = DELT
        self.stepCount      = 0
        
    
    def clone(self, newTimerClass):
        return newTimerClass(FINTIM = self.finTim,
                              PRDEL = self.prDel,  
                             OUTDEL = self.outDel, 
                               DELT = self._specifiedDelt,
                             DELMIN = self.delMin,
                               TIME = self.time)
                    
                    
    def __str__(self):
        name = type(self).__name__.replace("StepTimer", "")
        return f"time = {self.time}; delt = {self.delt}; final = {self.finTim}; step = {self.stepCount} [{name}]"
    
            
    def nextStepSize(self):
        if self.time > self.finTim:
            return numpy.nan
        
        regularNext = self.time + calcDelt(self.delMax, self._shiftDel)
        
        mileStones  = [event for event in 
                        (self._prnTimes.get(default = self.finTim), 
                         self._outTimes.get(default = self.finTim),
                         self.finTim, regularNext) if event > self.time]
        return min(numpy.array(mileStones) - self.time)  
    
    
    def start(self):
        self.stepCount      = 0
        self.time           = 0.0
        self._outTimes      = EventQueue(self.outDel, self.finTim, overshoot = 2)
        self._prnTimes      = EventQueue(self.prDel, self.finTim, overshoot = 2)
    
    
    def next(self):
        # uptime with delt used un the current time step:
        self.stepCount  += 1
        self.time       += self._currentDelt
        
        # purge event queus:
        pastEvents = lambda e: e < self.time
        self._prnTimes.purge(pastEvents)
        self._outTimes.purge(pastEvents)
    
        # returt True while not done:
        return self.time < self.finTim
    
    
    def simulationComplete(self):
        return self.time >= self.finTim
    
    
    def outputRequired(self):
        return self.time >= self._outTimes[0]
    
    
    def printRequired(self):
        return self.time >= self._prnTimes.get(self.finTim)
    
    
class FixedStepTimer(BaseTimer):
    @property
    def delt(self):
        return self._specifiedDelt
    
    @delt.setter
    def delt(self, value):   
        self._specifiedDelt = value
        

class VariableStepTimer(BaseTimer):
    
    def __init__(self, FINTIM, PRDEL=-1, OUTDEL=-1, DELT=-1, DELMIN=-1, TIME=0):
        super().__init__(FINTIM, PRDEL, OUTDEL, DELT, DELMIN, TIME)
        self.delMax, \
        self._shiftDel      = self._initialDelt(DELT)
        self._currentDelt   = 0 
        self._incrWait      = WaitstateCounter(WAITSTATES)
        
        
    @property
    def delt(self):
        return self._currentDelt
    
    @delt.setter        
    def delt(self, value):
        raise AttributeError(f"property 'delt' of '{type(self).__name__}' is managed and cannot be set")

        
    def _initialDelt(self, _specifiedDelt):    
        target      = min(self.prDel, self.outDel)
        start       = _specifiedDelt if _specifiedDelt > 0 else target / 16
        shiftExp    = max(0, ceil(log2(target / start)))
        
        
        while calcDelt(target, shiftExp) < self.delMin:
            if shiftExp <= 0:
                raise SimulationError("cannot adjust DELT due to DELMIN")
            shiftExp -= 1
        
        return target, shiftExp
        
    
    def _updateDelt(self):
        # store delt as it is now onto _currentDelt
        self._currentDelt = self.nextStepSize() 


    def start(self):
        super().start()
        self._updateDelt()
    
    
    def next(self):
        finished = super().next()    
        # determine delt for the upcoming time step: 
        self._updateDelt()
        # decrease increment-wait states:
        self._incrWait.pop()
        return finished
    
    
        
        
    def decreaseTimestep(self):
        # halve the timestep by increasing shiftDel
        if calcDelt(self.delMax, self._shiftDel + 1) < self.delMin:
            return False
        else:
            self._shiftDel += 1
            self._incrWait.set()
            self._updateDelt()
            return True
    
    
    def increaseTimestep(self):
        # double the timestep by decreasing shiftDel
        incrementAllowed = ((self._shiftDel  > 0)       # not at the max yet
                         and self._incrWait.ready())    # no more wait states
        
        if incrementAllowed:
            if calcDelt(self.delMax, self._shiftDel - 1) <= min(self.prDel, self.outDel):
                self._shiftDel -= 1
                self._incrWait.set()
                self._updateDelt()
                return True
        return False





if __name__ == '__main__':
    
    t = FixedStepTimer(FINTIM = 100, PRDEL = 10, OUTDEL = 5, DELT = 3)
    print(t)
    print(t.delt)
    t.delt = 0
    
    t = VariableStepTimer.cloned(t)
    print(t)
    print(t.delt)
    t.delt = 0
