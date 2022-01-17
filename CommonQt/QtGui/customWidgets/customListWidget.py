try:
    from PySide2 import QtWidgets, QtGui, QtCore

    if hasattr(QtCore, 'QStringListModel'):
        QtGui.QStringListModel = QtCore.QStringListModel

except ImportError:
    from PySide import QtGui, QtCore
    QtWidgets = QtGui


class CustomListWidget(QtWidgets.QListWidget):

    actionSingle = 'single'
    actionMultiple = 'multiple'

    def __init__(self):
        super(CustomListWidget, self).__init__()

        self.menu = None
        self.menuActions = list()

        self.setUniformItemSizes(False)
        self.setSelectionMode(self.ExtendedSelection)
        self.setStyleSheet('QListWidget::item { border-bottom: 1px solid grey; } '
                           'QWidget:item:selected {background-color: '
                           'QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #148F77, '
                           'stop: 1 #0E6251);}}')

    @property
    def selectedWidgets(self):
        """
        Returns:
            list: All the currently selected widgets for the items
        """
        widgets = list()
        for index in self.selectedIndexes():
            widgets.append(self.itemWidget(self.item(index.row())))

        return widgets

    @property
    def widgets(self):
        """
        Returns:
            list: All the currently selected widgets for the items
        """
        widgets = list()
        for index in range(self.count()):
            widgets.append(self.itemWidget(self.item(index)))

        return widgets

    def clear(self):

        super(CustomListWidget, self).clear()

    def updateItemSize(self):
        """
        This is used to update the size of all the items in the event that there are dynamically
        sized items in the list
        """
        for row in range(self.count()):
            listWidgetItem = self.item(row)
            widget = self.itemWidget(listWidgetItem)
            listWidgetItem.setSizeHint(widget.sizeHint())

    def addWidget(self, widget):
        """
        This is a helper to directly add a widget to the list without needing to go through the
        process of creating the listWidgetItem
        Args:
            widget (QtWidgets.QWidget): This is the widget object to add

        Returns:
            QtWidgets.QListWidgetItem: This is the newly created list widget item with the given
                                       widget
        """
        if hasattr(widget, 'initialize'):
            if not getattr(widget, 'initialized', False):
                widget.initialize()

        listItem = QtWidgets.QListWidgetItem()
        listItem.setSizeHint(widget.sizeHint())

        self.addItem(listItem)
        self.setItemWidget(listItem, widget)

        return listItem

    def removeItems(self, rows):
        """
        This is a helper used to remove items from the list.  Given a list of rows this will remove
        each item on that row
        Args:
            rows (list(int)): This is a list of integers pertaining to the indexes of items to be
                              removed
        """
        for row in sorted(rows, reverse=True):
            self.removeItem(row)

    def removeItem(self, row):
        """
        This is a helper to remove an item from the list(self) at the given index
        Args:
            row (int): This is the index of the item to remove
        """
        self.model().removeRow(row)
        self.clearSelection()

    def addMenuItem(self, name, action, **kwargs):
        """
        This is used to add a menu item to the right click menu.  Selection type can be either
        single or multiple
        Args:
            name (str): This is the name for the menu item
            action (callable): This is the action that will be triggered by the menu item.  This
                               will have the row passed to it
        Kwargs:
            selectionType (int|optional): This is either single or multiple to determine the items
                                          that will pertain to the action
        """
        menuAction = QtWidgets.QAction(name, self)
        kwargs['action'] = action
        menuAction.setData(kwargs)
        self.menuActions.append(menuAction)

    def mousePressEvent(self, event):
        """
        This is overridden to add in a menu to allow for easy customization and additional actions
        to items in the list
        Args:
            event (QtGui.QMouseEvent): This is the QMouseEvent that triggered the method
        """

        # Collect the current item under the mouse
        pos = self.mapFromGlobal(QtGui.QCursor.pos())
        row = self.indexAt(pos).row()

        # If the event is not a button press then we just treat this as a regular event
        if not event.type() == QtCore.QEvent.MouseButtonPress:
            return super(CustomListWidget, self).mousePressEvent(event)

        # If the event is a right click then we will show our menu if there are any items
        if event.button() == QtCore.Qt.RightButton:
            if self.count() == 0:
                event.ignore()
                return

            # If there aren't and defined menu items then we ignore the event and return
            if not self.menuActions:
                event.ignore()
                return

            self.menu = QtWidgets.QMenu()
            self.setCurrentItem(self.item(row), QtCore.QItemSelectionModel.Current)
            self._populateMenuItems()
            action = self.menu.exec_(QtGui.QCursor.pos())
            if not action:
                event.ignore()
                return
            if action.data().get('selectionType', self.actionSingle) == self.actionSingle:
                rows = [row]
            else:
                rows = [index.row() for index in self.selectedIndexes()]

            # Call the action with the current rows
            action.data().get('action')(rows)
            return

        # Here we clear the selection if the user presses the left button
        elif event.button() == QtCore.Qt.LeftButton:
            if row < 0:
                self.clearSelection()
                event.ignore()
                return
            return super(CustomListWidget, self).mousePressEvent(event)
        else:
            event.ignore()

    def _populateMenuItems(self):
        """
        This will create and populate all the menu items for the right click menu.  Creating
        separate entries if there are any defined sub menus.
        """

        subMenus = dict()
        for menuAction in self.menuActions:
            subMenu = menuAction.data().get('subMenu', '')
            menuActions = subMenus.get(subMenu, list())
            menuActions.append(menuAction)
            subMenus[subMenu] = menuActions

        for subMenu, menuActions in subMenus.items():
            if subMenu:
                self.menu.addSection(subMenu)
            for menuAction in menuActions:
                self.menu.addAction(menuAction)