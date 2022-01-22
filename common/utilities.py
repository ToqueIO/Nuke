import nuke
import logging
import threading


__release__ = 'release'
__major__ = 1
__minor__ = 1
__bugfix__ = 0
__version__ = '{release} {major:02}.{minor:02}.{bugfix:02}'.format(release=__release__,
                                                                   major=__major__,
                                                                   minor=__minor__,
                                                                   bugfix=__bugfix__)


def allNodes(**kwargs):
    """
    This is an extension on nukes internal node collection and is used to collect all nodes in a
    script.  This extends the ability allowing for re-cursing gizmos

    Kwargs:
        recurseGroups (bool|optional): True or False if the node collection should recurse groups
        recurseGizmos (bool|optional): True or False if the node collection should recurse gizmos
        context (nuke.Node|optional): This is the node context to use when collecting nodes.
                                      Generally used only when re-cursing gizmos
        nodeClass (str|optional): This is a node class to limit the node collection to

    Returns:
        set: This is a set of all the collected nodes
    """
    recurseGroups = kwargs.get('recurseGroups', False)
    recurseGizmos = kwargs.get('recurseGizmos', False)
    context = kwargs.get('context', None)
    nodeClass = kwargs.get('nodeClass', None)

    if context:
        with context:
            return allNodes(recurseGroups=recurseGroups, recurseGizmos=recurseGizmos)

    if nodeClass:
        baseList = set(nuke.allNodes(nodeClass, recurseGroups=recurseGroups))
    else:
        baseList = set(nuke.allNodes(recurseGroups=recurseGroups))

    if any([recurseGizmos, recurseGroups]):
        for node in baseList:
            if recurseGizmos and isinstance(node, nuke.Gizmo):
                logging.debug('Processing Gizmo:', node.fullName())
                baseList = baseList.union(allNodes(recurseGroups=recurseGroups,
                                          recurseGizmos=recurseGizmos,
                                          context=node))

    return baseList


def select(nodes, **kwargs):
    """
    This will select all of the given nodes,  if the kwarg is passed this will append the current
    selection.  If append is not passed then the current collection will be cleared
    Args:
        nodes (set|nuke.Node|list): This is a set/list of nodes to select or a single node

    Kwargs:
        append (bool): True or False if this should append the current selection of nodes or not
    """
    append = kwargs.get('append', False)
    selected = set()
    if append:
        selected = set(nuke.selectedNodes())

    deselect()

    if isinstance(nodes, nuke.Node):
        nodes = {nodes}
    elif not isinstance(nodes, set):
        nodes = set(nodes)

    nodes = nodes.union(selected)

    if threading.current_thread() is not threading.main_thread():
        nuke.executeInMainThread(select, args=(nodes,))
        return

    for node in nodes:
        node['selected'].setValue(True)


def deselect(nodes=None):
    """
    This will deselect all nodes in the node graph.  If a set/list of nodes are passed then they
    will be the only nodes that are deselected

    Kwargs:
        nodes (set|nuke.Node|list): This is a set/list of nodes to deselect or a single node
    """
    nodes = nodes or allNodes()

    if isinstance(nodes, nuke.Node):
        nodes = {nodes}
    elif not isinstance(nodes, set):
        nodes = set(nodes)

    if threading.current_thread() is not threading.main_thread():
        nuke.executeInMainThread(deselect, args=(nodes,))
        return

    for node in nodes:
        node['selected'].setValue(False)


def delete(nodes):
    """
    This will delete all the given nodes,
    Args:
        nodes (set|nuke.Node|list): This is a set/list of nodes to delete or a single node
    """

    if isinstance(nodes, nuke.Node):
        nodes = {nodes}
    elif not isinstance(nodes, set):
        nodes = set(nodes)

    if threading.currentThread():
        pass

    undoStack = nuke.Undo()
    undoStack.begin('Delete Nodes: {0}'.format(len(nodes)))
    # Deletion should always happen in the main thread otherwise it can cause nuke to crash
    if threading.current_thread() is not threading.main_thread():
        nuke.executeInMainThread(delete, args=(nodes,))
        return

    for node in nodes:
        nuke.delete(node)

    undoStack.end()


def getFileKnobs(node):
    """
    helper method to collect all the file knobs on a node
    Args:
        node (nuke.Node): node to collect the knobs from

    Returns:
        set: set of all the file knobs present on the node or an empty set if there are none
    """
    fileKnobs = set()
    for knob in node.knobs():
        knob = node[knob]
        if isinstance(knob, nuke.File_Knob):
            fileKnobs.add(knob)

    return fileKnobs


def getFilenames(node):
    """
    Helper method to get the filenames from a nuke node as nuke.filename doesn't always return the
    filename if it is a user node/gizmo and only accounts for a single filename
    Args:
        node (nuke.Node): node to collect filenames from

    Returns:
        set: set of all the filenames on the node or an empy set if there are none
    """

    fileKnobs = getFileKnobs(node)

    filenames = set()
    for knob in fileKnobs:
        if knob.value():
            filenames.add(knob.value())

    return filenames
