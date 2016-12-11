from PyQt5 import QtCore, QtGui
import sys
from ui_functions.rominfo_class import *
from PIL.ImageQt import ImageQt

# the root is defined in ImageEditor.py
# the rom is defined in the rom_api.py


class Node(object):
    def __init__(self, id, parent=None):

        self._id = id
        self.name = ""
        self._children = []
        self._parent = parent
        self.image = None

        if parent is not None:
            parent.addChild(self)

    def typeInfo(self):
        return "NODE"

    def addChild(self, child):
        self._children.append(child)

    def insertChild(self, position, child):

        if position < 0 or position > len(self._children):
            return False

        self._children.insert(position, child)
        child._parent = self
        return True

    def removeChild(self, position):

        if position < 0 or position > len(self._children):
            return False

        child = self._children.pop(position)
        child._parent = None

        return True

    def setName(self, name):
        self._name = name

    def child(self, row):
        return self._children[row]

    def childCount(self):
        return len(self._children)

    def parent(self):
        return self._parent

    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)

    def log(self, tabLevel=-1):

        output = ""
        tabLevel += 1

        for i in range(tabLevel):
            output += "\t"

        output += "|------" + self._name + "\n"

        for child in self._children:
            output += child.log(tabLevel)

        tabLevel -= 1
        output += "\n"

        return output

    def __repr__(self):
        return self.log()

    def getId(self):
        return self._id

    def setId(self, val):
        self._id = val


class TableNode(Node):
    def __init__(self, id, parent=None):
        super(TableNode, self).__init__(id, parent)
        self.name = "Table "

    def typeInfo(self):
        return "table_node"


class OWNode(Node):
    def __init__(self, id, parent=None):
        super(OWNode, self).__init__(id, parent)
        self.name = "Overworld "
        self.frames = 0

        if parent is not None:
            self.setInfo()

    def typeInfo(self):
        return "ow_node"

    def setInfo(self):
        table_id = self._parent.getId()
        ow_id = self._id

        self.image = ImageManager().get_ow_frame(ow_id, table_id, 0)
        self.frames = root.tables_list[table_id].ow_data_pointers[ow_id].frames.get_num()


