


class Singleton(type):
    """
    Singleton metaclass. Usage:
    
    > class C(object, metaclass = Singleton):
                     -------------
            ...
            
    Subclasses are NOT pooled with superclass by default.
    To change this, add a __group__ attribute to the superclass
    (see examples below)
    """
    
    instances = {}

    def __tag__(cls):  # @NoSelf
        return getattr(cls, "__group__", cls)

    
    def __call__(cls, *args, **kwargs):  # @NoSelf
        tag = cls.__tag__()
        
        if tag not in cls.instances:
            cls.instances[tag] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instances[tag]

    
    def exists(cls):  # @NoSelf
        tag = cls.__tag__()
        return tag in cls.instances


    
if __name__ == '__main__':
            
    class Test(metaclass = Singleton):
        __group__ = "testers" # inherited by test2!!
        ...
        
    class Test2(Test):
        pass
        
    print(Test.exists(), Test2.exists(), Singleton.instances)
    print(Test2())
    print(Test.exists(), Test2.exists(), Singleton.instances)
    print(Test())
    print(Test.exists(), Test2.exists(), Singleton.instances)
