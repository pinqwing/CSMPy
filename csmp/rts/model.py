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
            print("{:>12.8f}".format(x), end = "")
            # print("%12g" % x, end = "")
        
        print("{:>8.4E}".format(time), end = "")
        # print("%8.4E" % time, end = "")
        for name in self.varNames:
            printVar(name)
        print()
            
    
            

