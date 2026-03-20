import lib.ast_comments as ast
from csmp.precompiler import lister



class NodeWrap:
    ''' wrapper-object to make an ast-statement easier to handle.
    
    This used to be the base class of a whole family of wraps for statement nodes
    fulfilling a specific role. But Keywords now offers a cleaner approach to the 
    same purpose.    
    '''
    
    objects = []
    
    remarkCallback = lambda *args, **kwargs: None # one assignment to rule all
    
    def __init__(self, node: ast.AST, **kwargs):
        self.node    = node
        self.lines   = [node.lineno] 
        if node.end_lineno > node.lineno:
            self.lines.append(node.end_lineno)
            
        for n, v in kwargs.items():
            setattr(self, n, v) 
         
        self.objects.append(self)
        
    
    def getStatement(self):
        return self.node
    
    statement = property(lambda w: w.getStatement())    
    
    
    def getSource(self): # DONE: renamed from source()
        return ast.unparse(self.node)
    
    def getLineNumber(self):
        return self.getStart()
    
    def getStart(self):
        return self.lines[0]
    
    def getEnd(self):
        return self.lines[-1]
    
    
    def addRemark(self, msg: str, errorLvl = lister.ERROR, originator = None):
        lister.Lister().addMessage(errorLvl, msg, self.getEnd(), originator)
    
    
    def __repr__(self):
        return "%04d:%04d %s" % (self.getStart(), self.getEnd(), self.getSource())


    def sync(self, peer):
        if hasattr(peer, "__iter__"):
            return [self.sync(p) for p in peer]
        else:
            node = peer.node if isinstance(peer, NodeWrap) else peer
            ast.copy_location(node, self.node)
            return peer
    
