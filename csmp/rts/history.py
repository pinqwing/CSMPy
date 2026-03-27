from csmp import errors




class MemoryFunction:
    
    def __init__(self, initial = 0):
        self.current        = initial  
        self.changed        = None
        
        
    def getCurrentValue(self):
        return self.current
    
    
    def setCurrentValue(self, value):
        self.changed = value
        return self.current
    
    
    def commit(self):
        self.current = self.changed

            
            
class HistoryFunction(MemoryFunction):
    
    def __init__(self, wrappedFunction, initial = [0]):
        raise errors.NotYetImplementedError("HISTORY")
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
                    
             
