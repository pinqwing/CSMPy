import lib.ast_comments as ast
import importlib.util
import inspect
from pathlib import Path
from importlib.machinery import SourceFileLoader


from csmp.precompiler.lister import Lister


class ModelLoader:
    
    def __init__(self, fileName):
        path        = Path(fileName)
        if not path.exists():
            raise FileNotFoundError(fileName)
        self.file   = path
        name        = path.stem.replace(".", "_")
        loader      = SourceFileLoader(name, str(fileName))
        spec        = importlib.util.spec_from_file_location(name, loader=loader)        
        self.module = importlib.util.module_from_spec(spec)
        # apply module's imports:
        try:    spec.loader.exec_module(self.module)
        except: pass
        
        self.folder = self.createOutputDirectory()
        self.source = path
        
    modelName   = property(lambda p: p.getFilepath("").name) 
    runnable    = property(lambda p: p.getFilepath(".py").absolute())  
            
            
    def createOutputDirectory(self):
        folder = (self.file.parent / self.file.stem).with_suffix(".out") 
        folder.mkdir(exist_ok = True)
        return folder
    
                    
    def getSyntaxTree(self):
        return ast.parse(self.getSource())
        

    def getGlobals(self, filtered = True):
        result = vars(self.module)
        return result if not filtered else dict([(k, v) for k, v in result.items() if not k.startswith("_")])


    def getSource(self):
        return inspect.getsource(self.module)
        
        
    def getFilepath(self, extension = None):
        if extension is None:
            return self.folder
        else: 
            p = self.folder / self.file.stem
            return p.with_suffix(extension)
        
        
    