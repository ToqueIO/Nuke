try:
    # Doing an from import * is getting an error here due to QtCharts,  Explicitly importing
    # modules instead.  Updating The list as needed
    from PySide2 import QtGui, QtCore, QtWidgets, QtSvg
except ImportError:
    from PySide import QtCore
    from PySide import *

del globals()['QtGui']
del globals()['QtWidgets']
del globals()['QtCore']


__release__ = 'release'
__major__ = 1
__minor__ = 0
__bugfix__ = 3
__version__ = '{release} {major:02}.{minor:02}.{bugfix:02}'.format(release=__release__,
                                                                   major=__major__,
                                                                   minor=__minor__,
                                                                   bugfix=__bugfix__)


from . import QtGui
from . import QtCore
