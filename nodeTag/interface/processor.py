import nuke
import nodeTag.logic

from CommonQt import QtCore
import common.utilities
from nodeTag.interface.widgets import tagItem
from nodeTag.globals import Globals


class _Processor(QtCore.QObject):
    """
    Base processor object that will handle all the processing for the node tags and the creation of
    the tag items for the UI
    """

    _globalInstance = None
    _thread = QtCore.QThread()
    tagItems = QtCore.Signal(set)
    actionCompleted = QtCore.Signal(dict)

    action = 'action'
    update = 'update'

    actionSet = 'set'
    actionRemove = 'remove'
    actionSelect = 'select'
    actionDelete = 'delete'
    actionClear = 'clear'
    actionCustom = 'custom'

    def __init__(self):
        super(_Processor, self).__init__()

        self._nodes = set()
        self._data = dict()

    @QtCore.Slot(dict)
    def dataReceived(self, data):
        """
        Triggered when an update is emitted from the UI after any of the filter options have been
        updated or an action has been triggered

        Args:
            data (dict): Data for the update that is to be triggered. Primary key used is type to
                         determine the update that is being triggered
        """
        processType = data.get('type', self.update)
        forceUpdate = data.get('forceUpdate', False)
        if processType == self.update:
            self._data = data
            self._update(forceUpdate=forceUpdate)
        elif processType == self.action:
            self._data.update(data)
            self._runAction()

    def _update(self, forceUpdate=False):
        """
        This will check all the nodes either getting selected nodes or nodes with the tags in the
        filters.  Once the nodes have been collected then tag items will be created and emitted
        Args:
            forceUpdate (bool|optional): True or False if we want to force the update process
        """

        selectionType = self._data.get('selection', Globals.selectedIndex)
        if selectionType == Globals.selectedIndex:
            nodes = nuke.selectedNodes()
        else:
            forceUpdate = True
            if not self._data.get('tags', None):
                nodes = set()
            else:
                nodes = nodeTag.logic.findNodes(**self._data)

        if nodes == self._nodes and not forceUpdate:
            return

        self._nodes = nodes
        tagItems = {tagItem.TagItem.globalInstance(node) for node in self._nodes}

        for item in tagItems:
            item.updateFilters(self._data)

        self.tagItems.emit(tagItems)

    def _runAction(self):
        """
        Runs the action that is specified in the data provided from the GUI.

        Current actions:
        Set:
            This will set the tags on the nodes replacing the exiting tags

        Remove:
            This will remove the passed tags from the nodes if they exist

        Clear:
            This will clear all tags from the nodes

        Delete:
            This will delete all the nodes that are in the current filter

        Select:
            This will select all the nodes that are in the current filter
        """
        action = self._data.get('action', None)

        nodes = self._data.get('nodes', self._nodes)
        if action == self.actionSet:
            nodeTag.logic.tagNodes(nodes,
                                   self._data.get('setTags'),
                                   append=self._data.get('append'))
        elif action == self.actionRemove:
            for node in nodes:
                nodeTag.logic.removeTags(node,
                                         self._data.get('setTags'))
        elif action == self.actionClear:
            for node in nodes:
                nodeTag.logic.clearTags(node)
        elif action == self.actionDelete:
            if not self._data.get('nukeDelete', False):
                common.utilities.delete(nodes)
            for node in nodes:
                tagItem.TagItem.removeInstance(node)
            self._nodes = set()
        elif action == self.actionSelect:
            self._data['tagItems'] = {tagItem.TagItem.globalInstance(node) for node in nodes}
            self._nodes = nodes
            common.utilities.select(nodes)

        self.actionCompleted.emit(self._data)

    @classmethod
    def globalInstance(cls):
        """
        Checks to see if there is an instance already created and returns that if there is.
        Otherwise, this will create a new instance and return that

        Returns:
            _Processor: Instance of the Processor
        """
        if cls._globalInstance is None:
            cls._globalInstance = cls()
            cls._globalInstance.moveToThread(cls._thread)
            cls._thread.start()

        return cls._globalInstance


class MouseEventFilter(QtCore.QObject):

    mouseState = QtCore.Signal()

    def eventFilter(self, obj, event):
        """
        Override handler used to emit a signal anytime there is a mouse button release from inside
        of nuke.
        """
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            self.mouseState.emit()

        return super(MouseEventFilter, self).eventFilter(obj, event)


Processor = _Processor.globalInstance
