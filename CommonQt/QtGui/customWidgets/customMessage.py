import logging

try:
    from PySide2 import QtWidgets, QtGui, QtCore, QtSvg

    if hasattr(QtCore, 'QStringListModel'):
        QtGui.QStringListModel = QtCore.QStringListModel

except ImportError:
    from PySide import QtGui, QtCore
    QtWidgets = QtGui

from ..icons import warning, info, critical, question


class CustomMessage(QtWidgets.QDialog):

    Declined = False

    warning = warning
    info = info
    question = question
    critical = critical
    messageTypes = [info, question, critical, warning]

    def __init__(self, title, **kwargs):
        super(CustomMessage, self).__init__()

        self.masterLayout = QtWidgets.QVBoxLayout()
        self.infoLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout = QtWidgets.QHBoxLayout()

        self.titleLabel = QtWidgets.QLabel()
        self.iconLabel = QtSvg.QSvgWidget()
        self.messageBox = QtWidgets.QTextEdit()
        self.acceptButton = QtWidgets.QPushButton('Accept')
        self.declineButton = QtWidgets.QPushButton('Cancel')

        self.title = title
        self.messageType = kwargs.get('messageType', self.info)
        self.message = kwargs.get('message', None)
        self.initialized = False

    def initialize(self):
        """
        This is used to initialize the widget (self) by calling all the individual initialization
        methods
        """
        logging.info('Starting initialization of widget')
        logging.info('Initializing interface')
        self.initializeInterface()
        logging.info('Interface initialized')
        logging.info('Initializing defaults')
        self.initializeDefaults()
        logging.info('Defaults initialized')
        logging.info('Initializing signals')
        self.initializeSignals()
        logging.info('Signals initialized')
        self.initialized = True
        logging.info('Initialization of widget complete')

    def initializeInterface(self):
        self.masterLayout.addLayout(self.infoLayout)
        self.masterLayout.addWidget(self.messageBox)
        self.masterLayout.addStretch(0)
        self.masterLayout.addLayout(self.buttonLayout)

        self.infoLayout.addWidget(self.titleLabel)
        self.infoLayout.addStretch(0)
        self.infoLayout.addWidget(self.iconLabel)

        self.buttonLayout.addStretch(0)
        self.buttonLayout.addWidget(self.acceptButton)
        self.buttonLayout.addWidget(self.declineButton)

        self.setLayout(self.masterLayout)

    def initializeDefaults(self):

        self.setMessageType(self.messageType)
        self.titleLabel.setText(self.title)
        titleFont = QtGui.QFont("consolas", 12, QtGui.QFont.Bold)
        self.titleLabel.setFont(titleFont)

        self.setFixedWidth(400)

        self.messageBox.setVisible(False)
        if self.message:
            self.setMessage(self.message)

    def initializeSignals(self):

        self.acceptButton.pressed.connect(self.accept)
        self.declineButton.pressed.connect(self.decline)

    def setTitle(self, title):

        self.title = title
        self.titleLabel.setText(self.title)

    def setMessage(self, message):

        self.message = message
        self.messageBox.setVisible(True)
        self.messageBox.setText(self.message)
        self.messageBox.setReadOnly(True)

    def setMessageType(self, messageType):

        if isinstance(messageType, str):
            messageType = getattr(self, messageType)

        if messageType not in self.messageTypes:
            raise TypeError('Invalid type given.  Type must be either\n'
                            'CustomMessage.info\n'
                            'CustomMessage.question\n'
                            'CustomMessage.warning\n'
                            'CustomMessage.critical'
                            '')

        if messageType == self.question:
            self.declineButton.setVisible(True)
        else:
            self.declineButton.setVisible(False)

        self.messageType = messageType
        self.iconLabel.load(self.messageType)
        self.iconLabel.setFixedSize(64, 64)

    def accept(self):
        self.done(self.Accepted)

    def decline(self):
        self.done(self.Declined)

    def showEvent(self, event):
        """
        This is overridden to ensure that we initialize the widget before it is shown
        """
        if self.initialized is False:
            self.initialize()

        super(CustomMessage, self).showEvent(event)
        self.adjustSize()

    def show(self):
        if self.messageType == self.question:
            return super(CustomMessage, self).exec_()
        else:
            return super(CustomMessage, self).show()
