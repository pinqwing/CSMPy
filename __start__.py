from csmp.precompiler import Precompiler
from lib.options import Options
from lib.settings import globalConfig


class CsmpOptions(Options):
    
    def __init__(self):
        super().__init__("")
        self.template = globalConfig.get("precompiler", "template")
        self.listFile = self._getFileOptions("precompiler", "listFile")
        self.summary  = self._getFileOptions("precompiler", "summary")
        self.sorted   = self._getFileOptions("precompiler", "sorted")
        self.unsorted = self._getFileOptions("precompiler", "unsorted")
        self.debugSeg = self._getFileOptions("precompiler", "debugSeg")
        
            

    def _getFileOptions(self, section, key):
        setting = globalConfig.get(section, key, "").replace(", ", ",").split(',')
        return dict(scrn = "show" in setting,
                    file = "save" in setting)
        
        
        
if __name__ == '__main__':
    from csmp.precompiler.nodeWraps import NodeWrap
            
    globalConfig.setFilename("./", "csmp.config")
    options = CsmpOptions()
    
    mdl = Precompiler(options)
    mdl.compile("./models/test.csm.py")
    mdl.writeSummary()
    # print("\n", '-'*80, '\n')
    # mdl.writeListFile()
    print("\n", '-'*80, '\n')
    mdl.writeTemplate()
    # mdl.debugSegmentation()
    # for o in sorted(NodeWrap.objects, key=lambda o: str(o)):
    #     print(o)    