import lib.ast_comments as ast
from lib.ast_tools import dump, printNode
from lib.smallUtilities import flatten
from csmp import functions
from csmp.errors import PrecompilerError
from csmp.precompiler import csmpStatements


class Sorter:
    
    def __init__(self):
        self.symbols = set(csmpStatements.symbols()) | set(functions.symbols())
        self.addSymbol("self")
        for name in vars(csmpStatements):
            if name == name.upper() and not name.startswith("_"):
                self.addSymbol(name)
        for name in vars(functions):
            if name == name.upper() and not name.startswith("_"):
                self.addSymbol(name)
        
    
    def addSymbol(self, name):
        self.symbols.add(name)
        
    def addSymbols(self, names):
        for name in names:
            self.addSymbol(name)
        
    
    def useImports(self, imports):
        blanc = ast.parse("print()") # placeholder
        
        def importNode(imp):
            dummy = blanc.body.pop(0)
            
            # note: the next line changes imp.node.(end_)lineno,
            #       but not node.lines/getStart()/getEnd() 
            blanc.body.append(ast.copy_location(imp.node, dummy))
    
            obj = compile(blanc, filename="<ast>", mode="exec")
            globalSymbols = {}
            localSymbols  = {}
            try:
                exec(obj, globalSymbols, localSymbols)
            except ModuleNotFoundError as e:
                imp.addRemark(e.msg)
                
            for name in globalSymbols:
                self.addSymbol(name)
                
            for name in localSymbols:
                self.addSymbol(name)
            
        for wrap in imports: # one by one in order to use line numbers
            importNode(wrap)
            
        
    def getDependencies(self, wraps):
        result = []
        for wrapper in wraps:
            defined = set()
            needed  = set()
            for node in ast.walk(wrapper.node):
                if isinstance(node, ast.Name):
                    if isinstance(node.ctx, ast.Store):
                        defined.add(node.id)
                    else:
                        needed.add(node.id)
            result.append((defined, needed, wrapper))
        return result    

            
    def sort(self, wraps, addToSymbols = True, blockID = "sorter"):
        resolved = []
        unSorted = []
        items    = self.getDependencies(wraps)
        count    = len(items) * len(items)
        known    = set() | self.symbols # a copy as working set
        
        while items and count:
            count -=1
            line   = items.pop(0)
            names, dependencies, wrap = line
            if all([v in known for v in dependencies]):
                known |= names
                resolved.append(wrap)
            else:
                items.append(line)
                
        for names, dependencies, wrap in items:
            names = [d for d in dependencies if not d in known]
            unSorted.append(wrap)
            wrap.addRemark("unresolved name(s): %s" % names, originator = blockID)
            
        # return resolved, unSorted
        wraps.clear()
        wraps.extend(resolved)
        wraps.extend(unSorted)
        
        if addToSymbols:
            self.symbols = known
        
        
        
        
    
    
    
    
    
    
        