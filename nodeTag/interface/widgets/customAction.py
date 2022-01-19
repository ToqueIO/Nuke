import os.path

import nuke
from CommonQt import QtGui, QtCore


class CustomAction(QtGui.BaseWidget):

    globalInstance = None

    def __init__(self, searchWidget):
        super(CustomAction, self).__init__()

        self.highlighter = None
        self._userDir = None

        self.searchWidget = searchWidget
        self.initialized = False

        self.masterLayout = QtGui.QVBoxLayout()
        self.buttonLayout = QtGui.QHBoxLayout()

        self.splitter = QtGui.QSplitter()

        self.commandOutput = QtGui.QTextEdit()
        self.commandEntry = QtGui.CodeEditor(saveDir=self.userDir, saveCode=True, saveLog=True)
        self.runButton = QtGui.QPushButton('Run')
        self.runSelectedButton = QtGui.QPushButton('Run Selected')
        self.cancelButton = QtGui.QPushButton('Clear')

    @property
    def userDir(self):
        """
        Returns:
            str: Path to the current users .nuke folder
        """
        if self._userDir is None:
            userDir = None
            for path in nuke.pluginPath():
                if '.nuke' in path:
                    userDir = path
                    break

            if userDir:
                self._userDir = os.path.join(userDir, 'customAction')

        return self._userDir

    def initializeInterface(self):
        """
        Set up the interface for the widget
        """
        self.buttonLayout.addWidget(self.runButton)
        self.buttonLayout.addWidget(self.runSelectedButton)
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.addStretch()
        self.masterLayout.addLayout(self.buttonLayout)

        self.splitter.addWidget(self.commandOutput)
        self.splitter.addWidget(self.commandEntry)
        self.masterLayout.addWidget(self.splitter)

        self.highlighter = QtGui.syntaxPython.PythonHighlighter(self.commandEntry)

        self.setLayout(self.masterLayout)
        self.setWindowTitle('Node Tag Custom Action')

    def initializeDefaults(self):
        """
        Set the base defaults for the widget
        """
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.commandOutput.setReadOnly(True)
        self.commandEntry.defaultCode = ('\'\'\'\n'
                                         'Tag items can be referenced with the attribute items\n'
                                         'or selectedItems if you want to run the code on only\n'
                                         'the selected items in the search tab\n'
                                         'Each item has the following attributes\n\n'
                                         'name: Name of the tagItem/Node\n'
                                         'node: Instance of the nuke Node\n'
                                         'tags: Tags that are on the node/item\n\n'
                                         '\'\'\'\n\n'
                                         '# You can run the below example to print all item names\n'
                                         'print(\'All\')\n'
                                         'for item in items:\n'
                                         '    print(item.name)\n\n'
                                         '# You can run the below example to print selected item '
                                         'names\n'
                                         'print(\'Selected\')\n'
                                         'for item in selectedItems:\n'
                                         '    print(item.name)\n\n'
                                         '')
        self.commandEntry.setToolTip(
            self.commandEntry.defaultCode.split('#')[0].replace('\'\'\'', '').strip('\n'))

    def initializeSignals(self):
        """
        Initialize all signals for the widget
        """
        self.cancelButton.pressed.connect(self.commandOutput.clear)
        self.runButton.pressed.connect(self.runAction)
        self.runSelectedButton.pressed.connect(lambda: self.runAction(selected=True))
        self.commandEntry.clearOutputRequested.connect(self.commandOutput.clear)
        self.commandEntry.runCodeRequested.connect(lambda: self.runAction(selected=True))

    def runAction(self, selected=False):
        """
        Passed on the attributes for the items to the code editor and triggers runs the users code
        Args:
            selected (bool): True or False if the code is to be run on only the currently selected
                             items
        """
        globalAttrs = globals()
        globalAttrs['items'] = [item.tagItem for item in self.searchWidget.tagItemList.widgets]
        globalAttrs['selectedItems'] = [item.tagItem for item in
                                        self.searchWidget.tagItemList.selectedWidgets]

        output = self.commandEntry.runCode(selected=selected, globalAttrs=globalAttrs)
        self.commandOutput.insertPlainText(output)
        self.commandOutput.moveCursor(QtGui.QTextCursor.End)
