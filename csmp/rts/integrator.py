import numpy
from functools import partial


class StateVariable:
    
    def __init__(self, name, initialValue):        
        self.name       = name
        self._value     = initialValue
        self._rate      = 0.0
        self.temp       = None
        self.mapManager = None
        self.mapIndex   = -1
        

    def map(self, mapManager, position):
        self.mapManager = mapManager
        self.mapIndex   = position
        self.setValue(self._value)
        self.setRate(self._rate)

    def isMapped(self):
        return self.mapIndex >= 0
    
    
    def getValue(self):
        return self.mapManager.states[self.mapIndex] if self.isMapped() else self._value
    
    
    def getRate(self):
        return self.mapManager.rates[self.mapIndex] if self.isMapped() else self._rate
    
    
    def setValue(self, value):
        if self.isMapped():
            self.mapManager.states[self.mapIndex] = value
        else:
            self._value = value
    
    
    def setRate(self, rate):
        if self.isMapped():
            self.mapManager.rates[self.mapIndex] = rate
        else:
            self._rate = rate


    value = property(lambda s: s.getValue(), lambda s, v: s.setValue(v))
    rate  = property(lambda s: s.getRate(), lambda s, v: s.setRate(v))
    

    
class StateVariables: 
    def __init__(self, model):
        self.states = numpy.zeros((len(model.stateVariables),), dtype=numpy.float64)
        self.rates  = numpy.zeros_like(self.states)
        self.map(model)
        
    def map(self, model):
        for i, s in enumerate(model.stateVariables):
            s.map(self, i)      
    


class Integrator: 

    def __init__(self, model, storage: StateVariables = None):
        self.model       = model
        self.timer       = model.timer
        self.storage     = storage
        self.isMajorStep = True
        
    KEEP = property(lambda i: 1 if i.isMajorStep else 0) # TODO: make available to the model
    
        
    def getStates(self):            return self.storage.states    
    def getRates(self):             return self.storage.rates
    def setStates(self, states):    self.storage.states = states     
    def setRates(self,  rates):     self.storage.rates  = rates     
    states = property(getStates, setStates)
    rates  = property(getRates,  setRates)
        
        
    def initialize(self):  
        self.storage = StateVariables(self.model) 
        

    def run(self):
        ...
        
           
    def recalculateRates(self, time):
        ratesEtc = self.model.loop(TIME = time, DELT = self.timer.delt, KEEP = self.KEEP)
        if self.isMajorStep:
            self.model.ratesEtc.update(ratesEtc)
            

    def copyArray(self, arr):
        return numpy.array(arr, copy = True)
    
    
    def copyStates(self):
        return numpy.array(self.states, copy = True) # TODO: performance cost of using copyArray?
    
    
    def copyRates(self):
        return numpy.array(self.rates, copy = True)
    
    
    def eulerSteps(self, time, delt, count):
        ''' perfrom a short series of subsequent euler steps
        
        args: 
            time: time for first step
            delt: local step size
            count: number of rate vectors caculated (including the one at tme)
            
        return: 
            list of count rate vectors
            
        note:
            as side effect set isMajorStep to False after each step (but it 
            is not affected within the first step!) 
        '''
        result = []
        for i in range(count):
            self.recalculateRates(time + i * delt)
            self.isMajorStep = False
            self.states += delt * self.rates
            result.append(self.copyRates())
        return result
        
        


class Rect(Integrator):
    
    def run(self):
        self.recalculateRates(self.timer.time)
        self.states += self.timer.delt * self.rates


    

class Trapz(Integrator):

    def run(self):
        Yt = self.copyStates()
        r1, r2 = self.eulerSteps(self.timer.time, self.timer.delt, 2)
        self.rates  = (r1 + r2) / 2.
        self.states = Yt + self.timer.delt * self.rates

        

    
class RungeKutta4thOrder(Integrator):

    def run(self):
        delt = self.timer.delt
        dlt2 = delt / 2.
        Yt   = self.copyStates()
        self.recalculateRates(self.timer.time)
        try:
            self.isMajorStep = False
            k1  = self.rates * delt
            
            self.states = Yt + k1 / 2.  
            self.recalculateRates(self.timer.time + delt / 2.0)
            k2  = self.rates * delt
    
            self.states = Yt + k2 / 2.  
            self.recalculateRates(self.timer.time + delt / 2.0)
            k3  = self.rates * delt
    
            self.states = Yt + k3  
            self.recalculateRates(self.timer.time)
            k4  = self.rates * delt
    
            change      = (k1 + 2 * k2 + 2 * k3 + k4) / 6.
            self.states = Yt + change     
            self.rates  = change / delt
        finally:
            self.isMajorStep = True

            
class Simpson(Integrator):


    def run(self):
        Yt   = self.copyStates()
        delt = self.timer.delt
        dlt2 = delt / 2.0
        
        self.isMajorStep = True
        try:
            # calc Simpson rates X0 .. X2:
            X = self.eulerSteps(self.timer.time, dlt2, 3)
            # Yc = Yt + (delt/6) * (Xt + 4*Xmid + Xend)
            self.rates  = (X[0] + 4.0 * X[1] + X[2]) / 6.0
            self.states = Yt + delt * self.rates
        finally:
            self.isMajorStep = True
            
            
            
            
class RungeKuttaSimpson(RungeKutta4thOrder):
    ERROR_LIMIT = 1./32, 1.
    
    def run(self):
        Yt   = self.copyStates()
        delt = self.timer.delt
        dlt2 = delt / 2.0
        
        self.isMajorStep = True
        try:
            # calc Simpson rates X0 .. X2:
            X = self.eulerSteps(self.timer.time, dlt2, 3)
            # derive RK4's K1 & K2 from the Simpson rates:
            K1, K2 = [delt * x for x in X[:2]]
    
            # K3:
            self.states = Yt + K2 / 2.0
            self.recalculateRates(self.timer.time + dlt2)
            K3 = delt * self.rates
            
            # K4:
            self.states = Yt + K3
            self.recalculateRates(self.timer.time + delt)
            K4 = delt * self.rates
            
            # RK4 resultaat (Yrks)
            change      = (K1 + 2*K2 + 2*K3 + K4) / 6.0
            self.rates  = change / delt 
            self.states = Yt + change 
            Yrks        = self.states
            
            # Simpson result (Ysim):
            Ysim = Yt + (delt / 6.0) * (X[0] + 4.0 * X[1] + X[2])
        finally:
            self.isMajorStep = True
            
        # Foutberekening
        A = R = 0.0001  
        err     = abs(Yrks - Ysim) / (A + R * abs(Yrks))
        max_err = numpy.max(err)
        
        if self.ERROR_LIMIT[0] <= max_err <= self.ERROR_LIMIT[1]:
            self.states = Yrks
            
        elif max_err > self.ERROR_LIMIT[1]:
            if self.timer.decreaseTimestep():
                self.states = Yt # Reset
                self.run() 
                
        else: 
            if self.timer.increaseTimestep():
                self.states = Yt # Reset
                self.run() 
        
        
        
        
        
         
        
        