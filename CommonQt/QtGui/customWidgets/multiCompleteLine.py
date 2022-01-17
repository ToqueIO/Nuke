import re
import logging

try:
    from PySide2 import QtWidgets, QtGui, QtCore

    if hasattr(QtCore, 'QStringListModel'):
        QtGui.QStringListModel = QtCore.QStringListModel

except ImportError:
    from PySide import QtGui, QtCore
    QtWidgets = QtGui


class MultiCompleteLine(QtWidgets.QLineEdit):
    """
    Kwargs:
        ignoreExisting (bool|optional): True or False is the completion is to ignore existing items
        escapeClear (bool|optional): True or False if the text should be cleared when the user
                                     presses escape
        separators (list(str)|optional): This is a list of characters to use as separators when
                                         determining the values of the lineEdit(self).  When this is
                                         set it will also override and reset the value of the
                                         completion addition
        completionAddition (str|optional): This is the value that will be added to each completion
                                           when it is activated
    """

    itemComplete = QtCore.Signal(str)
    actionReplace = 'replace'
    actionGet = 'get'

    def __init__(self,  **kwargs):
        super(MultiCompleteLine, self).__init__()

        self._completer = QtWidgets.QCompleter()
        self._completer.setWidget(self)
        # self._completer.activated.connect(self._insertCompletion)

        self.completerModel = QtGui.QStringListModel()
        self._completer.setModel(self.completerModel)

        self._keysToIgnore = [QtCore.Qt.Key_Enter,
                              QtCore.Qt.Key_Return,
                              QtCore.Qt.Key_Escape]

        self._completionValues = None
        self._completionAddition = None
        self._separators = None
        self._baseValidator = self.validator()

        self.ignoreExisting = kwargs.get('ignoreExisting', False)
        self.escapeClear = kwargs.get('escapeClear', False)
        self.separators = kwargs.get('separators', [' '])
        self.completionAddition = kwargs.get('completionAddition', None)

    @property
    def completionAddition(self):
        """
        Returns:
            str: This is the addition which is added after every completion
        """
        return self._completionAddition

    @completionAddition.setter
    def completionAddition(self, value):
        """
        This ensures that the given completion addition is included in the separators.  This is to
        ensure proper formatting of the text, so it may be properly parsed to extract the values
        Args:
            value (str): This is the string to add after each completion.
        """
        if value is None or re.search(self.separators, value):
            self._completionAddition = value
        else:
            raise ValueError('The given addition is invalid.  Please ensure that the addition is '
                             'included in the separators')

    @property
    def separators(self):
        """
        Returns:
            re.Pattern: This is the compiled regular expression used to separate out the values
        """
        return self._separators

    @separators.setter
    def separators(self, characters):
        """
        This ensures that the values set for the separators is properly formatted.  It will take the
        given list of characters and format them into an regular expression which will be used to
        separate out and parse the values

        In addition this will also update the completion addition to be a valid character from
        within the characters
        Args:
            characters (list): This is a list of characters that will be used as valid separators
        """
        formatted = list()
        for character in characters:
            if character == ' ':
                formatted.append(r'\s')
            else:
                formatted.append(character)

        self._separators = re.compile('[{characters}]'.format(characters=''.join(formatted)))
        self.completionAddition = formatted[0] if formatted[0] != r'\s' else ' '

    @property
    def values(self):
        """
        This will return all the values in the current lineEdit(self).  The values are determined
        by the current separators

        Returns:
            list: A list strings,  each of which is an item from the lineEdit(self)
        """
        values = re.split(self.separators, self.text())

        if self.completionAddition:
            values = [value.strip(self.completionAddition) for value in values]

        values = [str(value.strip(self.completionAddition)) for value in values if value]

        return values

    @property
    def textUnderCursor(self):
        """
        Returns:
            str: This is the text which is currently under the cursor
        """
        text = str(self.text())
        letters = list()
        cursorIndex = self.cursorPosition() - 1
        while cursorIndex >= 0:
            letters.insert(0, text[cursorIndex])
            cursorIndex -= 1
            if re.search(self.separators, text[cursorIndex]):
                break

        return ''.join(letters)

    def setCompletionValues(self, values, updateCache=True):
        """
        This is used to set the values that are to be used for the autocompletion
        Args:
            values (list(str)): This is a list of strings to be used for the autocompletion
            updateCache (bool|optional): True or False if the internal cache of completions is to be
                                         updated.  This is only used internally and set to false
                                         when we are limiting existing items
        """

        if not isinstance(values, list):
            values = list(values)
        if updateCache:
            self._completionValues = values
        self.completerModel.setStringList(values)

    def setRegEx(self, regex):
        """
        This is used to set the regex on self to determine which characters will be accepted
        Args:
            regex (str): This is a formatted regular expression to be used to filter characters on
                         self
        """
        regex = QtCore.QRegExp(regex)
        validator = QtGui.QRegExpValidator(regex, self)
        self.setValidator(validator)

    def removeRegEx(self):

        self.setValidator(self._baseValidator)

    def currentWordAction(self, action=None, currentIndex=None):

        action = action or self.actionGet
        currentIndex = currentIndex or self.cursorPosition()
        indexes = list()
        for index in reversed(range(currentIndex)):
            if re.search(self.separators, self.text()[index]):
                break
            indexes.append(index)

        for index in range(currentIndex, len(self.text())):
            if re.search(self.separators, self.text()[index]):
                break
            indexes.append(index)

        if not indexes:
            return ''

        indexes = sorted(indexes)
        currentWord = ''.join([self.text()[index] for index in indexes])

        if action == self.actionGet:
            return currentWord

        letters = list()
        for index, letter in enumerate(self.text()):
            if index in indexes:
                continue

            letters.append(letter)

        self.setText(''.join(letters))
        self.setCursorPosition(min(indexes))

        return currentWord

    def _insertCompletion(self, completion, replace=False):
        """
        This is the event handler for the QCompleter.activated(QString) signal,
        it is called when the user selects an item in the completer popup.
        """

        prefix = self._completer.completionPrefix()

        if prefix:
            completion = completion.split(prefix, 1)[-1]

        if replace:
            self.currentWordAction(action=self.actionReplace)

        if self.completionAddition and completion:
            completion += self.completionAddition

        self.insert(completion)
        cursorPosition = int(self.cursorPosition())
        separators = self.separators.findall(self.text())
        self.setText(re.sub(self.separators.pattern + '+', separators[0], self.text()))
        self.setCursorPosition(cursorPosition)

        self.itemComplete.emit(self.currentWordAction(action=self.actionGet,
                                                      currentIndex=cursorPosition - 2))

    def focusNextPrevChild(self, *args):
        return False

    def keyPressEvent(self, event):
        """
        This override ensures that certain key shortcuts activate/complete the completer in the way
        we want it to be

        The Up key will activate the completer if it is not yet shown.  If the completer is shown an
        the TAB key is pressed the completion will replace the current word where enter will just
        add

        If escapeClear is set then when escape is pressed it will clear the line

        Args:
            event (QtGui.QKeyEvent): This is the Key event which triggered the method
        Returns:
            None
        """

        key = str(event.text())
        if self._completer.popup().isVisible():

            if event.key() in [QtCore.Qt.Key_Tab, QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
                if not self._completer.popup().selectedIndexes():
                    event.ignore()
                    return

                replace = event.key() == QtCore.Qt.Key_Tab
                self.blockSignals(True)
                self._completer.blockSignals(True)
                self._insertCompletion(
                    completion=self._completer.popup().selectedIndexes()[0].data(), replace=replace)
                self._completer.popup().hide()
                self._completer.blockSignals(False)
                self.blockSignals(False)
                event.ignore()
                return
            if event.key() in self._keysToIgnore:
                event.ignore()
                return

        if event.key() not in [QtCore.Qt.Key_Tab]:
            super(MultiCompleteLine, self).keyPressEvent(event)

        if event.key() in [QtCore.Qt.Key_Down, QtCore.Qt.Key_Tab]:
            self.showCompleter('', prefix='', force=True)
        elif self.escapeClear and event.key() == QtCore.Qt.Key_Escape:
            self.setText('')
        else:
            self.showCompleter(event.text())

        if re.search(self.separators, key):
            if self.values:
                self.itemComplete.emit(self.values[-1])
            else:
                self.itemComplete.emit('')

    def showCompleter(self, text, prefix=None, force=False):
        """
        When triggered this will process and determine if the completer is to be shown and update
        the prefix if one is not provided.  If the completer is set to ignore existing completions
        then this will also limit the completions to items that have not yet already been entered

        Args:
            text (str): This is the entered text which triggered the completer
            prefix (str|None|optional): This is the prefix that is to be used for the completer.  If
                                        this is not provided then it will be collected based on the
                                        current cursor position
            force (bool|optional): True or False if we are to force the showing of the completer
        """
        if prefix is None:
            prefix = self.textUnderCursor

        values = self._completionValues or list()
        if self.ignoreExisting:
            values = [value for value in values if value not in self.values]
        self.setCompletionValues(values, updateCache=False)

        if prefix != self._completer.completionPrefix() or force:
            self._updateCompleterItems(prefix)

        # This ensures that the completer is shown when the user enters text
        if len(text) > 0 and len(prefix) > 0:
            self._completer.complete()

        if len(prefix) == 0 and force is False:
            self._completer.popup().hide()

        if force:
            if True:
                self._completer.popup().move(self.mapToGlobal(self.rect().bottomLeft()))
                self._completer.popup().setFixedWidth(self.width())
                self._completer.popup().adjustSize()
                self._completer.popup().show()

    def _updateCompleterItems(self, prefix):
        """
        This will ensure that the prefix is set correctly,  this is in the event that the given
        prefix is None or if the current prefix on the completer does not match the expected prefix
        """
        if prefix is None:
            logging.debug('No Prefix given.  Collecting prefix')
            self.cursorWordBackward(True)
            prefix = self.selectedText()
            cursorPos = self.cursorPosition()
            # Since we selected and marked text we need to de-select the text
            # The quickest way to clear selected text is to reset the text
            self.setText(self.text())
            # We need to add the len of the prefix or the cursor position is set incorrectly
            self.setCursorPosition(cursorPos + len(prefix))
            logging.debug('Prefix collected: {0}'.format(prefix))

        self._completer.setCompletionPrefix(prefix)
        self._completer.popup().setCurrentIndex(
                self._completer.completionModel().index(0, 0))
