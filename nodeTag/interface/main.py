import os
import nuke
import nukescripts

from CommonQt import QtCore, QtGui
from nodeTag.globals import Globals
from nodeTag.interface.widgets import tagItem, customAction
import nodeTag.interface.processor
import nodeTag.logic


NODE_TAG_MANAGER = None


class NodeTagManager(QtGui.BaseWidget):

    _globalInstance = None

    SearchKeys = {Globals.selectedIndex: 'Selected',
                  Globals.tagSearchIndex: 'Tag Search'}

    dataUpdated = QtCore.Signal(dict)

    def __init__(self):
        super(NodeTagManager, self).__init__()

        self.setterControlWidget = QtGui.QWidget()

        self.splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.searchWidget = QtGui.QWidget()
        self._splitterHolder = QtGui.QVBoxLayout()

        self.tabWidget = QtGui.QTabWidget()
        self.customAction = customAction.CustomAction(self)

        self.masterLayout = QtGui.QVBoxLayout()
        self.searchLayout = QtGui.QVBoxLayout()
        self.generalSearchLayout = QtGui.QHBoxLayout()
        self.advancedSearchLayout = QtGui.QHBoxLayout()

        self.selectionDrop = QtGui.FilteredComboBox()
        self.tagSearchLine = QtGui.MultiCompleteLine()
        self.limitToSelectedCheck = QtGui.QCheckBox('Limit To Selected')

        self.advancedSearchLabel = QtGui.QLabel('Advanced Options:')
        self.addClassCheck = QtGui.QCheckBox('Class Tag')
        self.caseSensitiveCheck = QtGui.QCheckBox('Case Sensitive')
        self.exactMatchCheck = QtGui.QCheckBox('Exact Match')
        self.matchAllCheck = QtGui.QCheckBox('Match All')
        self.useRegExCheck = QtGui.QCheckBox('Use Regex')

        self.setterLayout = QtGui.QVBoxLayout()
        self.setterControlLayout = QtGui.QHBoxLayout()
        self.tagSetterLine = QtGui.MultiCompleteLine()
        self.tagSetButton = QtGui.QPushButton('Set')
        self.tagRemoveButton = QtGui.QPushButton('Remove')
        self.selectNodesButton = QtGui.QPushButton('Select')
        self.deleteNodesButton = QtGui.QPushButton('Delete')
        self.clearTagsButton = QtGui.QPushButton('Clear')
        self.appendCheck = QtGui.QCheckBox('Append')

        self.tagItemList = QtGui.CustomListWidget()

        self.progressBar = QtGui.QProgressBar()
        self.progressInfo = QtGui.QLabel()

        self.processor = nodeTag.interface.processor.Processor()
        self.mouseFilter = nodeTag.interface.processor.MouseEventFilter()

        self.data = dict()
        self.items = list()

    def initializeInterface(self):
        """
        This is used to add all the widgets to the main layout and set all interface items.
        """
        self.generalSearchLayout.addWidget(self.selectionDrop)
        self.generalSearchLayout.addWidget(self.tagSearchLine)
        self.generalSearchLayout.addWidget(self.limitToSelectedCheck)
        self.generalSearchLayout.addStretch()

        self.advancedSearchLayout.addStretch(0)
        self.advancedSearchLayout.addWidget(self.advancedSearchLabel)
        self.advancedSearchLayout.addWidget(self.addClassCheck)
        self.advancedSearchLayout.addWidget(self.caseSensitiveCheck)
        self.advancedSearchLayout.addWidget(self.exactMatchCheck)
        self.advancedSearchLayout.addWidget(self.matchAllCheck)
        self.advancedSearchLayout.addWidget(self.useRegExCheck)

        self.setterLayout.addWidget(self.tagSetterLine)
        self.setterControlLayout.addWidget(self.progressInfo)
        self.setterControlLayout.addStretch()
        self.setterLayout.addLayout(self.setterControlLayout)
        self.setterControlLayout.addWidget(self.appendCheck)
        self.setterControlLayout.addWidget(self.tagSetButton)
        self.setterControlLayout.addWidget(self.tagRemoveButton)
        self.setterControlLayout.addWidget(self.selectNodesButton)
        self.setterControlLayout.addWidget(self.deleteNodesButton)
        self.setterControlLayout.addWidget(self.clearTagsButton)
        self.setterControlWidget.setLayout(self.setterLayout)
        self.setterLayout.addWidget(self.progressBar)

        self.searchLayout.addLayout(self.generalSearchLayout)
        self.searchLayout.addLayout(self.advancedSearchLayout)

        self.splitter.addWidget(self.tagItemList)
        self.splitter.addWidget(self.setterControlWidget)
        self._splitterHolder.addWidget(self.splitter)
        self.searchLayout.addLayout(self._splitterHolder)
        self.searchWidget.setLayout(self.searchLayout)

        self.tabWidget.addTab(self.searchWidget, 'Node Tag')
        self.tabWidget.addTab(self.customAction, 'Custom Action')
        self.masterLayout.addWidget(self.tabWidget)

        self.setLayout(self.masterLayout)
        self.removeMargins()

    def initializeDefaults(self):
        """
        This will set all the initial values for all the widgets and self
        """

        self.selectionDrop.addItems(list(self.SearchKeys.values()))
        self.selectionDrop.setFixedWidth(125)
        self.tagSearchLine.setMinimumWidth(300)
        self.tagSetterLine.ignoreExisting = True
        self.setterControlWidget.setFixedHeight(100)
        self.progressInfo.setFixedWidth(200)

        tagSeparators = self.tagSearchLine.separators.pattern.replace('[', '').replace(']', '')
        self.tagSearchLine.setRegEx(Globals.baseTagSearchRegEx.format(''.join(tagSeparators)))
        self.tagSearchLine.setPlaceholderText('Search tags here')
        self.tagSearchLine.ignoreExisting = True
        self.tagSearchLine.separators = [' ', ',', '|']

        self.tagSetterLine.setPlaceholderText('Set tags here')
        self.tagSetterLine.separators = [' ', ',', '|']

        actions = [self.processor.actionSet,
                   self.processor.actionRemove,
                   self.processor.actionSelect,
                   self.processor.actionDelete,
                   self.processor.actionClear]
        for action in actions:
            actionMethod = getattr(self, 'menuAction{action}'.format(action=action.capitalize()))
            self.tagItemList.addMenuItem(action.capitalize(),
                                         action=actionMethod,
                                         selectionType=self.tagItemList.actionMultiple)

        self.advancedOptionsActivated()
        self.setMinimumWidth(625)

    def initializeSignals(self):
        """
        This will connect all the signals for all widgets and self
        """

        self.selectionDrop.currentIndexChanged.connect(self.advancedOptionsActivated)

        self.processor.tagItems.connect(self.createWidgets)
        self.processor.actionCompleted.connect(self.completeAction)
        self.dataUpdated.connect(self.processor.dataReceived)

        self.tagSearchLine.editingFinished.connect(self.updateData)
        self.tagSearchLine.itemComplete.connect(self.updateData)

        self.limitToSelectedCheck.stateChanged.connect(self.updateData)
        self.addClassCheck.stateChanged.connect(self.updateData)
        self.caseSensitiveCheck.stateChanged.connect(self.updateData)
        self.exactMatchCheck.stateChanged.connect(self.updateData)
        self.matchAllCheck.stateChanged.connect(self.updateData)
        self.useRegExCheck.stateChanged.connect(self.updateData)

        self.tagSetButton.pressed.connect(lambda: self.processAction(
            self.processor.actionSet))
        self.tagRemoveButton.pressed.connect(lambda: self.processAction(
            self.processor.actionRemove))
        self.selectNodesButton.pressed.connect(lambda: self.processAction(
            self.processor.actionSelect))
        self.deleteNodesButton.pressed.connect(lambda: self.processAction(
            self.processor.actionDelete))
        self.clearTagsButton.pressed.connect(lambda: self.processAction(self.processor.actionClear))

        self.mouseFilter.mouseState.connect(self.updateData)
        self.registerCallbacks()

    def registerCallbacks(self):
        """
        Register callbacks so interactions in the node graph will connect with the manager
        """
        app = QtGui.QApplication.instance()
        app.installEventFilter(self.mouseFilter)
        nuke.addOnDestroy(self.menuActionDelete)
        nuke.addOnUserCreate(self.updateData)

    def removeMargins(self):

        self.tabWidget.setContentsMargins(0, 0, 0, 0)
        self.masterLayout.setContentsMargins(0, 0, 0, 0)
        parentWidget = self.parentWidget()
        while parentWidget:
            parentLayout = parentWidget.layout()
            if parentLayout:
                parentLayout.setContentsMargins(0, 0, 0, 0)
            parentWidget = parentWidget.parentWidget()

    def updateData(self, *args, **kwargs):
        """
        Triggered when any of the tag search options are changed and will re-evaluate and re-process
        the tags.  This will send out a signal to the processor thread to collect the new updated
        information
        Args:
            *args: Unused in place to avoid errors when it gets called from signals
        """

        forceUpdate = kwargs.get('forceUpdate', False)
        self.data = {'selection': self.selectionDrop.currentIndex(),
                     'type': self.processor.update,
                     'forceUpdate': forceUpdate}

        if self.selectionDrop.currentIndex() == Globals.tagSearchIndex:
            self.data['tags'] = self.tagSearchLine.values
            self.data['limitToSelected'] = self.limitToSelectedCheck.isChecked()
            self.data['classTag'] = self.addClassCheck.isChecked()
            self.data['caseSensitive'] = self.caseSensitiveCheck.isChecked()
            self.data['exactMatch'] = self.exactMatchCheck.isChecked()
            self.data['matchAll'] = self.matchAllCheck.isChecked()
            self.data['useRegex'] = self.useRegExCheck.isChecked()

        if self.useRegExCheck.isChecked():
            self.tagSearchLine.removeRegEx()
        else:
            tagSeparators = self.tagSearchLine.separators.pattern.replace('[', '').replace(']', '')
            self.tagSearchLine.setRegEx(Globals.baseTagSearchRegEx.format(''.join(tagSeparators)))

        self.tagSearchLine.setCompletionValues(list(nodeTag.logic.getAllTags()))
        self.tagSetterLine.setCompletionValues(list(nodeTag.logic.getAllTags()))
        self.dataUpdated.emit(self.data)

    def menuActionSet(self, rows):
        """
        Triggers the action to set tags on the current items or selected items for the given rows
        Args:
            rows (list[int]): Rows to process the action on
        """
        self.processAction(self.processor.actionSet, rows=rows)

    def menuActionRemove(self, rows):
        """
        Triggers the action to remove tags on the current items or selected items for the given rows
        Args:
            rows (list[int]): Rows to process the action on
        """
        self.processAction(self.processor.actionRemove, rows=rows)

    def menuActionSelect(self, rows):
        """
        Triggers the action to select the nodes in the current selection of tag items
        Args:
            rows (list[int]): Rows to process the action on
        """
        self.processAction(self.processor.actionSelect, rows=rows)

    def menuActionDelete(self, rows=None):
        """
        Triggers the action delete select the nodes in the current selection of tag items
        Args:
            rows (list[int]|optional): Rows to process the action on, if this is not passed then
                                       this will collect the current node remove that
        """

        if rows:
            self.processAction(self.processor.actionDelete, rows=rows)
        else:
            self.processAction(self.processor.actionDelete, nodes={nuke.thisNode()})

    def menuActionClear(self, rows):
        """
        Triggers the action to clear the tags on the current items or selected items for the given
        rows
        Args:
            rows (list[int]): Rows to process the action on
        """
        self.processAction(self.processor.actionClear, rows=rows)

    def processAction(self, action, rows=None, nodes=None):
        """
        Will take the given rows, or process all rows if none are given and trigger the given action

        Actions:
            set: Sets the current tags on the specified rows
            remove: Removes the current tags on the specified rows
            select: Selects the nodes based on the current tag search
            delete: Deletes the nodes based on the current tag search
            clear: Clears all tags from the nodes based on the current tag search or items
            custom: Triggers a custom action
        Args:
            action (str): The action that is to be triggered on the specified items
            rows (list[int]|optional): List of rows to process
            nodes (set[nuke.Node]|optional): Set of nodes to remove, if given then the warning to
                                             delete is ignored
        """
        if action == self.processor.actionDelete and not nodes:
            proceed = nuke.ask('Do you want to delete the tagged nodes?')
            if not proceed:
                return

        self.data['tags'] = self.tagSearchLine.values
        actionFilters = {'type': self.processor.action,
                         'action': action,
                         'setTags': self.tagSetterLine.values,
                         'append': self.appendCheck.isChecked()}

        if rows or nodes:
            if not nodes:
                nodes = set()
                for row in rows:
                    item = self.tagItemList.item(row)
                    widget = self.tagItemList.itemWidget(item)
                    node = widget.tagItem.node
                    nodes.add(node)
            else:
                actionFilters['nukeDelete'] = True
            actionFilters['nodes'] = nodes

        self.dataUpdated.emit(actionFilters)
        if action not in [self.processor.actionSelect]:
            self.tagSetterLine.setText('')

    @QtCore.Slot(set)
    def createWidgets(self, tagItems):
        """
        Triggered when a signal is received from the processor.  The signal will contain the tag
        data items that will be used to create the tag widget items that are to be added to the list

        Args:
            tagItems (set[tagItem.TagItem]): List of the tag data items that need to have widgets
                                             created for
        """
        currentNames = list()
        self.items = tagItems
        for index, item in enumerate(self.tagItemList.widgets):
            try:
                currentNames.append(item.tagItem.node.fullName())
            except ValueError:
                self.tagItemList.removeItem(index)

        names = {item.name for item in tagItems if nuke.exists(item.name)}
        total = len(names)
        if set(currentNames) != names:
            self.progressBar.setRange(0, total)
            self.tagItemList.clear()
            for index, item in enumerate(sorted(tagItems, key=(lambda a: a.name))):
                self.progressBar.setValue(index)
                self.progressInfo.setText('{name} {count}/{total}'.format(name=item.node.fullName(),
                                                                          count=index,
                                                                          total=total))
                widget = tagItem.TagItemWidget(item, updateSignal=self.dataUpdated)
                self.tagItemList.addWidget(widget)

            self.progressBar.setValue(total)
            self.progressInfo.setText('')

        for widget in self.tagItemList.widgets:
            if nuke.exists(widget.tagItem.name):
                widget.updateLabels()

    @QtCore.Slot(str)
    def completeAction(self, data):
        """
        Triggered from the processor after actions are completed so that the list is updated
        Args:
            data (dict): The data for the action that was just completed
        """

        action = data.get('action', None)
        inTagSearchMode = self.selectionDrop.currentIndex() == Globals.tagSearchIndex
        if action in [self.processor.actionSelect] and not inTagSearchMode:
            # We specifically create the items passed as for some reason the update wont add
            # back just the currently selected items.
            # TODO:  Figure out why this is happening and change to just update
            self.items = data.get('tagItems', set())
            self.tagItemList.clear()
            self.createWidgets(self.items)

        elif action in [self.processor.actionDelete]:
            self.tagItemList.clear()
            self.items = list()
            self.updateData(forceUpdate=True)
        else:
            self.tagItemList.clear()
            self.updateData(forceUpdate=True)

    @QtCore.Slot()
    def advancedOptionsActivated(self):
        """
        Triggered whenever the advanced options are enabled in the gui and will handle
        showing/hiding any of the controls that are to be used for advanced searches.  Once these
        have been activated it will trigger an update of the data to ensure that the tag list is
        representing the most up to date search
        """
        advancedControls = [self.addClassCheck, self.caseSensitiveCheck, self.exactMatchCheck,
                            self.useRegExCheck, self.tagSearchLine, self.limitToSelectedCheck,
                            self.advancedSearchLabel, self.matchAllCheck]
        enableAdvancedControls = self.selectionDrop.currentIndex() == Globals.tagSearchIndex
        for control in advancedControls:
            control.setVisible(enableAdvancedControls)

        self.tagSearchLine.setFixedWidth(
            self.width() - (self.selectionDrop.width() + self.limitToSelectedCheck.width() + 50))

        self.updateData()

    def resizeEvent(self, event):
        """
        Override to ensure that the search line stays the correct size compared to the selection
        option drop
        Args:
            event (QtGui.QResizeEvent): Resize event that was triggered
        """
        super(NodeTagManager, self).resizeEvent(event)
        self.tagSearchLine.setFixedWidth(
            self.width() - (self.selectionDrop.width() + self.limitToSelectedCheck.width() + 50))

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

    global NODE_TAG_MANAGER

    if not nuke.GUI:
        return None

    if NODE_TAG_MANAGER is None:
        NODE_TAG_MANAGER = NodeTagManager.globalInstance()
        nuke.pluginAddPath(os.path.dirname(__file__))
        nukescripts.panels.registerWidgetAsPanel('{name}.NODE_TAG_MANAGER'.format(name=__name__),
                                                 'NodeTagManager',
                                                 'com.nukeDr.NodeTagManager')

    return NODE_TAG_MANAGER

