


class StateVariable:
    
    def __init__(self, name, initialValue):        
        self.name  = name
        self.value = initialValue
        self.rate  = 0.0
        self.temp  = None



class Integrator: 

    def __init__(self, model):
        self.model = model
        self.timer = model.timer
        
        
    def integrate(self, s): pass
    
    def initialize(self): pass
        
        
    def run(self):
        for s in self.model.stateVariables:
            self.integrate(s)
           
           
            

class Rect(Integrator):
    
    def integrate(self, s):
        s.value += s.rate * self.timer.delt

    

class Trapz(Integrator):

    class TempData:
        def __init__(self, previousRate = 0):
            self.previousRate = previousRate


    def initialize(self):
        self.model.loop(self.timer.time)
        for s in self.model.stateVariables:
            s.temp = self.TempData(s.rate)
            
            
    def integrate(self, s):
        rate     = (s.rate + s.temp.previousRate) / 2
        s.value += rate * self.timer.delt
        s.temp.previousRate = rate

    
# class RksFx(Integrator):
#
#     class TempData:
#         def __init__(self, previousRate = 0):
#             self.previousRate = previousRate
#
#
#     def initialize(self):
#         self.model.loop(self.timer.time)
#         for s in self.model.stateVariables:
#             s.temp = self.TempData(s.rate)
#
#
#     def integrate(self, s):
#         rate     = (s.rate + s.temp.previousRate) / 2
#         s.value += rate * self.timer.delt
#         s.temp.previousRate = rate

        