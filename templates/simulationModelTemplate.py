from csmp.rts import CSMP_Model


class SimulationModel(CSMP_Model):
    
    def defineConstants(self):
        ' -/- '
        ":constants:"
        return locals()
    
    
    def defineParameters(self):
        ' -/- '
        ":parameters:"
        return locals()
    
    
    def setUp(self):        
        globals().update(self.defineConstants())
        globals().update(self.defineParameters())
        globals().update(self.initial())
        ':functions:'
        ':generators:'
        ':initStates:'
        ':memoryObjects:'
        ':systemParams:'
        
        
    def initial(self):
        """
        Initialization-block called before the loop is started.
        All variables created here will persist in the global scope,
        unless explicitly deleted.
        note: parameters and constants have been created above
              and may be used here.
        """
        ':incons:'
        ':initial:'
        return locals()
        
        
    def loop(self, TIME, DELT, KEEP = True):
        """
        Called each time step and also in between,
        if the integration method requires so.
        """
        ":common:"
        
        ":restoreValues:"
        
        ":dynamic:"
        
        ":update:"
        
        return locals()

        
    def final(self):
        """ 
        End condition has been met. 
        Final actions to take.
        """
        ":terminal:"

