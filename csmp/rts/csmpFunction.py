import numpy 
from csmp import errors
import re
from csmp.rts.linearExtrapolators import Clip, LastSegment, Regression
from csmp.rts.linearInterpolators import Lagrange



class Csmp_Method:
    
    def __init__(self):
        self.name   = re.sub("Csmp_(.+)", lambda m: m.group(1).upper(), type(self).__name__)
        
        
    def runtimeError(self, message, origin = None):
        sender = origin if origin is not None else self.name
        message = f"{sender}: {message}"
        raise errors.SimulationError(message)
    
    
    def compiletimeError(self, message):
        message = f"{self.name}: {message}"
        raise errors.PrecompilerError(message)


    def warn(self, message):
        print("WARNING:", message)



class Csmp_Function(Csmp_Method):
    '''
    combined FUNCTION and AFGEN function
    '''
    MINIMUM_COUNT = 2 # minimumNrOfElements

    def __init__(self, *args, x=[], y=[]):
        '''creates FUNCTION object.
        args:
            x, y: independent and dependent variable values supplied as list, tuple or array.
                Both must be of equal size and have at least 2 elements.
                Alternatively x-y pairs may be given as tuples or alternating values. SO, valid options
                are Csmp_Function(x1, y1, x2, y2, ... xn, yn), Csmp_Function((x1, y1), (x2, y2), ..., (xn, yn)),
                Csmp_Function(x = (x1, x2, ... xn), y=(y1, y2, ... , yn)
                Note: the pairs are sorted and need not be in order
        example:
            f = Csmp_Function(x=(1, 2, 3, 4, 5), y=[1.1, 2.0, 3.3, 4.0, 5.5], warnings = 2)
            y = f(1.5)
        '''
        super().__init__()
        x, y                = self._handleDatapairs(*args, x=x, y=y)
        self.x              = numpy.array(x, dtype = numpy.float64)  # @UndefinedVariable
        self.y              = numpy.array(y, dtype = numpy.float64)  # @UndefinedVariable
        self._sortAndCheckData(self.MINIMUM_COUNT)
        

    def _handleDatapairs(self, *args, x=[], y=[]):
        # sort out all the forms taht __init__'s xy-parameters can take
        isIterable = lambda v: hasattr(v, "__iter__")
        isDataPair = lambda v: isIterable(v) and (len(v) == 2)

        if x or y: # x and y provided
            if not (isIterable(x) and isIterable(y)):
                self.compiletimeError("x and y arguments should be lists or tuples")
            if args:
                self.compiletimeError("when x and y arguments are provided, other data cannot be supplied too")
            if len(x) != len(y):
                self.compiletimeError("x and y arguments must have the same length")

        else:
            if len(args) == 1 and isIterable(args[0]):          # call([...])
                x, y = self._handleDatapairs(*tuple(args[0]))

            elif all([isDataPair(a) for a in args]):            # call((x, y), (x, y), ...)
                x, y = zip(*args)

            elif len(args) % 2 != 0:                            # call(x, y, x, y, ..., x)
                self.compiletimeError("an even number of x-y arguments should be supplied")

            else:                                               # call(x, y, x, y, ..., x, y)
                x = args[::2]
                y = args[1::2]
        return x, y


    def _sortAndCheckData(self, minimumNrOfElements):
        # sort data points and verify x doesn't contain doubles
        index   = self.x.argsort()
        self.x  = self.x[index]
        self.y  = self.y[index]
        if numpy.any(self.x[1:] <= self.x[:-1]):
            self.compiletimeError("x-arguments must be strictly ascending")

        if len(self.x) < minimumNrOfElements:
            self.compiletimeError("a minimum of %d data points is required" % minimumNrOfElements)


class Csmp_AfGen(Csmp_Method):

    def __init__(self, function: Csmp_Function, warnings: int = -1, extrapolation = Clip):
        ''' creates AFGEN, an arbitrary (=linear) function generator
        
        args:
            function: the datasource function
            warnings: number of warnings to be issued in case x exceeds the x-interval
                end is extrapolated. A value < 0 will suppress all warnings.
            extrapolation: Extrapolator class. Available are Clip (nearest terminal value, classic, default);
                LastSegment (extrapolates the last (or first) segment of the function); Regression
                (extrapolates the trend line of the functino. NB: discontinuities may arise at the domain boundary)
        '''
        super().__init__()
        self.function       = function
        self.x              = self.function.x
        self.y              = self.function.y
        self.warnings       = warnings
        self.extrapolator   = extrapolation(self.function)
        
        
    def warn(self, message):
        if self.warnings > 0:
            self.warnings -= 1
            finalMessage = ". No more warnings will be issued for this function." if self.warnings == 0 else ""
            super().warn(message + finalMessage)
        

    def __call__(self, x):
        return self.getValue(x)
    
    
    def getValue(self, x):
        try:
            if not (self.x[0] <= x <= self.x[-1]):
                self.warn(self.extrapolator.getMessage(x))
                return self.extrapolator(x)
            return numpy.interp(x, self.x, self.y)
        except Exception as e:
            self.runtimeError(str(e), "AFGEN")



class Csmp_NlfGen(Csmp_AfGen):
    '''
    NLFGEN function
    '''
    MINIMUM_COUNT = 3 # minimumNrOfElements
            
    def __init__(self, function: Csmp_Function, warnings: int = -1, extrapolation = Clip, algoritm = Lagrange):
        ''' creates AFGEN, an arbitrary (=linear) function generator
        
        args:
            function: the datasource function
            warnings: number of warnings to be issued in case x exceeds the x-interval
                end is extrapolated. A value < 0 will suppress all warnings.
            extrapolation: Extrapolator class. Available are Clip (nearest terminal value, classic, default);
                LastSegment (extrapolates the last (or first) segment of the function); Regression
                (extrapolates the trend line of the functino. NB: discontinuities may arise at the domain boundary)
        '''
        super().__init__(function, warnings, extrapolation)
        # algoritm --> strategy pattern
        self.algoritm = algoritm(self)


    def __call__(self, x):
        return self.getValue(x)
    
    
    def getValue(self, x):
        try:
            if not (self.x[0] <= x <= self.x[-1]):
                self.warn(self.extrapolator.getMessage(x))
                return self.extrapolator(x)
            return self.algoritm(x)
        except Exception as e:
            self.runtimeError(str(e), "NLFGEN")
            
            
            
            
if __name__ == '__main__':
    from datetime import datetime    
    xy = (0,1), (1,1), (2,0), (3,0)        
    fn = Csmp_Function(xy)
    f  = Csmp_AfGen(fn, warnings = 2, extrapolation = Clip)
    g  = Csmp_NlfGen(fn, warnings = 2, extrapolation = Clip)
    for i in numpy.arange(-5, 6, 0.25):
        print("%5.2f: %10.4f .. %10.4f" % (i, f(i), g(i)))
