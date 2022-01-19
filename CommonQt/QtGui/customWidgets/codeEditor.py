import itertools
import time
import os.path
import re
import sys
import traceback

try:
    from StringIO import StringIO
except (ImportError, ModuleNotFoundError):
    from io import StringIO

try:
    from PySide2 import QtWidgets, QtGui, QtCore
except ImportError:
    from PySide import QtGui, QtCore


class NumberBar(QtWidgets.QWidget):
    def __init__(self, editor):
        super(NumberBar, self).__init__(editor)
        self.editor = editor
        self.setStyleSheet("text-align: center;")

    def sizeHint(self):
        return QtCore.QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QtWidgets.QPlainTextEdit):

    clearOutputRequested = QtCore.Signal()
    runCodeRequested = QtCore.Signal()

    codeSaveName = 'customAction.py'
    escapeCharacters = [b'\n', b'\t', b'\r', b'\b', b'\f', b'\'', b'\"', b'\\', b'\v']

    def __init__(self, **kwargs):
        super(CodeEditor, self).__init__()

        self.saveDir = kwargs.get('saveDir', None)
        self.saveLog = kwargs.get('saveLog', False)
        self.saveCode = kwargs.get('saveCode', False)
        self.defaultCode = kwargs.get('defaultCode', None)

        self.lineNumberArea = NumberBar(self)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.updateLineNumberAreaWidth()
        self.highlightCurrentLine()

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.initialized = False

    @property
    def logSaveName(self):
        """
        Returns:
            str: Dated and times name for saving out the log of the run code
                 ie: log/%m.%d.%Y-%H.%M.%S.log
        """
        return time.strftime('log/%m.%d.%Y-%H.%M.%S.log')

    def lineNumberAreaPaintEvent(self, event):

        if self.isReadOnly():
            return

        painter = QtGui.QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QtGui.QColor(36, 36, 36))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        currentLine = self.document().findBlock(self.textCursor().position()).blockNumber()
        painter.setPen(self.palette().color(QtGui.QPalette.Text))

        painterFont = QtGui.QFont()
        painterFont.setStyleHint(QtGui.QFont.Monospace)
        painterFont.setFixedPitch(True)

        while block.isValid() and top <= event.rect().bottom():

            textColour = QtGui.QColor(110, 110, 110)
            if blockNumber == currentLine and self.hasFocus():
                textColour = QtGui.QColor(255, 170, 0)

            painter.setPen(textColour)

            number = str(blockNumber + 1)
            painter.drawText(-3, top, self.lineNumberArea.width(),
                             self.fontMetrics().height(),
                             QtCore.Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def lineNumberAreaWidth(self):
        """
        Determines the width to use for the line numbers sidebar
        Returns:
            int: width of the line number sidebar
        """
        digits = 1
        maxNum = max(1, self.blockCount())
        while maxNum >= 10:
            maxNum /= 10
            digits += 1

        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def resizeEvent(self, event):
        """
        Update the line number area so that it matches the size of the editor
        """
        super(CodeEditor, self).resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(
            QtCore.QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def updateLineNumberAreaWidth(self, *args):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def highlightCurrentLine(self):
        """
        Highlights the current line under the cursor
        """
        extraSelections = []
        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            lineColor = QtGui.QColor(QtCore.Qt.gray)
            lineColor.setAlpha(50)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def highlightErrorLine(self, line):
        """
        Highlights the given line number in red
        Args:
            line (int): Line number that is to be highlighted
        """
        cursor = QtGui.QTextCursor(self.document().findBlockByLineNumber(line))
        self.setTextCursor(cursor)
        extraSelections = []
        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            lineColor = QtGui.QColor(QtCore.Qt.red)
            lineColor.setAlpha(50)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def selectedText(self):
        """
        Returns:
            str: The text currently selected in the editor
        """
        selectedText = self.textCursor().selectedText()
        if not selectedText:
            return ''
        lines = selectedText.splitlines()
        text = '\n'.join(lines)

        # Fix syntax error if last line is a comment with no new line
        if not text.endswith('\n'):
            text = text + '\n'

        return text

    def getSelectedLineNumber(self):
        """
        If there is selected text this will collect and return the line number for the first line
        of the selected text.  If there is no selected text then 0 will be returned
        Returns:
            int:  The first line for the currently selected text or 0
        """
        if not self.selectedText():
            return 0
        preBlock, _ = self.toPlainText().split(self.selectedText(), 1)
        return len(preBlock.split('\n')) - 1

    def runCode(self, selected=False, globalAttrs=None):
        """
        Runs the code in the current editor,  This will run it in a try/except and save out the
        output if set to do so.

        Either the error log or the output will be returned.  In the event of an error that line
        will be highlighted in the editor
        Args:
            selected (bool|optional): True or False if only the selected code should be executed
            globalAttrs (dict|optional): Dictionary of globals to have included in the environment
                                         when the code is executed

        Returns:
            str: The output of the code execution
        """
        globalAttrs = globalAttrs or globals()
        if selected:
            text = self.selectedText() or self.toPlainText()
            lineNumber = self.getSelectedLineNumber()
        else:
            text = self.toPlainText()
            lineNumber = 0

        print('line:', lineNumber)
        error = False
        currentOutput = sys.stdout

        try:
            executionMode = 'exec'
            if text.count('\n') == 1:
                executionMode = 'single'

            compiled = compile(text, 'CustomAction', executionMode)

            stdout = StringIO()
            sys.stdout = stdout
            exec(compiled, globalAttrs)
            output = 'Result:\n{0}'.format(stdout.getvalue())

        except Exception:
            error = True
            errors = traceback.format_exc().split('\n')
            del errors[1:3]

            formattedLines = list()
            foundLine = False
            for line in reversed(errors):
                if not foundLine:
                    search = re.search('File "CustomAction", line (\d+)', line)
                    if search:

                        lineNumber += int(search.groups()[0]) - 1
                        line = re.sub('File "CustomAction", line (\d+)',
                                      'File "CustomAction", line {0}'.format(lineNumber + 1),
                                      line)
                formattedLines.append(line)

            output = '\n'.join(reversed(formattedLines))

        finally:
            sys.stdout = currentOutput

        if self.saveLog:
            self.saveData(self.logSaveName, output)

        if error and isinstance(lineNumber, int):
            self.highlightErrorLine(lineNumber)

        return output

    def saveData(self, basename, data):
        """
        Saves out the given data to the specified save dir for this instance.  If no save dir has
        been set then nothing is saved
        Args:
            basename (str): basename for the file to save the data to
            data (str): Data to be saved out
        """
        if not self.saveDir:
            return

        savePath = os.path.join(self.saveDir, basename).replace('\\', '/')

        if not os.path.exists(os.path.dirname(savePath)):
            os.makedirs(os.path.dirname(savePath))

        with open(savePath, 'w') as saveFile:
            saveFile.write(data)

    def loadData(self, basename):
        """
        Loads data for the given basename.  This will collect this from the save dir specified for
        the current instance
        Args:
            basename (str): basename for the file to load the data from

        Returns:
            str: Data that has been loaded
        """
        loadPath = os.path.join(self.saveDir, basename).replace('\\', '/')
        if not os.path.exists(loadPath):
            return

        with open(loadPath, 'r') as saveFile:
            data = saveFile.read()

        if data and isinstance(data, str):
            self.setPlainText(data)

        return data
    
    def focusOutEvent(self, event):
        """
        Triggers the save of the current text in the editor
        """
        if self.saveCode:
            self.saveData(self.codeSaveName, self.toPlainText())
        super(CodeEditor, self).focusOutEvent(event)

    def keyPressEvent(self, event):
        """
        Add in some keyboard shortcuts for the editor

        Ctrl+Backspace: emits signal to clear output
        Ctrl+Enter: Emits signal to run code
        Ctrl+L: Open the log dir
        """
        ctrlToggled = event.modifiers() == QtCore.Qt.ControlModifier
        # altToggled = event.modifiers() == QtCore.Qt.AltModifier
        # shiftToggled = event.modifiers() == QtCore.Qt.ShiftModifier
        key = event.key()

        if ctrlToggled:
            if key in [QtCore.Qt.Key_Backspace]:
                self.clearOutputRequested.emit()
                return
            elif key in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
                self.runCodeRequested.emit()

            elif key in [QtCore.Qt.Key_L]:
                self.openLogDir()

        super(CodeEditor, self).keyPressEvent(event)

    def setToolTip(self, toolTip):
        """
        Override for setTooltip to ensure that we add in our shortcuts to the tooltip no matter what
        the user has set it to
        Args:
            toolTip (str): Tooltip to set
        """
        toolTip += ('\n\nShortcuts:\n'
                    'Ctrl+Backspace: emits signal to clear output\n'
                    'Ctrl+Enter: Emits signal to run code\n'
                    'Ctrl+L: Open the log dir')
        super(CodeEditor, self).setToolTip(toolTip)

    def openLogDir(self):
        """
        Opens the log dir for the current instance
        """
        logPath = os.path.dirname(os.path.join(self.saveDir, self.logSaveName)).replace('\\', '/')
        os.startfile(logPath, 'open')

    def showEvent(self, event):
        """
        Override to ensure that the initialization is run on startup.  This will also load any
        previous code if there is any present
        """
        if not self.initialized:
            if self.saveDir:
                self.loadData(self.codeSaveName)
            if not self.toPlainText() and self.defaultCode:
                self.setPlainText(self.defaultCode)
            self.initialized = True

        super(CodeEditor, self).showEvent(event)
