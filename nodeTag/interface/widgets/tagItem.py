import nuke
import copy
import nodeTag.logic

from CommonQt import QtGui, QtCore


class TagItemWidget(QtGui.BaseWidget):
    """
    Simple widget item to display the node and its tag data
    """

    def __init__(self, tagItem, updateSignal=None):
        super(TagItemWidget, self).__init__()

        self.updateSignal = updateSignal
        self.tagItem = tagItem

        self.masterLayout = QtGui.QVBoxLayout()
        self.nodeInfoLayout = QtGui.QHBoxLayout()

        self.nameLabel = QtGui.QLabel()
        self.classLabel = QtGui.QLabel()
        self.tagsLabel = QtGui.QLabel()
        self.filters = dict()

    def initializeDefaults(self):
        """
        Set the defaults for the widget
        """
        self.updateLabels()

    def initializeInterface(self):
        """
        Set the base interface.
        Adding widgets to layouts and setting base layouts.
        Sets base values on widgets
        """
        self.nodeInfoLayout.addWidget(self.nameLabel)
        self.nodeInfoLayout.addStretch()
        self.nodeInfoLayout.addWidget(self.classLabel)

        self.masterLayout.addLayout(self.nodeInfoLayout)
        self.masterLayout.addWidget(self.tagsLabel)

        self.setLayout(self.masterLayout)
        self.tagsLabel.setText('|'.join(self.tagItem.formattedTags))

    def initializeSignals(self):
        """
        Connects all the signals for the current instance (self)
        """
        if self.updateSignal:
            self.updateSignal.connect(self.tagItem.updateFilters)

    def updateLabels(self):
        """
        Updates the labels on self to reflect the information for the current node
        """
        self.nameLabel.setText('Name: {0}'.format(self.tagItem.node.fullName()))
        self.classLabel.setText('Class: {0}'.format(self.tagItem.node.Class()))
        self.tagsLabel.setText('|'.join(self.tagItem.formattedTags))


class TagItem(QtCore.QObject):
    """
    Data item for handling the tags on a node and providing basic information for the tag gui
    """

    colourMatchingTag = '#38d100'
    colourMissingTag = '#ff5e5e'

    _globalInstances = dict()

    def __init__(self, node, filters=None):
        super(TagItem, self).__init__()

        self._node = None
        self.node = node

        self._name = None
        self._formattedTags = None

        self.filters = filters or dict()

    @property
    def node(self):
        """
        Returns:
            nuke.Node: This is the node the current instance (self) pertains to
        """
        if not isinstance(self._node, nuke.Node):

            if self._node:
                self._node = nuke.toNode(self._node)

        return self._node

    @node.setter
    def node(self, value):
        """
        Used to set the node for the current instance (self)  This will ensure that the cache for the current node
        is cleared to avoid and issues later.  Once that has been done it will either set the node to the value or
        do a call to nuke collecting the node by name
        Args:
            value (str|nuke.Node): Either the node object or the name of the node
        """
        self._name = None
        self._formattedTags = None
        if self._node:
            self._globalInstances[self._node.__hash__()] = None

        if isinstance(value, nuke.Node):
            self._node = value

        else:
            self._node = nuke.toNode(value)

    @property
    def name(self):
        """
        Returns:
            str: The name of the node that pertains to the current instance (self)
        """
        if self._name is None:
            self._name = self.node.name()

        return self._name

    @property
    def tags(self):
        """
        Returns:
            set: This is a set of all the tags that are present on the node
        """
        return nodeTag.logic.getTags(self.node, **self.filters)

    @property
    def formattedTags(self):
        """
        Takes all the tags for the current node and will format them into a html string that has all matching tags
        as green, missing as red and all others as default grey.  This is determined from the data recieved from the
        processor
        Returns:
            str: html formatted string of all tags on the node
        """
        if self._formattedTags is None:
            self.blockSignals(True)
            search = self.filters.get('tags', set())

            if not isinstance(search, set):
                search = set(search)

            tags = {self.colourMissingTag: set(),
                    self.colourMatchingTag: set()}
            existingTags = copy.copy(self.tags)

            for tag in search:
                matchedTags = list(nodeTag.logic.getTagMatches(self.node, tag, **self.filters))

                if len(matchedTags) > 1:
                    for matchedTag in matchedTags:
                        tags[self.colourMatchingTag].add(matchedTag)

                    continue

                elif matchedTags:
                    tags[self.colourMatchingTag].add(matchedTags[0])
                else:
                    tags[self.colourMissingTag].add(tag)

            _formattedTags = list()
            for colourKey in [self.colourMatchingTag, self.colourMissingTag]:
                tagList = sorted(tags.get(colourKey, set()))
                for tag in tagList:
                    if tag in existingTags:
                        existingTags.remove(tag)
                    _formattedTags.append('<font color="{colour}">{tag}</font>'.format(colour=colourKey, tag=tag))

            _formattedTags.extend(existingTags)
            self._formattedTags = _formattedTags
            self.blockSignals(False)

        return self._formattedTags

    @QtCore.Slot(dict)
    def updateFilters(self, filters):
        """
        Triggered when data is received from the processor with updated filter information for the tags
        Args:
            filters (dict): information dict with all the filters and their settings
        """
        self.filters = filters
        self._formattedTags = None

    @classmethod
    def removeInstance(cls, node):
        """
        Removes the cached instance of the node
        Args:
            node (nuke.Node|str): Either the node object or the name of the node
        """
        if not isinstance(node, nuke.Node):
            node = nuke.toNode(node)

        instance = cls._globalInstances.get(node.__hash__(), None)
        if instance:
            try:
                del cls._globalInstances[node.__hash__]
            except KeyError:
                return

    @classmethod
    def globalInstance(cls, node):
        """
        Collects the cached instance of the Tag item for the given node.  If one is not yet created a new one will be
        initialized
        Args:
            node (nuke.Node|str): Either the node object or the name of the node

        Returns:
            TagItem: Instance of the TagItem for the given node
        """
        if not isinstance(node, nuke.Node):
            node = nuke.toNode(node)

        instance = cls._globalInstances.get(node.__hash__(), None)
        if not instance:
            instance = cls(node)
            cls._globalInstances[node.__hash__()] = instance

        return instance
