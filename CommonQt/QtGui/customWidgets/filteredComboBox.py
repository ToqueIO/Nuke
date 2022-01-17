import re
import logging

try:
    from PySide2 import QtWidgets, QtGui, QtCore

    if hasattr(QtCore, 'QStringListModel'):
        QtGui.QStringListModel = QtCore.QStringListModel

except ImportError:
    from PySide import QtGui, QtCore
    QtWidgets = QtGui


class FilteredComboBox(QtWidgets.QComboBox):
    def __init__(self):
        super(FilteredComboBox, self).__init__()

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)

        self.filterModel = QtCore.QSortFilterProxyModel(self)
        self.filterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.filterModel.setSourceModel(self.model())

        self.completer = QtWidgets.QCompleter(self.filterModel, self)
        self.completer.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)
        self.completer.activated.connect(self.completerActivated)

        self.lineEdit().textEdited.connect(
            lambda text: self.filterModel.setFilterFixedString(str(text)))

    def completerActivated(self, text):
        """
        This ensures that we correctly set the index of the comboBox(self) when the user has
        entered text.  If the text has not been presented then this will do nothing.  If the given
        text can not be found then nothing will happen

        Args:
            text (str): This is the text from the completion
        """
        if text:
            index = self.findText(str(text))
            if index >= 0:
                self.setCurrentIndex(index)

    def setModel(self, model):
        """
        We override the setModel to ensure that the completer is properly linked to the newly
        updated model
        """
        super(FilteredComboBox, self).setModel(model)
        self.filterModel.setSourceModel(model)
        self.completer.setModel(self.filterModel)

    def setModelColumn(self, column):
        """
        This assures that all of the columns are updated for all models when the model of the
        comboBox(self) is updated1
        """
        self.completer.setCompletionColumn(column)
        self.filterModel.setFilterKeyColumn(column)
        super(FilteredComboBox, self).setModelColumn(column)
