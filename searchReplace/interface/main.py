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

        self.mouseFilter = QtGui.MouseEventFilter.globalInstance()

    def initializeInterface(self):

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

        self.setLayout(self.masterLayout)

    def initializeDefaults(self):

        self.selectionModeDrop.addItems([self.allNodes, self.selectedNodes])
        self.selectionModeDrop.setFixedWidth(120)
        self.upperWidget.setFixedHeight(125)

        self.searchLine.setPlaceholderText('Search:')
        self.replaceLine.setPlaceholderText('Replace:')

        self.infoBox.setReadOnly(True)
        self.infoBox.setLineWrapMode(QtGui.QTextEdit.NoWrap)

    def initializeSignals(self):
        self.executeButton.pressed.connect(self.replace)
        self.selectionModeDrop.currentIndexChanged.connect(self.updateInfo)
        self.searchLine.editingFinished.connect(self.updateInfo)
        self.replaceLine.editingFinished.connect(self.updateInfo)
        self.caseSensitiveCheck.stateChanged.connect(self.updateInfo)
        self.useRegexCheck.stateChanged.connect(self.updateInfo)
        self.mouseFilter.mouseReleased.connect(self.updateInfo)

    @property
    def nodes(self):

        if self.selectionModeDrop.currentText() == self.selectedNodes:
            nodes = nuke.selectedNodes()
        else:
            nodes = common.utilities.allNodes()

        return nodes

    def updateInfo(self, *args):

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
            NodeTagManager: Instance of the Node Tag Manager
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
