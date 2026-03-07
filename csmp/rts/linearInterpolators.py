import numpy


class Lagrange:
    '''
    3-point quadratic Lagrange interpolation like presumably was used in CSMP's
    original NLFGEN
    '''
    
    def __init__(self, client):
        self.client = client
        x = client.x
        y = client.y
        
        # calculations that can be made in advance to speed up runtime calls:
        factors = numpy.zeros_like((x, x, x), shape = (len(x), 3))
        for i in range(len(x) - 2):
            x1, x2, x3 = x[i:i + 3]
            dx12 = x1 - x2
            dx13 = x1 - x3
            dx21 = -dx12
            dx23 = x2 - x3
            dx31 = -dx13
            dx32 = -dx23
        
            y1, y2, y3 = y[i:i + 3]
            f1 = y1 / (dx12 * dx13)
            f2 = y2 / (dx21 * dx23)
            f3 = y3 / (dx31 * dx32)
            factors[i] = f1, f2, f3
        self.factors = factors
        
        
    def __call__(self, x):
        xp = x - self.client.x
        idx = numpy.absolute(xp).argmin()
        idx = max(0, min(len(xp) - 3, idx))
        x1  = xp[idx    ]
        x2  = xp[idx + 1]
        x3  = xp[idx + 2]

        f = self.factors[idx]
        
        return f[0] * x2 * x3 \
             + f[1] * x1 * x3 \
             + f[2] * x1 * x2 


         

