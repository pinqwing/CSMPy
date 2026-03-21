from csmp import errors


class MemoryFunction:
    
    def __init__(self, wrappedFunction, initial = [0]):
        if not hasattr(initial, "__iter__"):
            raise errors.ModelError(f"initial arguments of a {type(self).__name__} must be a list or a tuple")
        if len(initial) == 0:
            raise errors.ModelError(f"a {type(self).__name__} must be supplied with at least one initial value")
        self.wrappedFunction = wrappedFunction
        self.previous        = initial[0] if len(initial) == 1 else tuple(initial)  
        self.latest          = []
        
        
    def __call__(self, *args, **kwargs):
        self.latest = self.wrappedFunction(*args, **kwargs)
        return self.previous
    
    
    def stampValid(self):
        if self.latest != []:
            self.previous = self.latest
            
            
class HistoryFunction(MemoryFunction):
    
    def __init__(self, wrappedFunction, initial = [0]):
        super().__init__(wrappedFunction, initial)
        self.isTuple = isinstance(self.previous, tuple)
    
    
    def __call__(self, *args, **kwargs):
        if self.isTuple: 
            self.latest = self.wrappedFunction(*self.previous, *args, **kwargs)
        else:
            self.latest = self.wrappedFunction(self.previous, *args, **kwargs)
        return self.previous
            


            
if __name__ == '__main__':
                
    mfunc = MemoryFunction(lambda p:  (p, p * p))
    hfunc = HistoryFunction(lambda h, p: (h + p))
    
    for i in range(10):
        print(i, mfunc(i), hfunc(i))
        mfunc.stampValid()
        hfunc.stampValid()
                    
             
