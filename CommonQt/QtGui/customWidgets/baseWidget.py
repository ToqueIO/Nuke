import logging

try:
    from PySide2 import QtWidgets as QtGui
except ImportError:
    from PySide import QtGui


class BaseWidget(QtGui.QWidget):
    def __init__(self):
        super(BaseWidget, self).__init__()

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
        """
        This is used to add all the widgets to the main layout and set all interface items. This
        must be overridden
        """
        raise NotImplementedError('This must be overridden to ensure proper initialization')

    def initializeDefaults(self):
        """
        This will set all the initial values for all the widgets and self.  This must be overridden
        """
        raise NotImplementedError('This must be overridden to ensure proper initialization')

    def initializeSignals(self):
        """
        This will connect all the signals for all widgets and self.  This must be overridden
        """
        raise NotImplementedError('This must be overridden to ensure proper initialization')

    def showEvent(self, event):
        """
        This is overridden to ensure that we initialize the widget before it is shown
        """
        if self.initialized is False:
            self.initialize()

        super(BaseWidget, self).showEvent(event)
