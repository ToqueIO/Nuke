import nuke
import copy
import re
import logging

import common.utilities

from nodeTag.globals import Globals

# Version information
__Major__ = '1'
__Minor__ = '0'
__BugFix__ = '0'
__version__ = '.'.join([__Major__, __Minor__, __BugFix__])

# Creator information
__author__ = 'Joshua Robertson'
__copyright__ = 'Copyright 2021, Joshua Robertson'
__license__ = 'GPL 3.0'
__email__ = 'dragobyvfx@gmail.com'

'''
This is a base logic system for tagging and managing tags on nodes inside of nuke.  This allows for more complex logic
when it comes to identifying and locating nodes

Here are a list of common kwargs that can be passed to most of the functions.  Not all are used directly but can
cascade down into sub calls of each function
Kwargs:
    append (bool|optional): True or False if the given tag is to be appended to the nodes tags or if it shall
                            replace the existing tags
           default: False
    create (bool|optional): True or False if we should create the tag knob if one does not yet exist
           default: True
    classTag (bool|optional): True or False if we are to include the nodes class as a tag
             default: False     
    caseSensitive (bool|optional): True or False if the tag check should ignore the case of the tags when checking
                                   if a tag exists
                  default: True 
    exactMatch (bool|optional): True or False if the tag should be an exact match to the search query
               default: True
    useRegex (bool|optional): True or False if the tag query given is a regex and should be processed using re
    subInvalidTags (bool|optional): True of False if invalid characters in given tag should be replaced when adding
                                    the tag to the node
                   default: False
    ignoreErrors (bool|optional): True of False if errors are to be ignored when processing the tag knob
                 default: False
                 
License:
    This file is part of NodeTag.
    
    NodeTag is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    NodeTag is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with NodeTag.  If not, see <https://www.gnu.org/licenses/>.     
'''


def addTag(node, tag, **kwargs):
    """
    This will add the given tag to the given node.  If the create kwarg is created this will also create the tag knob
    if one is not yet present
    Args:
        node (nuke.Node): This is the node in which to add the tag to
        tag (str): This is the tag to add to the node

    Kwargs:
        append (bool|optional): True or False if the given tag is to be appended to the nodes tags or if it shall
                                replace the existing tags
               default: False
        create (bool|optional): True or False if we should create the tag knob if one does not yet exist
               default: True
        classTag (bool|optional): True or False if we are to include the nodes class as a tag
                 default: False
        subInvalidTags (bool|optional): True of False if invalid characters in given tag should be replaced when adding
                                        the tag to the node
                       default: False
       ignoreErrors (bool|optional): True of False if errors are to be ignored when processing the tag knob
                    default: False
    """
    append = kwargs.get('append', False)

    existingTags = set()
    if append:
        existingTags = getTags(node, **kwargs)

    validTag = validateTag(tag, **kwargs)

    existingTags.add(validTag)
    tags = Globals.tagSeparator.join(existingTags)
    knob = getTagKnob(node, **kwargs)
    knob.setValue(tags)


def addTags(node, tags, **kwargs):
    """
    This will add all of the given tags to the given node.  Each tag will be validated to ensure that they meet the
    requirements
    Args:
        node (nuke.Node): This is the node in which to add the tag to
        tags (list|str|set): This is a list of tags to add to the given node

    See module level docs for possible Kwargs
    """
    if isinstance(tags, str):
        tags = getTagsFromString(tags)

    if isinstance(tags, set):
        tags = list(tags)

    tags = copy.copy(tags)
    if not tags:
        return

    firstTag = tags.pop(0)
    addTag(node, firstTag, **kwargs)
    kwargs['append'] = True
    for tag in tags:
        addTag(node, tag, **kwargs)


def removeTag(node, tag, **kwargs):
    """
    This will remove a given tag from the given node if it is present
    Args:
        node (nuke.Node): This is the node in which to remove the tag from
        tag (str): This is the tag to remove from the node

    See module level docs for possible Kwargs
    """
    tagMatches = getTagMatches(node, tag, **kwargs)
    tags = list(getTags(node, **kwargs))
    for tag in tagMatches:
        tags.remove(tag)

    if tags:
        addTags(node, tags, **kwargs)
    else:
        clearTags(node)

    return hasTag(node, tag)


def removeTags(node, tags, **kwargs):
    """
    This will attempt to remove the given tags from the given node
    Args:
        node (nuke.Node): This is the node in which to remove the tags from
        tags (list|str|set): This is a list of tags to remove from the given node

    See module level docs for possible Kwargs
    """
    for tag in tags:
        removeTag(node, tag, **kwargs)


def clearTags(node):
    """
    This will remove all the tags from the node if there are any present
    Args:
        node (nuke.Node): This is the node in which to remove the tags from
    """
    knob = getTagKnob(node, create=True)
    knob.setValue('')


