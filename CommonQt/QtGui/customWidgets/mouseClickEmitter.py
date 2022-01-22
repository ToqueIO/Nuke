try:
    from PySide2 import QtWidgets, QtGui, QtCore

    if hasattr(QtCore, 'QStringListModel'):
        QtGui.QStringListModel = QtCore.QStringListModel

except ImportError:
    from PySide import QtGui, QtCore
    QtWidgets = QtGui


class MouseEventFilter(QtCore.QObject):

    mouseReleased = QtCore.Signal()
    mousePressed = QtCore.Signal()
    mouseDoubleClick = QtCore.Signal()
    _globalInstances = dict()

    def eventFilter(self, obj, event):
        """
        Override handler used to emit a signal anytime there is a mouse button release.
        """
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            self.mouseReleased.emit()
        elif event.type() == QtCore.QEvent.MouseButtonPress:
            self.mousePressed.emit()
        elif event.type() == QtCore.QEvent.MouseButtonDblClick:
            self.mouseDoubleClick.emit()

        return super(MouseEventFilter, self).eventFilter(obj, event)

    @classmethod
    def globalInstance(cls):

        app = QtWidgets.QApplication.instance()
        appName = app.applicationName()

        instance = cls._globalInstances.get(appName)
        if not instance:
            instance = cls()
            app.installEventFilter(instance)
            cls._globalInstances[appName] = instance

        return instance
