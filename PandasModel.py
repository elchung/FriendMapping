from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd
# https://stackoverflow.com/questions/43915108/qtablewidget-insert-row-crashes-the-application-python


class PandasModel(QtCore.QAbstractTableModel):
    DtypeRole = QtCore.Qt.UserRole + 1000
    ValueRole = QtCore.Qt.UserRole + 1001

    def __init__(self, df=pd.DataFrame(), parent=None):
        super(PandasModel, self).__init__(parent)
        self._dataframe = df.copy(deep=False)
        # self.data_changed = QtCore.pyqtSignal(QtCore.QModelIndex, QtCore.QModelIndex)
        self.next_row_keys = [QtCore.Qt.Key_Down, QtCore.Qt.Key_Return]

    def setDataFrame(self, dataframe):
        self.beginResetModel()
        self._dataframe = dataframe.copy(deep=False)
        self.endResetModel()
        self.layoutchanged.emit()

    def dataFrame(self):
        return self._dataframe

    dataFrame = QtCore.pyqtProperty(pd.DataFrame, fget=dataFrame, fset=setDataFrame)

    @QtCore.pyqtSlot(int, QtCore.Qt.Orientation, result=str)
    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._dataframe.columns[section]
            else:
                return str(self._dataframe.index[section])
        return QtCore.QVariant()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._dataframe.index)  # not using shape due to len(index) having better performance

    def columnCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return self._dataframe.columns.size


    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount() and 0 <= index.column() < self.columnCount()):
            return QtCore.QVariant()
        row = self._dataframe.index[index.row()]
        col = self._dataframe.columns[index.column()]
        dt = self._dataframe[col].dtype

        val = self._dataframe.iloc[row][col]
        if role == QtCore.Qt.DisplayRole:
            return str(val)
        elif role == PandasModel.ValueRole:
            return val
        if role == PandasModel.DtypeRole:
            return dt
        return QtCore.QVariant()

    def flags(self, index):
        flags = QtCore.Qt.ItemIsDragEnabled
        flags |= QtCore.Qt.ItemIsDropEnabled
        flags |= QtCore.Qt.ItemIsEditable
        flags |= QtCore.Qt.ItemIsEnabled
        flags |= QtCore.Qt.ItemIsSelectable
        return flags

    def setData(self, index, any, role=QtCore.Qt.EditRole):
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        self._dataframe.iat[index.row(), index.column()] = any
        if index.row()+1 == self.rowCount():
            self.insertRow(self.rowCount(), index, pd.Series())
        self.dataChanged.emit(index,  index)
        self.layoutChanged.emit()
        return True

    def insertRow(self, p_int, parent=QtCore.QModelIndex(), *args, **kwargs):
        # data to insert should be in args, type pandas Series, dict, or list
        # https://stackoverflow.com/questions/15888648/is-it-possible-to-insert-a-row-at-an-arbitrary-position-in-a-dataframe-using-pan?rq=1
        # TODO: enable insertions not just at end of dataframe
        if p_int > self.rowCount():
            return False

        self.layoutAboutToBeChanged.emit()
        self.beginInsertRows(parent, p_int, p_int)
        if args:
            self._dataframe = self._dataframe.append(args[0], ignore_index=True)
        else:
            self._dataframe = self._dataframe.append(kwargs['data'], ignore_index=True)
        self.endInsertRows()
        self.layoutChanged.emit()
        return True

    def insertRows(self, p_int, p_int_1, parent=None, *args, **kwargs):
        # Data should be in list format, key worded 'data'
        # TODO enable row insertions not just at end of dataframe using concat?
        self.layoutAboutToBeChanged.emit()
        self.beginInsertRows(parent, p_int, p_int_1)
        for row in range(p_int_1-p_int+1):
            self.insertRow(p_int + row, data=kwargs['data'][row])
        self.endInsertRows()
        self.layoutChanged.emit()

    def removeRow(self, p_int, parent=None, *args, **kwargs):
        self.layoutAboutToBeChanged.emit()
        self.beginRemoveRows(parent, p_int, p_int)
        self._dataframe = self._dataframe.drop(self._dataframe.index[p_int])
        self.endRemoveRows()
        self.layoutChanged.emit()

    def removeRows(self, p_int, p_int_1, parent=QtCore.QModelIndex(), *args, **kwargs):
        self.layoutAboutToBeChanged.emit()
        self.beginRemoveRows(parent, p_int, p_int_1)
        self._dataframe = self._dataframe.drop([p_int, p_int_1])
        self.endRemoveRows()
        self.layoutChanged.emit()

    def roleNames(self):
        roles = {
            QtCore.Qt.DisplayRole: b'display',
            PandasModel.DtypeRole: b'dtype',
            PandasModel.ValueRole: b'value'
        }
        return roles

# class cellValidationDelegate(QtGui.QItemDelegate):
#     def __init__(self, parent=None):
#         super(cellValidationDelegate, self).__init__(parent)
#         self.setWindowFlags(QtCore.Qt.Popup)
#
#
#     def createEditor(self, parent, option, index):
#         return QtGui.QDoubleSpinBox(parent)

class ComboDelegate(QtWidgets.QAbstractItemDelegate):
    editorItems=['Combo_Zero', 'Combo_One','Combo_Two']
    height = 25
    width = 200
    def createEditor(self, parent, option, index):
        editor = QtWidgets.QListWidget(parent)
        # editor.addItems(self.editorItems)
        # editor.setEditable(True)
        editor.currentItemChanged.connect(self.currentItemChanged)
        return editor

    def setEditorData(self,editor,index):
        z = 0
        for item in self.editorItems:
            ai = QtWidgets.QListWidgetItem(item)
            editor.addItem(ai)
            if item == index.data():
                editor.setCurrentItem(editor.item(z))
            z += 1
        editor.setGeometry(0,index.row()*self.height,self.width,self.height*len(self.editorItems))

    def setModelData(self, editor, model, index):
        editorIndex=editor.currentIndex()
        text=editor.currentItem().text()
        model.setData(index, text)
        # print '\t\t\t ...setModelData() 1', text

    def currentItemChanged(self):
        self.commitData.emit(self.sender())