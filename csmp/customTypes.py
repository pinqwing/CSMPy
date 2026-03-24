from enum import Enum
from csmp.rts import integrator


class IntegrationMethod(Enum):
        
    ADAMS   = integrator.Adams2ndOrder
    CENTRL  = None
    MILNE   = None
    RECT    = integrator.Rect
    RKS     = integrator.RungeKuttaSimpson
    RKSFX   = integrator.RungeKutta4thOrder
    SIMP    = integrator.Simpson
    TRAPZ   = integrator.Trapz   
    
    
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