def tagNodes(nodes, tags, **kwargs):
    """
    This will add the given tags to all of the given nodes
    Args:
        nodes (list|set): This is a list or set of nodes in which to add the tags to
        tags (list|set|str): This is either a list, set or formatted string of nodes to add to the given nodes

    See module level docs for possible Kwargs
    """
    for node in nodes:
        addTags(node, tags, **kwargs)


def getTags(node, **kwargs):
    """
    This will collect all of the tags from the given node and return a set of all the collected tags
    Args:
        node (nuke.Node): This is the node in which to collect the tags from
    Kwargs:
        classTag (bool|optional): True or False if the nodes class should be included as a tag
                 default: False
        create (bool|optional): True or False if we should create the tag knob if one does not yet exist
               default: True

    See module level docs for any additional possible Kwargs

    Returns:
        set: This is a set of all the tags that where found on the node
    """
    classTag = kwargs.get('classTag', False)

    knob = getTagKnob(node, **kwargs)
    if not knob:
        return set()

    tags = set(getTagsFromString(knob.value()))
    if classTag:
        tags.add(node.Class())

    return tags


def getTagsFromString(tags):
    """
    This will take a given string and attempt to extract any tags from it.  This will also validate all of the collected
    tags to ensure that they conform with the tag rules
    Args:
        tags (str): This is a formatted string that contains possible tags.  The tags should be separated by any of the
                    following characters [' ', '|', '\n', ',']

    Returns:
        set: This is a set of the collected tags
    """
    if not isinstance(tags, str):
        raise TypeError('Expected a String {0} found'.format(type(tags)))

    for separator in Globals.potentialSeparators:
        tags = tags.replace(separator, Globals.tagSeparator)

    tags = [tag.strip(Globals.tagSeparator) for tag in tags.split(Globals.tagSeparator) if tag]
    tags = set(tags)

    tags = validateTags(tags, ignoreErrors=True, subInvalidTags=False)

    return tags


def getTagKnob(node, **kwargs):
    """
    This will collect the tag knob from a node and if it doesn't exist will create it if specified
    Args:
        node (nuke.Node): This is the node to collect the knob from

    Kwargs:
        create (bool|optional): True or False if the knob should be created when it doesn't exist
               default: True

    Returns:
        nuke.Knob|None: this is the tag knob or None if it doesn't exist
    """
    knob = node.knob(Globals.tagKnobName)
    if not knob and kwargs.get('create', True):
        knob = createKnobs(node)

    return knob


def getTagMatches(node, tag, **kwargs):
    """
    This will take a given node and get all tags which match the given tag.  The tag that is given can be in many forms

    Exact Match:
        This will check to see if there is a tag that is an exact match of the given tag while also taking into account
        the given rules/kwargs

    Regex:
        This will check if the given tag in the form of a regex expression matches any of the tags currently on the node
        see documentation for regular expressions for valid formatting

    Wildcard:
        If regex is disabled but there is a * in the given tag then the search will use the * as a wildcard.
        for example if glo* is given and the tags are glow, glowing, globe, flow, snow  then glow, glowing, and globe
        would be returned as matches

    Args:
        node (nuke.Node): This is the node to get tag matches from
        tag (str): This is the search query/tag to find matches for

    Kwargs:
        caseSensitive (bool|optional): True or False if the tag check should ignore the case of the tags when checking
                                   if a tag exists
                       default: True
        exactMatch (bool|optional): True or False if the tag should be an exact match to the search query
                   default: True
        useRegex (bool|optional): True or False if the tag query given is a regex and should be processed using re

    See module level docs for additional possible Kwargs

    Returns:
        set: This is a set of all the tag matches found on the node
    """
    caseSensitive = kwargs.get('caseSensitive', True)
    exactMatch = kwargs.get('exactMatch', True)
    useRegex = kwargs.get('useRegex', False)

    tags = getTags(node, **kwargs)
    casedTags = {existingTag.lower(): existingTag for existingTag in tags}
    matches = set()
    if not caseSensitive:
        tag = tag.lower()
        tags = casedTags.keys()

    if ('*' in tag or useRegex) and exactMatch:
        if not useRegex:
            tag = tag.replace('*', r'\w*')
        regexMatch = re.findall(tag, ' '.join(tags))
        if regexMatch:
            matches = set([casedTags.get(match.lower()) for match in regexMatch if match in tags])

    elif not exactMatch:
        for existingTag in tags:
            if tag in existingTag:
                matches.add(casedTags.get(existingTag.lower()))

    else:
        if tag in tags:
            return {casedTags.get(tag.lower())}

    return matches


