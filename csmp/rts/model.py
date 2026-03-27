import ast
import inspect
import re, sys
from abc import ABC, abstractmethod
from itertools import zip_longest



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
    
    def __init__(self, varNames = [], format = (0, 0)):
        self.fldWidth = format if any(format) else (12, 4)
        fmt           = "{:>%d.%df}" % self.fldWidth
        self.fltFmts  = ["{:>8.4f}"] + [fmt] * len(varNames) 
        self.strFmts  = [re.sub(r"([0-9]*)\.([0-9]*)f", r"\1s", fmt) for fmt in self.fltFmts]
        self.varNames = ["TIME"   ] + list(varNames)
        self.aliases  = {}
        
            
    def setAliases(self, aliasNames = {}):
        self.aliases = aliasNames
    
    
    def printHeader(self):
        for name, fmt  in zip(self.varNames, self.strFmts):
            name = self.aliases.get(name, name)
            print(fmt.format(name), end = "")
        print()
            
        
    def print(self, time, values):
        for name, ffmt, sfmt  in zip(self.varNames, self.fltFmts, self.strFmts):
            x = values.get(name, "n/a")
            try:
                print(ffmt.format(x), end = "")
            except:
                print(sfmt.format(str(x)))
        print()
            
    
            

