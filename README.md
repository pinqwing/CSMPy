# CSMPy
a Python implemenation of the Continuous Simulation Modeling Program (CSMP)

CSMPy (-Py pronounced as in 'happy'!) aims to provide a simulation environment that supports CSMP-models with as little adaptation as possible. 

CSMP is FORTRAN based and FORTRAN is syntactically not compatible with Python. But as it turns out, much existing CSMP-code can with modest syntax changes be run by the Python interpreter. Since CSMP always has allowed for FORTRAN code blocks to mix with the model code, much depends on the style of the original modeler. However, coding in Python is easier and more forgiving than in FORTRAN, so generally it shouldn't be too hard to make the model fit for CSMPy, unless dependencies on libraries exist than do not have their analogues in Python.

# state of development
CSMPy is in it's early stages of development, all work concentrating on the precompiler. It is expected that simple models can be compiled and run soon.

# the future
The first goal is to be able to run models according to the original specifications. From start however, all Python language facilities and libraries are available for use in new model development. As six character uppercase identifiers are no longer en vogue, the first change the modeler will note is the freedom of identifier length and case. New functions may be defined at will and their calls are sorted like any CSMP-statement. The use of objects has not yet een considered.

Since CSMPy uses Abstract Syntax Trees rather than line parsing, it is expected that most if not all python statements as black boxes, without requiring NOSORT blocks or interrupting SORT blocks and splitting them in multiple independent blocks, as CSMP did. (As of today, this has not yet been well tested).

Plots will be graphic - I can't think of any reason the reimplement the text-based plots (except perhaps for testing backward compatibility). In due time a GUI seems the way forward.
