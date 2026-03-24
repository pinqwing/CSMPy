from csmp import CSMPy



        
        
if __name__ == '__main__':
    import sys
    
    csmp = CSMPy()        
    csmp.compile("./models/test.csm.py")
    if csmp.compiled:
        csmp.run()
        
    