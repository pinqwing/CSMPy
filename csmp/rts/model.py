import ast
import inspect
import sys
from abc import ABC, abstractmethod
from itertools import zip_longest

from csmp.rts.csmpFunction import Csmp_Function, Csmp_AfGen, Csmp_NlfGen


# class EndCondition: elegant, but too simple
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
    '''
    note: in csmp the output was generated only after the run. That way
          too many columns could be passed to subsequent print blocks.
    '''
    
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
    


    
