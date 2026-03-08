import ast
from enum import Enum

from ..errors import SegmentationError
from .nodeWraps import NodeWrap


class SegmentLabel(Enum):
    SORT    =-2, True
    NOSORT  =-1, False
    INITIAL = 0, True
    DYNAMIC = 1, True
    TERMINAL= 2, False

    def index(self):
        return self.value[0]
    
    def sorted(self):
        return self.value[1]
        
    def isSegment(self):
        return self.value[0] >= 0
    
    def isSection(self):
        return not self.isSegment()
    
    @classmethod
    def byNumber(cls, index):
        for lbl in self:
            if lbl.index() == index:
                return lbl
        raise IndexError(index)
    
    
    

class Section:
    
    def __init__(self, label = SegmentLabel.SORT, startsAt = 0, default = False):
        self.label      = label
        self.lines      = [startsAt] * 2
        self.items      = []
        self.default    = default # TODO obsolete?


    def __repr__(self):
        return "%s-section%s (line %d; %d item(s))" % (self.label.name, '*' if self.default else '', 
                                                       self.start, len(self.items))
    
    def getStart(self): return self.lines[0]
    
    def setStart(self, startLine):
        self.lines[0] = startLine
        self.lines[1] = max(self.lines)
        
    def getEnd(self):   return self.lines[1]
    
    def setEnd(self, endLine):
        self.lines[1] = endLine
        self.lines[0] = min(self.lines)

    start   = property(getStart, setStart)
    end     = property(getEnd,   setEnd)
    sorted  = property(lambda s: s.label.value[-1])
        
        
    def append(self, item):
        if not isinstance(item, NodeWrap):
            raise SegmentationError("invalid sub-item '%s'" % (item))
        self.items.append(item)


    def statements(self):
        return [w.statement for w in self.items]
    
    
    def contains(self, lineNumber):
        return self.lines[0] <= lineNumber <= self.lines[1]
    
    
    def sort(self, sorter):
        sorter.sort(self.items)
        
    
    def getDependencies(self, wraps):
        result = []
        for branch in wraps:
            defined = set()
            needed  = set()
            for node in ast.walk(branch.node):
                if isinstance(node, ast.Name):
                    if isinstance(node.ctx, ast.Store):
                        defined.add(node.id)
                    else:
                        needed.add(node.id)
            result.append((defined, needed, branch))
        return result    
    
    
    def getAssignments(self):
        deps = [d[0] for d in self.getDependencies(self.items)]
        if deps:
            return set.union(*deps)
        return set()
    
        
        

class ModelSegment(Section):
    UNSELECT = 0
    IMPLICIT = 1
    EXPLICIT = 2
    
    def __init__(self, label: SegmentLabel, startsAt = 0):
        if not label.isSegment():
            raise SegmentationError("%s is not a valid precompiler segment (line %d)" % (label.name, startsAt))
        super().__init__(label, startsAt)
        self.currentSection = self.appendSection(Section(SegmentLabel.SORT if self.sorted else SegmentLabel.NOSORT, default = True))
        self.selected       = self.UNSELECT
        
    sections = property(lambda s: s.items)


    def setStart(self, startLine):
        super().setStart(startLine)
        self.sections[0].start = startLine
        
        
    def setEnd(self, endLine):
        super().setEnd(endLine)
        self.sections[-1].end = endLine
        
    
    def select(self, reason):
        if self.selected and reason:
            if self.selected == self.EXPLICIT:
                raise SegmentationError("multiple definitions of the %s-segment" % self.label.name)
            else:
                raise SegmentationError("%s-segment label following implicit selection" % self.label.name)
        self.selected = reason
    

    def addSection(self, label: SegmentLabel, node: ast.Expr):
        line = node.lineno
        if label != self.currentSection.label:
            self.currentSection.end = line -1    
            self.currentSection = self.appendSection(Section(label, line))
        self.currentSection.end = max(line, self.currentSection.end)    
        
                
    def appendSection(self, item):
        if not item.label.isSection():
            raise SegmentationError("invalid sub-item '%s'" % (item))
        self.items.append(item)
        return item
    

    def appendStatement(self, statement):
        line = statement.getLineNumber()
        for section in self.sections:
            if section.end >= line:
                section.append(statement)
                return
        raise Exception("statement could not be assigned to any section of %s (line %d)" % (self.label.name, line))
 
    
    def structureSections(self):
        self.sections[0].start = self.start
        self.sections[-1].end  = self.end
        
        for i, s in enumerate(self.sections):
            s.start    = max(s.start, self.start)
            s.end  = min(s.end, self.end)
            if i > 0:
                self[i-1].end  = min(self[i-1].end, self[i].start -1)
    
    
    def getAssignments(self):
        result = set()
        for s in self.sections:
            result |= s.getAssignments()
        return sorted(set(result))
    
        
    def statements(self):
        result = []
        for s in self.sections:
            result += s.statements()
        return result
    
    
    def sort(self, sorter):
        for s in self.sections:
            if s.sorted:
                s.sort(sorter)
        
        
    def debug(self):
        print(self)
        print("%d - %d" % tuple(self.lines))
        
        for s in self.sections:
            print("    ", s)
            print("    ", "%d - %d" % tuple(s.lines))
            for st in s.items:
                print(" "*8, st)
        print()
                
                
                
                
class ModelSegments:
    
    def __init__(self, source):
        self.segments = [ ModelSegment(lbl) for lbl in SegmentLabel if lbl.isSegment()]
        self.dynamic.start = source.body[0].lineno
        self.dynamic.end   = source.body[-1].end_lineno
        
        currentSegment = self.dynamic # default, still may be changed until 1st assignment
        
        for node in source.body:
            line = node.lineno
            try:
                if (isinstance(node, ast.Assign) and not currentSegment.selected):
                    currentSegment.select(ModelSegment.IMPLICIT)
                
                if (isinstance(node, ast.Expr) and 
                    isinstance(node.value, ast.Constant) and 
                    node.value.value in dir(SegmentLabel)):
                 
                    lbl  = SegmentLabel[node.value.value]
                    
                    if lbl.isSegment():
                        # check segment order and multiple occurences:
                        valid = (lbl.index() >= currentSegment.label.index()) or not currentSegment.selected
                        if not valid:
                            raise SegmentationError("%s-segment out of sequence" % (lbl.name))
                        
                        anchor  = 0
                        if lbl != currentSegment.label:
                            anchor              = currentSegment.end  
                            currentSegment.end  = line - 1
                        
                        currentSegment          = self[lbl]
                        currentSegment.start    = line
                        currentSegment.end      = max(currentSegment.end, anchor)
                        currentSegment.select(ModelSegment.EXPLICIT)
                    else:
                        currentSegment.addSection(lbl, node)
            except SegmentationError as e:
                e.setLine(line)
                raise
            
        for s in self.segments:    
            s.structureSections()
            
        
    initial  = property(lambda ms: ms[0])
    dynamic  = property(lambda ms: ms[1])
    terminal = property(lambda ms: ms[2])
        
        
    def items(self):
        return [(s.label, s) for s in self.segments]
    
    def values(self):
        return [s for s in self.segments]
    
    def __iter__(self):
        return iter(self.segments)
    
    def __getitem__(self, n):
        if isinstance(n, int):
            return self.segments[n]
        
        if isinstance(n, SegmentLabel):
            return self.__getitem__(n.index())
        
        if isinstance(n, str):
            lbl = SegmentLabel[n]
            return self.__getitem__(lbl.index())


    def debug(self):            
        for s in self.segments:
            s.debug()
            
         
