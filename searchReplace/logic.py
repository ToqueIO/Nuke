import fnmatch
import re
import common.utilities


matchColour = '#3aeb34'
replaceColour = '#34cdeb'


def getNodeInfo(nodes, search, replace, **kwargs):
    """
    Scans over all the nodes and will find which nodes have file knobs with strings that match the
    given search.  For all nodes that are found this will construct a dict as follows

    <nodeFullName>: in: formatted source value (html formatted with)
                    out: formatted output value (html formatted with)
                    matches: list(all of the matches found in the source)
    Args:
        nodes (set|list): iterator of all the nodes to process
        search (str): search string used to find matches
        replace (str): string to be used when processing replace

    kwargs:
        useRegex (bool|optional): True or False if the search is regex formatted
        caseSensitive (bool|optional): True of False if the search should be case-sensitive
    Returns:
        dict: Dictionary of all the nodes which have knobs that match the given search
    """
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
                                     'out': getFormattedText(knob.value(), matches, replace),
                                     'matches': matches}

        if nodeData:
            searchData[node.fullName()] = nodeData

    return searchData


def getMatches(text, searchString, **kwargs):
    """
    Checks the given text and finds all occurrences of the match in the text.

    Args:
        text (str): Text to search
        searchString (str): search to use when checking the text

    kwargs:
        useRegex (bool|optional): True or False if the search is regex formatted
        caseSensitive (bool|optional): True of False if the search should be case-sensitive


    Returns:

    """
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
    """
    Creates html formatted text.  This will highlight the matches in green if there are any.  If a
    replace is given then it will be highlighted in blue
    Args:
        text (str): base text that is to be formatted
        matches (list): Matches that are to be formatted in the text
        replace (str|optional): string that the matches are to be replaced with

    Returns:
        str: Html formatted string
    """
    for match in matches:
        if replace is None:
            replace = '<span style="color:{0}">{1}</span>'.format(matchColour, match)
        else:
            replace = '<span style="color:{0}">{1}</span>'.format(replaceColour, replace)
        text = text.replace(match, replace)

    return text


def replaceText(node, knob, matches, replace):
    """
    Takes all the matches and replaces the text on the given knob with the provided replacement
    Args:
        node (nuke.Node): Nuke node to process
        knob: (str): Knob name to do the replacement ont
        matches (list): List of all the matches to replace
        replace (str): string to replace all the matches with
    """
    value = node[knob].value()
    for match in matches:
        value = value.replace(match, replace)

    node[knob].setValue(value)
