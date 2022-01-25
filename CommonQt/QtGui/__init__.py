try:
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except ImportError:
    from PySide.QtGui import *

from .customWidgets.multiCompleteLine import MultiCompleteLine
from .customWidgets.filteredComboBox import FilteredComboBox
from .customWidgets.baseWidget import BaseWidget
from .customWidgets.customListWidget import CustomListWidget
from .customWidgets.codeEditor import CodeEditor
from .customWidgets.mouseClickEmitter import MouseEventFilter

from .highlighters import syntaxPython
