from PyQt5 import QtCore
import pandas as pd


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
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setData(self, index, any, role=QtCore.Qt.EditRole):
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        self._dataframe.iat[index.row(), index.column()] = any
        if index.row()+1 == self.rowCount():
            print("Trying to insert row")
            self.layoutAboutToBeChanged.emit()
            self.beginInsertRows(index, 1, 1)
            self._dataframe = self._dataframe.append(pd.Series(), ignore_index=True).copy(deep=False)
            print(self._dataframe)
            self.endInsertRows()
            self.layoutChanged.emit()
        self.dataChanged.emit(index,  index)
        self.layoutChanged.emit()
        # self._dataframe.reset_index(inplace=True, drop=True)
        print(self._dataframe)
        print()
        return True


    def roleNames(self):
        roles = {
            QtCore.Qt.DisplayRole: b'display',
            PandasModel.DtypeRole: b'dtype',
            PandasModel.ValueRole: b'value'
        }
        return roles