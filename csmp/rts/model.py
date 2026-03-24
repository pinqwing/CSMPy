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
    
    def __init__(self, varNames = [], format = "{:>18.4f}"):
        self.formats  = ["{:>8.4f}"] + [format] * len(varNames) 
        self.varNames = ["TIME"   ] + list(varNames)
    
    
    def printHeader(self):
        for name, fmt  in zip(self.varNames, self.formats):
            print(fmt.replace("f}", "}").format(name), end = "")
        print()
            
        
    def print(self, time, values):
        for name, fmt  in zip(self.varNames, self.formats):
            x = values.get(name, -99999)
            print(fmt.format(x), end = "")
        print()
            
    
            

