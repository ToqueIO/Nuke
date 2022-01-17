try:
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except ImportError:
    from PySide.QtGui import *

from .customWidgets.multiCompleteLine import MultiCompleteLine
from .customWidgets.filteredComboBox import FilteredComboBox
from .customWidgets.baseWidget import BaseWidget
from .customWidgets.labeledWidget import LabeledWidget
from .customWidgets.customListWidget import CustomListWidget
from .customWidgets.customMessage import CustomMessage
from .customWidgets.codeEditor import CodeEditor

from .highlighters import syntaxPython
