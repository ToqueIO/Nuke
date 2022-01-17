try:
    from PySide2 import QtWidgets as QtGui
except ImportError:
    from PySide import QtGui


class LabeledWidget(QtGui.QWidget):
    """
    This is a convenience widget that is used to add a label to a knob.  It has the ability to
    position the label either before, after, above, or below the given widget
    """
    Before = 'before'
    After = 'after'
    Above = 'above'
    Below = 'below'
    Middle = 'middle'

    __indexPositions = {Before: 0,
                        After: 2,
                        Middle: 1,
                        Above: 0,
                        Below: 2}

    def __init__(self, label, widget, **kwargs):
        """
        Args:
            label (str): This is the text to use for the label
            widget (QtGui.QWidget): This is the widget to use the label for and can be any widget
                                    type
        Kwargs:
            orientation (str|optional): This is the orientation for the label position.  This can
                                        be either above, below before or after
            stretchPosition (str|optional): This is the position for the stretch if one is to be
                                            added.  This can be before, after, or middle
        """
        super(LabeledWidget, self).__init__()

        self.orientation = kwargs.get('orientation', self.Before)
        self.stretchPosition = kwargs.get('stretchPosition', None)
        self.label = QtGui.QLabel(label)
        self.baseWidget = widget

        self.masterLayout = None
        self.__initialized = False

    def initialize(self):
        """
        This is called when the widget is shown, it processes the kwargs to ensure that the label is
        positioned correctly. This can be either above, below, before or after the given widget.  If
        defined this will also add a stretch to the layout
        """
        if self.orientation in [self.Before, self.After]:
            self.masterLayout = QtGui.QHBoxLayout()
        else:
            self.masterLayout = QtGui.QVBoxLayout()

        items = [self.baseWidget]

        if self.orientation in [self.Before, self.Above]:
            items.insert(0, self.label)
        else:
            items.append(self.label)

        print(items)

        if self.stretchPosition is not None:
            items.insert(self.__indexPositions.get(self.stretchPosition, 2), 'stretch')

        for item in items:
            print(item)
            if isinstance(item, str):
                self.masterLayout.addStretch(0)
                continue
            self.masterLayout.addWidget(item)

        self.setLayout(self.masterLayout)
        self.__initialized = True

    def showEvent(self, event):
        """
        This is overridden to ensure that we initialize the widget before it is shown
        Args:
            event (QtGui.QShowEvent):
        """
        if self.__initialized is False:
            self.initialize()
        super(LabeledWidget, self).showEvent(event)

