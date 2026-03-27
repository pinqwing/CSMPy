import ast
import sys
from pathlib import Path

from lib.smallUtilities import flatten
from csmp.precompiler.lister import Lister
from csmp.precompiler.segment import SegmentLabel
from csmp.precompiler.statementBase import StatementCategory, StatementClass
from csmp.precompiler.template import TemplateBuilder
import itertools
from csmp.precompiler.nodeWraps import NodeWrap


class PrecompilerOutput:
    '''
    Helper class for saving output of the precompiler
    '''
    
    def __init__(self, options, model):
        self.options    = options
        self.model      = model
        self.path       = Path(model.folder)
    

    def _getFile(self, file):
        if not file:
            return sys.stdout
        
        if isinstance(file, str) or isinstance(file, Path):
            file = (self.path / Path(file).name) # force into output path
            print(f"writing file {file}")
            return file.open("w")
        
        return file
    
    
    @Lister.withContextError
    def writeListfile(self, file = "", summary = False):
        file = self._getFile(file)
        Lister().report(self.model.getSource(), file = file, onlyMarkedLines = summary)
        print("%8d error(s)\n%8d warning(s)" % Lister().count(), file = file)
        
        
    def _getConstantValues(self, constants):
        '''
        Evaluate the hard-defined values of constants, parameters and incons.
        :return: dict
        '''
        tmpSource = "def dummy(): ...\n" + "\n".join([s.toString() for s in constants])
        result    = {}
        exec(tmpSource, locals = result)
        return result 
            
        
    @Lister.withContextError
    def writeSummary(self, file = ""):
        file = self._getFile(file)
        modelFileName       = self.model.file
        errors, warnings    = Lister().count()
        completed           = "succesfully completed" if errors == 0 else "failed"
        stateVars           = ", ".join([v.name for v in sorted(self.model.states, key = lambda n: n.name)])
        
        print("\n\n", file = file)
        print(f"Parsing of {modelFileName} {completed} with {errors} error(s) and {warnings} warning(s).\n", file = file)
        print(f"{len(self.model.states)} state variables: {stateVars}\n", file = file)
        
        constants = (self.model.consts, self.model.params, self.model.incons)
        sizes     = [len(c) for c in constants]  
        consts = self._getConstantValues(flatten(constants))
        format = lambda coll: ([" %-8s = %-12s " % (k.name, consts.get(k.name, -99999)) for k in sorted(coll, key = lambda n: n.name)])
        items  = tuple([format(c) for c in constants])
        
        print("   %-22s "*3 % (f"CONST ({sizes[0]})", f"PARAM ({sizes[1]})", f"INCON ({sizes[2]})"), file = file)
        for values in itertools.zip_longest(*items, fillvalue = " "*25):
            print(*values, file = file)
            
        self.writeListfile(file, summary = True)
        print("\n\n", file = file)
                
            
    
    @Lister.withContextError
    def writeRunnable(self, file = ""):
        file = self._getFile(file)
    
        def common():
            variables = segments[SegmentLabel.INITIAL].getAssignments()
            s = "global %s" % ", ".join(variables) if variables else "# (nothing to do)" 
            node = ast.parse(s)
            return [node.body[0]] if node.body else []

        template    = Path(self.options.template)
        comment     = self.options.templateComment
        placeHolder = self.options.templatePlcHldr
        builder     = TemplateBuilder(template, segmentComment = comment, placeholders = placeHolder)
        
        segments = self.model.segments
        builder.replace(StatementCategory.common, common())
        builder.replace(StatementCategory.initial,    [w.node for w in segments.initial.getItems()],  False)
        builder.replace(StatementCategory.dynamic,    [w.node for w in segments.dynamic.getItems()],  False)
        builder.replace(StatementCategory.terminal,   [w.node for w in segments.terminal.getItems()], False)

        for cat in StatementCategory: # this loops through _all_ cats and destroys any remaining placeholders
            items       = self.model.statements[cat]
            transformed = flatten([item.transform(cat) for item in items])
            builder.replace(cat, transformed, True)

        builder.write(file)

        
    @Lister.withContextError
    def writeCurrentSource(self, file = ""):
        file = self._getFile(file)

        def output(label, items):
            print("\n"+'-'*10, label, '-'*20, file=file)
            for item in items:
                print(item, file=file)
            
        for lbl in [StatementCategory.functions,
                    StatementCategory.generators,
                    StatementCategory.initStates,
                    StatementCategory.constants,
                    StatementCategory.parameters,
                    StatementCategory.systemParams,
                    StatementCategory.incons, 
                    StatementCategory.initial, 
                    StatementCategory.restoreValues,
                    StatementCategory.dynamic,
                    StatementCategory.update,
                    StatementCategory.terminal]:
            if   lbl == StatementCategory.initial:
                items = self.model.segments.initial.getItems()
            elif lbl == StatementCategory.dynamic:
                items = self.model.segments.dynamic.getItems()
            elif lbl == StatementCategory.terminal:
                items = self.model.segments.terminal.getItems()
            else:
                items = [NodeWrap(w.transform(lbl)) for w in self.model.statements[lbl]]  
            output(lbl.value, items)        
        

        
        