def findNodes(tags, **kwargs):
    """
    This will search and find all nodes that have the given tags.  This uses the getTagMatches to
    determine if there are any matching tags.  See the docstring for the getTagMatches function
    for more information

    Args:
        tags (list|str|set): This is a list of tags that will be used to search for nodes

    Kwargs:
        matchAll (bool|optional): True or False if nodes must match all the given tags.  If set to
                                  False then as long as one tag matches the node will be considered
                                  a match
                 default: True
        nodes (set|list|optional): This is a set or list of nodes in which to check for matches.
                                   If this is not given then all current nodes will be processed
              default: None
        limitToSelected (bool:optional): True or False if the node collection should be limited to
                                         only nodes within the current selection
              default: False

    See module level docs for possible additional Kwargs

    Returns:
        set: This is a set of all nodes found which match the search parameters provided
    """
    matchAll = kwargs.get('matchAll', True)
    nodes = kwargs.get('nodes', common.utilities.allNodes(**kwargs))

    if isinstance(tags, str):
        tags = getTagsFromString(tags)

    matches = set()
    if matchAll:
        filterFunction = all
    else:
        filterFunction = any

    limitToSelected = kwargs.get('limitToSelected', False)

    for node in nodes:
        if limitToSelected and not node['selected'].value():
            continue

        matchedTags = dict()
        for tag in tags:
            matchedTags[tag] = hasTag(node, tag, **kwargs)

        if filterFunction(matchedTags.values()):
            matches.add(node)
            continue

    return matches


def getAllTags(**kwargs):
    """
    This will collect all of the tags that are present in the current session.  If there are given
    nodes passed then this will only collect the tags for those nodes

    Kwargs:
        nodes (set|list|optional): This is a set or list of nodes in which to collect the tags from

    Returns:
        set: This is a set of all the tags which have been collected for the nodes
    """

    tags = set()

    nodes = kwargs.get('nodes',
                       common.utilities.allNodes(recurseGroups=True,
                                                 recurseGizmos=kwargs.get('recurseGizmos', False)))

    for node in nodes:
        nodeTags = getTags(node, **kwargs)
        if nodeTags:
            tags = tags.union(nodeTags)

    return tags


def hasTag(node, tag, **kwargs):
    """
    This will determine if the given node has the given tag

    see getTagMatches docs for acceptable kwargs
    Returns:
        bool: True or False if the given node has the given tag
    """
    return bool(getTagMatches(node, tag, **kwargs))


def validateTag(tag, **kwargs):
    """
    This will take a given tag and see if it is valid to be added to a node.  If the tag cannot be
    validated and ignore errors is enabled then this will return None if the tag is invalid
    Args:
        tag (str): This is the tag in which to validate

    see validateTags docs for available/accepted kwargs

    Returns:
        str|None: This is either the tag which has been validated or None if the tag is invalid
    """
    validatedTags = validateTags(tag, **kwargs)
    if validatedTags:
        return list(validatedTags)[0]

    return None


def validateTags(tags, **kwargs):
    """
    This will take a given set, list or formatted string of tags and validate them ensuring that
    they all meet the requirements for being added as a tag.

    The tag validation is done using regular expressions with the regex being defined in the globals
    but by default will only allow for alpha numeric tags using a reverse re check '[^a-zA-Z0-9_-]'

    Args:
        tags (list|set|str): This is a list, set or formatted string of tags to process

    Kwargs:
        subInvalidTags (bool|optional): This is True or False if invalid characters in the tags
                                        should be substituted. This will substitute the invalid
                                        characters for a -
                       default: False
        ignoreErrors (bool|optional): True or False if invalid tags should be ignored and just
                                      removed from the list. By default an error is raised if any
                                      invalid tags are found.  With this set to True then any errors
                                      will just be logged
                     default: False

    Returns:
        set: This is a set of all the validated tags
    """
    subInvalidTags = kwargs.get('subInvalidTags', False)
    ignoreErrors = kwargs.get('ignoreErrors', False)

    if isinstance(tags, str):
        tags = getTagsFromString(tags)

    invalidTags = dict()
    validTags = set()

    for tag in tags:
        invalidItems = re.findall(Globals.invalidCharacterFilter, tag)
        if invalidItems and subInvalidTags:
            tag = re.sub(Globals.invalidCharacterFilter, '-', tag)
            validTags.add(tag)
        elif invalidItems:
            invalidTags[tag] = invalidItems
        else:
            validTags.add(tag)

    if invalidTags:
        errorItems = ['{key}: {value}'.format(key=key, value=invalidTags.get(key)) for key in
                      invalidTags.keys()]
        errorItems.insert(0, 'The following Tags have invalid characters')
        if ignoreErrors:
            logging.warning('\n'.join(errorItems))
        else:
            logging.error('\n'.join(errorItems))
            raise ValueError('\n'.join(errorItems))

    return validTags


def createKnobs(node):
    """
    This will create the required knobs on the node if they are not yet present
    Args:
        node (nuke.Node): This is the node to add the knobs to

    Returns:
        nuke.String_Knob: This is the knob that the information will be stored on
    """

    tagTab = node.knob(Globals.tagTabName)
    if not tagTab:
        tagTab = nuke.Tab_Knob(Globals.tagTabName)
        tagTab.setFlag(nuke.INVISIBLE)
        node.addKnob(tagTab)

    tagKnob = node.knob(Globals.tagKnobName)
    if not tagKnob:
        tagKnob = nuke.String_Knob(Globals.tagKnobName)
        tagKnob.setFlag(nuke.INVISIBLE)
        node.addKnob(tagKnob)

    return tagKnob
