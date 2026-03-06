import ast
import importlib.util
import inspect
from pathlib import Path

from csmp.precompiler.lister import Lister


class ModelLoader:
    
    def __init__(self, fileName):
        path        = Path(fileName)
        if not path.exists():
            raise FileNotFoundError(fileName)
        self.file   = path
        name        = path.stem.replace(".", "_")
        spec        = importlib.util.spec_from_file_location(name, path)
        self.module = importlib.util.module_from_spec(spec)
        try:    spec.loader.exec_module(self.module)
        except: pass
            
                    
    def getSyntaxTree(self):
        return ast.parse(self.getSource())
        

    def getGlobals(self, filtered = True):
        result = vars(self.module)
        return result if not filtered else dict([(k, v) for k, v in result.items() if not k.startswith("_")])


    def getSource(self):
        return inspect.getsource(self.module)
        
        
    def saveList(self, file = None, summary = False):
        
        def write(f):
            Lister().report(self.getSource(), file = f, onlyMarkedLines = summary)
            print("%8d error(s)\n%8d warning(s)" % Lister().count(), file = f)
            
        if file is None:
            path = self.file.with_suffix(".lst")
            with path.open("w") as f:
                write(f)
        else:
            write(file)
        



