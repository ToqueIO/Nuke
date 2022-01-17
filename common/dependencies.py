import nuke

import common.utilities


__release__ = 'release'
__major__ = 1
__minor__ = 0
__bugfix__ = 0
__version__ = '{release} {major:02}.{minor:02}.{bugfix:02}'.format(release=__release__,
                                                                   major=__major__,
                                                                   minor=__minor__,
                                                                   bugfix=__bugfix__)


class Dependencies(object):

    all = 'all'
    expression = 'exp'
    none = None

    def __init__(self):

        self.nodes = set()
        self.expressionNodes = set()

    def _getExpressionDependencies(self, node, nodes=None):
        """
        This will collect all of the expression linked nodes recursively for the given node.  If a
        given list of nodes is provided all of the collected nodes will be added to that set and
        returned
        Args:
            node (nuke.Node): This is the node in which to collect the expression dependencies for
            nodes (set|optional): This is a set of node to add the collected nodes to and will be
                                  returned

        Returns:
            set: This is a set of the collected dependencies or if a set of nodes is given it will
                 be that set with the addition of the collected dependencies
        """
        nodes = nodes or set()
        expressionNodes = nuke.dependencies(node, nuke.EXPRESSIONS)
        self.expressionNodes.add(node)

        if not expressionNodes:
            return nodes

        for expressionNode in expressionNodes:
            # We don't want to collect the expressions more than once in the event multiple nodes
            # are expression linked to a single node.  We could get into a recursion loop otherwise
            if expressionNode not in self.expressionNodes:
                nodes = nodes.union(self._getExpressionDependencies(expressionNode, nodes))
                nodes.add(expressionNode)

        nodes.add(node)
        return nodes

    def _getDependencies(self, node, **kwargs):
        """
        This is used to collect all the dependencies used by a given node.  This can collect and
        check both connected nodes and expression linked nodes
        Args:
            node (nuke.Node): This is the node to collect the dependencies for

        Kwargs:
            disableInclusion (str|optional): This is the 

        Returns:

        """
        disableInclusion = kwargs.get('disableInclusion', self.none)
        getExpressionLinked = kwargs.get('getExpressionLinked', True)
        recurseGroups = kwargs.get('recurseGroups', False)

        inputs = node.inputs()

        if disableInclusion != self.all:
            knob = node.knob('disable')
            if knob:
                disabled = knob.value()

                if disableInclusion == self.none:
                    if disabled:
                        inputs = 1

                elif disableInclusion == self.expression:
                    if disabled and not knob.isAnimated():
                        inputs = 1

        for inputId in range(inputs):
            connectedNode = node.input(inputId)
            if not connectedNode:
                continue

            dependentNodes = {connectedNode}
            if getExpressionLinked:
                dependentNodes = self._getExpressionDependencies(connectedNode, dependentNodes)

            if recurseGroups:
                try:
                    dependentNodes = dependentNodes.union(
                        common.utilities.allNodes(context=connectedNode))
                except AttributeError:
                    pass

            for dependentNode in dependentNodes:
                if dependentNode in self.nodes:
                    continue

                self.nodes = self.nodes.union(self._getDependencies(dependentNode, **kwargs))

        self.nodes.add(node)

        return self.nodes

    @classmethod
    def getDependencies(cls, node, **kwargs):

        dependencies = cls()
        return dependencies._getDependencies(node, **kwargs)
