import fnmatch
import re
import common.utilities


matchColour = '#3aeb34'
replaceColour = '#34cdeb'


def getNodeInfo(nodes, search, replace, **kwargs):

    searchData = dict()
    for node in nodes:
        nodeData = dict()
        fileKnobs = common.utilities.getFileKnobs(node)
        if not fileKnobs:
            continue

        for knob in fileKnobs:
            matches = getMatches(knob.value(), search, **kwargs)
            if not matches:
                continue

            source = getFormattedText(knob.value(), matches)
            nodeData[knob.name()] = {'in': source,
                                     'out': getFormattedText(knob.value(), matches, replace) if replace else source,
                                     'matches': matches}

        if nodeData:
            searchData[node.fullName()] = nodeData

    return searchData


def getMatches(text, searchString, **kwargs):

    useRegex = kwargs.get('useRegex', False)
    caseSensitive = kwargs.get('caseSensitive', False)
    if not useRegex:
        searchString = fnmatch.translate(searchString).strip('\\Z')
    try:
        if caseSensitive:
            search = re.compile(searchString)
        else:
            search = re.compile(searchString, flags=re.IGNORECASE)
    except re.error:
        return getMatches(text, searchString, useRegex=False, caseSensitive=caseSensitive)

    result = re.findall(search, text)
    return result


def getFormattedText(text, matches, replace=None):

    for match in matches:
        if replace:
            replace = '<span style="color:{0}">{1}</span>'.format(replaceColour, replace)
        else:
            replace = '<span style="color:{0}">{1}</span>'.format(matchColour, match)
        text = text.replace(match, replace)

    return text


def replaceText(node, knob, matches, replace):

    value = node[knob].value()
    for match in matches:
        value = value.replace(match, replace)

    node[knob].setValue(value)
