import json
import os
import nukescripts
import nuke
import common.utilities
import searchReplace.logic
from CommonQt import QtGui, QtCore


SEARCH_REPLACE_PANEL = None


class SearchReplacePane(QtGui.BaseWidget):

    selectedNodes = 'Selected Nodes'
    allNodes = 'All Nodes'

    _globalInstance = None

    def __init__(self):
        super(SearchReplacePane, self).__init__()

        self.masterLayout = QtGui.QVBoxLayout()
        self.splitter = QtGui.QSplitter(QtCore.Qt.Vertical)

        self.upperWidget = QtGui.QWidget()
        self.upperLayout = QtGui.QVBoxLayout()
        self.searchOptionsLayout = QtGui.QHBoxLayout()

        self.selectionModeDrop = QtGui.FilteredComboBox()
        self.useRegexCheck = QtGui.QCheckBox('Use Regex')
        self.caseSensitiveCheck = QtGui.QCheckBox('Case Sensitive')
        self.searchLine = QtGui.QLineEdit()
        self.replaceLine = QtGui.QLineEdit()
        self.executeButton = QtGui.QPushButton('Execute')
        self.infoBox = QtGui.QTextEdit()

        self.searchCompleterModel = QtCore.QStringListModel()
        self.searchCompleter = QtGui.QCompleter(self.searchCompleterModel)

        self.replaceCompleterModel = QtCore.QStringListModel()
        self.replaceCompleter = QtGui.QCompleter(self.replaceCompleterModel)

        self.versionLayout = QtGui.QHBoxLayout()
        self.versionLabel = QtGui.QLabel()

        self.mouseFilter = QtGui.MouseEventFilter.globalInstance()

        self._historyPath = None
        self._history = None

    def initializeInterface(self):
        """
        This is used to add all the widgets to the main layout and set all interface items.
        """

        self.upperLayout.addLayout(self.searchOptionsLayout)
        self.upperLayout.addWidget(self.searchLine)
        self.upperLayout.addWidget(self.replaceLine)
        self.upperLayout.addWidget(self.executeButton)
        self.masterLayout.addWidget(self.splitter)

        self.upperWidget.setLayout(self.upperLayout)
        self.splitter.addWidget(self.upperWidget)
        self.splitter.addWidget(self.infoBox)

        self.searchOptionsLayout.addWidget(self.selectionModeDrop)
        self.searchOptionsLayout.addStretch(0)
        self.searchOptionsLayout.addWidget(self.caseSensitiveCheck)
        self.searchOptionsLayout.addWidget(self.useRegexCheck)
        self.versionLayout.addStretch(0)
        self.versionLayout.addWidget(self.versionLabel)
        self.masterLayout.addLayout(self.versionLayout)

        self.searchLine.setCompleter(self.searchCompleter)
        self.replaceLine.setCompleter(self.replaceCompleter)

        self.removeMargins()

        self.setLayout(self.masterLayout)

    def initializeDefaults(self):
        """
        This will set all the initial values for all the widgets and self
        """

        self.selectionModeDrop.addItems([self.allNodes, self.selectedNodes])
        self.selectionModeDrop.setFixedWidth(120)
        self.upperWidget.setFixedHeight(125)

        self.searchLine.setPlaceholderText('Search:')
        self.replaceLine.setPlaceholderText('Replace:')

        self.infoBox.setReadOnly(True)
        self.infoBox.setLineWrapMode(QtGui.QTextEdit.NoWrap)

        self.versionLabel.setText(searchReplace.__version__)

        self.updateCompleter()

    def initializeSignals(self):
        """
        This will connect all the signals for all widgets and self
        """
        self.executeButton.pressed.connect(self.replace)
        self.selectionModeDrop.currentIndexChanged.connect(self.updateInfo)
        self.searchLine.editingFinished.connect(self.updateInfo)
        self.replaceLine.editingFinished.connect(self.updateInfo)
        self.caseSensitiveCheck.stateChanged.connect(self.updateInfo)
        self.useRegexCheck.stateChanged.connect(self.updateInfo)
        self.mouseFilter.mouseReleased.connect(self.updateInfo)

    def removeMargins(self):
        """
        Remove the margins from self, this creates a more integrated layout in nuke
        """
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        parentWidget = self.parentWidget()
        while parentWidget:
            parentLayout = parentWidget.layout()
            if parentLayout:
                parentLayout.setContentsMargins(0, 0, 0, 0)
            parentWidget = parentWidget.parentWidget()

    @property
    def nodes(self):
        """
        Returns:
             set: the current selection of  nodes.  All nodes if not set to selected
        """
        if self.selectionModeDrop.currentText() == self.selectedNodes:
            nodes = nuke.selectedNodes()
        else:
            nodes = common.utilities.allNodes()

        if not isinstance(nodes, set):
            nodes = set(nodes)

        return nodes

    @property
    def historyPath(self):
        """
        This will construct the path to the history path if it can find the .nuke folder for the
        user.  If one cannot be found then an empty string will be returned
        Returns:
            str: Path to the history file
        """
        if self._historyPath is None:
            userDir = common.utilities.getUserDir()
            if not userDir:
                self._historyPath = ''
            else:
                self._historyPath = os.path.join(userDir,
                                                 'searchReplace',
                                                 'history.dat').replace('\\', '/')
        return self._historyPath

    @property
    def history(self):
        """
        Loads the history file if one exists or returns an empty dict
        Returns:
            dict: Dictionary of the history for the search replace panel
        """
        if self._history is None:
            self._history = dict()
            if os.path.exists(self.historyPath):
                with open(self.historyPath, 'r') as historyFile:
                    self._history = json.load(historyFile)

        return self._history

    def updateInfo(self, *args):
        """
        Triggered when the user finished editing in either the search or replace line.  This is also
        triggered if the user updates the selection, or any of the search options.

        Once triggered this will get information from the nodes and format any file knobs with the
        search and replace information then updating the info box to display that
        """
        if not self.searchLine.text():
            self.infoBox.clear()
            return

        data = searchReplace.logic.getNodeInfo(self.nodes,
                                               str(self.searchLine.text()),
                                               str(self.replaceLine.text()),
                                               useRegex=self.useRegexCheck.isChecked(),
                                               caseSensitive=self.caseSensitiveCheck.isChecked())

        textItems = list()
        for nodeName, nodeData in data.items():
            knobTextItems = list()
            for knob, knobData in nodeData.items():
                # Since this will be setting html we need to ensure that the spaces are html.
                # otherwise, they will be squashed into single spaces
                knobTextItems.append('{knob}:&nbsp;input:&nbsp;{source}<br>'
                                     '{space}&nbsp;&nbsp;output:&nbsp;{output}'
                                     ''.format(knob=knob,
                                               source=knobData.get('in'),
                                               space='&nbsp;' * len(knob),
                                               output=knobData.get('out')))

            knobTextItems.insert(0, '<b>{name}</b>:'.format(name=nodeName))
            textItems.append('<br>'.join(knobTextItems))

        # set to use monospace font
        info = '<p style="font-family:consolas">{info}</p>'.format(info='<br><br>'.join(textItems))
        self.infoBox.setHtml(info)

    def replace(self):
        """
        Run the replacement for the nodes,  this will update the nodes as per the information
        displayed in the info box.  In addition this will save out the history to the history file,
        so it can be used for autocompletion later on
        """
        data = searchReplace.logic.getNodeInfo(self.nodes,
                                               str(self.searchLine.text()),
                                               str(self.replaceLine.text()),
                                               useRegex=self.useRegexCheck.isChecked(),
                                               caseSensitive=self.caseSensitiveCheck.isChecked())

        undoStack = nuke.Undo()
        undoStack.begin('Replace Text: {0}'.format(len(data.keys())))
        for nodeName, nodeData in data.items():
            node = nuke.toNode(nodeName)
            for knob, knobData in nodeData.items():
                matches = knobData.get('matches', None)
                if not matches:
                    continue
                searchReplace.logic.replaceText(node, knob, matches, str(self.replaceLine.text()))
        undoStack.end()
        self.updateInfo()
        self.updateHistory()

    def updateHistory(self):
        """
        Save out the current search and replace to the history file.  If a history file cannot be
        found or save then only a local history is kept
        """

        search = str(self.searchLine.text())
        searchHistory = self.history.get('search', list())
        replace = str(self.replaceLine.text())
        replaceHistory = self.history.get('replace', list())

        if search and search not in searchHistory:
            searchHistory.append(str(self.searchLine.text()))

        if replace and replace not in searchHistory:
            searchHistory.append(replace)

        while len(searchHistory) >= 100:
            searchHistory.pop(0)

        if len(replaceHistory) >= 100:
            searchHistory.pop(0)
        if replace and replace not in replaceHistory:
            replaceHistory.append(replace)

        self.history['search'] = searchHistory
        self.history['replace'] = replaceHistory

        if self.historyPath:
            if not os.path.exists(os.path.dirname(self.historyPath)):
                os.makedirs(os.path.dirname(self.historyPath))

            with open(self.historyPath, 'w') as historyFile:
                json.dump(self.history, historyFile)

        self.updateCompleter()

    def updateCompleter(self):
        """
        Update the completers for the search and replace lines with the latest history
        """
        searchHistory = self.history.get('search', list())
        self.searchCompleterModel.setStringList(searchHistory)
        replaceHistory = self.history.get('replace', list())
        self.replaceCompleterModel.setStringList(replaceHistory)

    def showCompleter(self):
        """
        Show the completer on the line that is currently in focus.  This is triggered by a keypress
        event
        """
        if self.searchLine.hasFocus():
            completer = self.searchCompleter
            line = self.searchLine
        else:
            completer = self.replaceCompleter
            line = self.replaceLine

        point = line.mapToGlobal(line.rect().bottomLeft())
        # For some reason the bottom left is a bit offset, so we need to shift it
        point.setX(point.x() + 7)

        completer.popup().move(point)
        completer.popup().setFixedWidth(line.width())
        completer.popup().adjustSize()
        completer.popup().show()

    def keyPressEvent(self, event):
        """
        Override to catch when the user presses the down arrow key so we can trigger the auto
        complete
        """
        if event.key() in [QtCore.Qt.Key_Down]:
            self.showCompleter()
            return

        return super(SearchReplacePane, self).keyPressEvent()

    def __call__(self):
        """
        Override for call method that is required for proper functionality as a panel in nuke
        """
        return self

    @classmethod
    def globalInstance(cls):
        """
        Checks if there is an already initialized instance of the interface and if so it will be
        returned.  If not then a new instance will be created
        Returns:
            SearchReplacePane: Instance of the Search Replace Pane
        """
        if cls._globalInstance is None:
            cls._globalInstance = cls()

        return cls._globalInstance


def start():

    global SEARCH_REPLACE_PANEL

    if not nuke.GUI:
        return None

    if SEARCH_REPLACE_PANEL is None:
        SEARCH_REPLACE_PANEL = SearchReplacePane.globalInstance()
        nuke.pluginAddPath(os.path.dirname(__file__))
        nukescripts.panels.registerWidgetAsPanel('{name}.SEARCH_REPLACE_PANEL'.format(name=__name__),
                                                 'SearchReplacePane',
                                                 'com.toqueIO.SearchReplacePane')

    return SEARCH_REPLACE_PANEL
