import numpy


class Extrapolator:
    def __init__(self, client):
        self.client = client
        self.range  = [float(client.x[0]), float(client.x[-1])]
        self.values = client.y[0], client.y[-1]   


    def getMessage(self, x):
        return f"input ({x}) extrapolated beyond table range {self.range}"


    
    
class Clip(Extrapolator):
    
    def __call__(self, x):
        return self.values[0] if x < self.range[0] else self.values[1] 
    
    
    def getMessage(self, x):
        return f"input ({x}) clipped to table range {self.range}"


    
    
class LastSegment(Extrapolator):

    def __init__(self, client):
        super().__init__(client)
        rc          = numpy.take(numpy.diff(client.y)            # @UndefinedVariable
                                /numpy.diff(client.x), (0, -1))  # @UndefinedVariable
        xmin, xmax  = self.range
        self.left   = lambda x: client.y[ 0] + rc[0] * (x-xmin)
        self.right  = lambda x: client.y[-1] + rc[1] * (x-xmax)
        
        
    def __call__(self, x):
        return self.left(x) if x < self.range[0] else self.right(x) 
    

        
class Regression(Extrapolator):

    def __init__(self, client):
        super().__init__(client)
        a, b        = numpy.polyfit(client.x, client.y, deg=1)
        self.values = lambda x: a * x + b
        
        
    def __call__(self, x):
        return self.values(x)  
    