class TreeViewModel(QtCore.QAbstractItemModel):
    """INPUTS: Node, QObject"""

    def __init__(self, model_root, parent=None):
        super(TreeViewModel, self).__init__(parent)
        self._rootNode = model_root

        global root

        for table in range(len(root.tables_list)):
            # add the table nodes
            newTableNode = TableNode(table, self._rootNode)

            for ow in range(len(root.tables_list[table].ow_data_pointers)):
                # add the ow nodes
                newOWNode = OWNode(ow, newTableNode)


    """INPUTS: QModelIndex"""
    """OUTPUT: int"""

    def rowCount(self, parent):
        if not parent.isValid():
            parentNode = self._rootNode
        else:
            parentNode = parent.internalPointer()

        return parentNode.childCount()

    """INPUTS: QModelIndex"""
    """OUTPUT: int"""

    def columnCount(self, parent):
        return 3

    """INPUTS: QModelIndex, int"""
    """OUTPUT: QVariant, strings are cast to QString which is a QVariant"""

    def data(self, index, role):

        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if index.column() == 0:
                return node.name + str(node.getId())
            elif index.column() == 2:
                global root

                if isinstance(node, OWNode):
                    return node.frames

                return None

        if role == QtCore.Qt.DecorationRole:
            if index.column() == 1:
                typeInfo = node.typeInfo()

                if typeInfo == "ow_node":
                    return QtGui.QIcon(QtGui.QPixmap.fromImage(ImageQt(node.image)))

                '''
                if typeInfo == "TRANSFORM":
                    return QtGui.QIcon(QtGui.QPixmap(":/Transform.png"))

                if typeInfo == "CAMERA":
                    return QtGui.QIcon(QtGui.QPixmap(":/Camera.png"))
                '''


    """INPUTS: QModelIndex, QVariant, int (flag)"""

    def setData(self, index, value, role=QtCore.Qt.EditRole):

        if index.isValid():

            node = index.internalPointer()

            # For the OWs
            if node.typeInfo() == "ow_node":
                if value is not None:
                    node.setId(value)
                else:
                    node.setInfo()

            # For the Tables
            if node.typeInfo() == "table_node":
                node.setId(value)

            return True

        return False

    """INPUTS: int, Qt::Orientation, int"""
    """OUTPUT: QVariant, strings are cast to QString which is a QVariant"""

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if section == 0:
                return "OWs Structure"
            elif section == 1:
                return "Preview"
            elif section == 2:
                return "Frames"

    """INPUTS: QModelIndex"""
    """OUTPUT: int (flag)"""

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    """INPUTS: QModelIndex"""
    """OUTPUT: QModelIndex"""
    """Should return the parent of the node with the given QModelIndex"""

    def parent(self, index):

        node = self.getNode(index)
        parentNode = node.parent()

        if parentNode == self._rootNode:
            return QtCore.QModelIndex()

        return self.createIndex(parentNode.row(), 0, parentNode)

    """INPUTS: int, int, QModelIndex"""
    """OUTPUT: QModelIndex"""
    """Should return a QModelIndex that corresponds to the given row, column and parent node"""

    def index(self, row, column, parent):

        parentNode = self.getNode(parent)

        childItem = parentNode.child(row)

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    """CUSTOM"""
    """INPUTS: QModelIndex"""

    def getNode(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node

        return self._rootNode

    """INPUTS: int, int, QModelIndex"""

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):

        parentNode = self.getNode(parent)

        self.beginInsertRows(parent, position, position + rows - 1)
        childCount = parentNode.childCount()

        for row in range(rows):

            if parentNode.typeInfo() == "table_node":
                # Adding OWs
                childNode = OWNode(position + row)
                success = parentNode.insertChild(position + row, childNode)
                # Re-init the node, so it loads the frame
                self.setData(self.index(row + position, 0, parent), None)
            if parentNode.typeInfo() == "NODE":
                childNode = TableNode(childCount)
                success = parentNode.insertChild(childCount, childNode)

        # Only for the OWs, increase the name Id by one, in case an OW was INSERTED
        if parentNode.typeInfo() == "table_node":
            for row in range(position + rows, childCount + rows):
                self.setData(self.index(row, 0, parent), row)

        self.endInsertRows()

        return success

    """INPUTS: int, int, QModelIndex"""

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):

        parentNode = self.getNode(parent)
        self.beginRemoveRows(parent, position, position + rows - 1)

        for row in range(rows):
            success = parentNode.removeChild(position)

            if parentNode.typeInfo() == "table_node":
                #remove OW
                root.tables_list[parentNode.getId()].remove_ow(position)
            elif parentNode.typeInfo() == "NODE":
                root.remove_table(position)

        for row in range(position, parentNode.childCount()):
            self.setData(self.index(row, 0, parent), row)

        self.endRemoveRows()

        return success

    # OW/Table interacting functionsqt c

    def insertOWs(self, ow_id, table_id, rows, ow_type, num_of_frames):

        parent = self.index(table_id, 0, QtCore.QModelIndex())
        parentNode = self.getNode(parent)

        for ow in range(rows):
            if ow_id == -1:
                ow_id = parentNode.childCount()
                root.tables_list[parentNode.getId()].add_ow(ow_type, num_of_frames)
            else:
                root.tables_list[parentNode.getId()].insert_ow(ow_id, ow_type, num_of_frames)

        self.insertRows(ow_id, rows, parent)

    def removeOWs(self, ow_id, table_id, rows):
        tableNode = self.index(table_id, 0, QtCore.QModelIndex())
        self.removeRows(ow_id, rows, tableNode)

    def resizeOW(self, ow_id, table_id, ow_type, num_of_frames):

        root.tables_list[table_id].resize_ow(ow_id, ow_type, num_of_frames)
        tableNode = self.index(table_id, 0, QtCore.QModelIndex())
        owNode = self.index(ow_id, 0, tableNode)
        self.setData(owNode, None)

    def insertTable(self, ow_pointers, data_pointers, frames_pointers, frames_address):
        parent = QtCore.QModelIndex()
        parentNode = self.getNode(parent)

        root.custom_table_import(ow_pointers, data_pointers, frames_pointers, frames_address)
        self.insertRows(-1, 1, parent)

    def removeTable(self, table_id):
        self.removeRows(table_id, 1, QtCore.QModelIndex())