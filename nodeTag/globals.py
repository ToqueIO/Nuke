import re


class _Globals(object):
    """
    General globals to be used for the entire tag system
    """

    tagKnobName = 'nodeTags'
    tagTabName = 'nodeTagTab'
    tagSeparator = '|'
    potentialSeparators = [tagSeparator, ',', ' ', '\n']
    baseTagSearchRegEx = '[a-zA-Z0-9_-{0}]+'

    selectedIndex = 0
    tagSearchIndex = 1
    allNodesIndex = 2

    def __init__(self):
        super(_Globals, self).__init__()
        
        self._invalidCharacterFilter = None

    @property
    def invalidCharacterFilter(self):
        """
        Returns:
            re.Pattern: Compiled re pattern to limit the available characters to alphanumeric and _- characters
        """
        if self._invalidCharacterFilter is None:
            self._invalidCharacterFilter = re.compile('[^a-zA-Z0-9_-]+')

        return self._invalidCharacterFilter


Globals = _Globals()
