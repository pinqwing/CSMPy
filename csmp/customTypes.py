from enum import Enum


class IntegrationMethod(Enum):
        
    ADAMS   = "Second-order Adams integration with fixed interval"
    CENTRL  = "A dummy routine that may be replaced by a user-supplied centralized " + \
              "integration subroutine, if desired"
    MILNE   = "Variable-step, fifth-order, predictor-corrector Milne integration method"
    RECT    = "Rectangular integration"
    RKS     = "Fourth-order Runge-Kutta with variable integration interval; " + \
              "Simpson's Rule used for error estimation"
    RKSFX   = "Fourth-order Runge-Kutta with fixed interval"
    SIMP    = "Simpson's Rule integration with fixed integration interval"
    TRAPZ   = "Trapezoidal integration"  
    
    
class VarType(Enum):
    NONE     =-1
    INTGRL   = 0
    PARAM    = 1
    INCON    = 2
    CONSTANT = 3
    FUNCTION = 4

    

# class Comparator (float):
#     @staticmethod 
#     def gt(a, b): return a > b
#
#     @staticmethod 
#     def ge(a, b): return a >= b
#
#     @staticmethod 
#     def lt(a, b): return a < b
#
#     @staticmethod 
#     def le(a, b): return a <= b
#
#     @staticmethod 
#     def eq(a, b): return a == b
#
#     @staticmethod 
#     def ne(a, b): return a != b
#
#
#     @classmethod    
#     def __class_getitem__(cls, operator):
#         result = getattr(cls, operator.lower(), False)
#         if result: return result
#         return   {'>':    cls.gt, '>=':   cls.ge,
#                   '<':    cls.lt, '<=':   cls.le,
#                   '==':   cls.eq, '!=':   cls.ne}[operator]
