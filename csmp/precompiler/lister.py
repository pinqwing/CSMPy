import copy, sys
from collections import defaultdict
from logging import ERROR, WARNING, INFO, _levelToName as levelName

from lib.singleton import Singleton
from csmp.errors import PrecompilerError


class Lister(metaclass = Singleton):
    FINAL   = -1
    INITIAL = -2

    @staticmethod        
    def withContextError(method):
        # @decorator to sent contextual information to Lister
        def wrapper(*args, **kwargs):
            try:
                method(*args, **kwargs)
            except Exception as e:        
                context      = method.__name__
                if context.startswith("_"): context = context[1:]
                Lister().addError(str(e), Lister.FINAL, context)
                raise
        return wrapper
        
        
    def __init__(self):
        self.messages   = {}
            
            
    def start(self):
        factory = lambda : defaultdict(list)
        self.messages = defaultdict(factory)

        
    def addMessage(self, level: int, message: str, sourceLine: int, originator: str = None):
        self.messages[sourceLine][level].append((message, originator))
    
    def addError(self, message: str, sourceLine: int, originator: str):
        self.addMessage(ERROR, message, sourceLine, originator)
        
    def addWarning(self, message: str, sourceLine: int, originator: str):
        self.addMessage(WARNING, message, sourceLine, originator)
        
    def addInfo(self, message: str, sourceLine: int, originator: str):
        self.addMessage(INFO, message, sourceLine, originator)
        
        
    def addSyntaxErrorError(self, error, message: str, sourceLine: int, originator: str):
        msg = PrecompilerError.rewriteSyntaxError(error, message)
        self.addError(msg, sourceLine, originator)
    
        
    def report(self, code, file = sys.stdout, reportAll = False, onlyMarkedLines = False):
        decoration = {ERROR: "**", WARNING: "!!", INFO: ">>"}
        
        messages = copy.copy(self.messages)
        
        def printRemarks(lineNr, lineTxt = None):
            n = 0
            all = messages.pop(lineNr, {})
            if lineTxt is not None and (all or not onlyMarkedLines):
                print("%04d" % (lineNr), lineTxt, file = file)
            for level in (ERROR, WARNING, INFO):
                messagesAtLevel = all.get(level, [])
                for msg in messagesAtLevel:
                    deco    = decoration.get(level, "??")
                    lvl     = levelName[level]
                    text    = msg[0]
                    sender  = "" if msg[1] is None else "(%s)" % msg[1]
                    for s in text if isinstance(text, list) else [text]:
                        print(f"{lvl} {deco} {s} {sender}", file = file)
                        sender = "" # do not repeat this
                    n += 1
            return (n > 0) # anything done
        
        
        code = code.split("\n")

        printRemarks(self.INITIAL)
        print("\n", file = file)
        
        for i, line in enumerate(code, start = 1):
            if printRemarks(i, line):
                print("", file = file)
        
        
        print("\n", file = file)
        printRemarks(self.FINAL)
        
        if reportAll: 
            # add messages from lines beyond those of code:
            for l in sorted(messages):
                printRemarks(l)
                    
                    
          
    def count(self):
        errors = warnings = 0
        for lineMsg in self.messages.values():
            errors      += len(lineMsg.get(ERROR,   []))
            warnings    += len(lineMsg.get(WARNING, []))
        
        return errors, warnings
    
        
                
if __name__ == '__main__':
                        
    l = Lister()
    l.start()        
    l.addWarning("started", Lister.INITIAL, "test")
    l.addError("error", 15, "test")
    l.addWarning("warning", 15, "test")
    l.addWarning("final warning", Lister.FINAL, None)
    
    # print(l.messages)
    s = sys.modules[__name__]
    import inspect
    l.report(inspect.getsource(s), onlyMarkedLines = True)
    print(l.count())