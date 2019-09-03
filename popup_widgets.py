from PyQt5 import QtWidgets, QtGui
from geo import Geo
import datetime

class Ui_SetHomeWidget(QtWidgets.QDialog):
    def __init__(self):
        # in: options is type(list) of names for each option to input
        QtWidgets.QDialog.__init__(self)
        self.obj_list = []  # storage for dynamic variables since can't name them all..# .
        self.info = {}
        self.geo_locator = Geo()
        self.setupUi()

    def setupUi(self):
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(5)
        double_validator = QtGui.QDoubleValidator()

        self.city_label = QtWidgets.QLabel("Address (City, state, address, etc")
        self.address_input = QtWidgets.QLineEdit()
        grid.addWidget(self.city_label, 1, 0)
        grid.addWidget(self.address_input, 1, 1)

        self.lat_label = QtWidgets.QLabel("Latitude:")
        self.lat_input = QtWidgets.QLineEdit()
        grid.addWidget(self.lat_label, 2, 0)
        grid.addWidget(self.lat_input, 2, 1)
        self.lat_input.setValidator(double_validator)

        self.lon_label = QtWidgets.QLabel("City:")
        self.lon_input = QtWidgets.QLineEdit()
        grid.addWidget(self.lon_label, 3, 0)
        grid.addWidget(self.lon_input, 3, 1)
        self.lon_input.setValidator(double_validator)

        self.address_input.editingFinished.connect(self.address_event)
        self.lat_input.editingFinished.connect(self.lat_lon_event)
        self.lon_input.editingFinished.connect(self.lat_lon_event)
        self.double_only = QtGui.QDoubleValidator()
        self.lat_input.setValidator(self.double_only)
        self.lon_input.setValidator(self.double_only)
        self.buttons = QtWidgets.QDialogButtonBox()
        self.buttons.addButton("Submit", QtWidgets.QDialogButtonBox.AcceptRole)
        self.buttons.addButton("Cancel", QtWidgets.QDialogButtonBox.RejectRole)
        grid.addWidget(self.buttons)
        self.setLayout(grid)
        # self.setGeometry(300, 300, 300, 300)
        self.setWindowTitle("Enter Information")
        self.buttons.accepted.connect(self.submit_close)
        self.buttons.rejected.connect(self.reject)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())


        self.show()

    def address_event(self):
        if not self.address_input.text():
            return
        lat, lon = self.geo_locator.address_to_lat_lon(self.address_input.text())
        if lat:
            self.lat_input.setText(lat)  # prevents none return from wiping text
        if lon:
            self.lon_input.setText(lon)

    def lat_lon_event(self):
        if not self.lat_input.text() or not self.lon_input.text():
            return
        address = self.geo_locator.lat_lon_to_address(float(self.lat_input.text()), float(self.lon_input.text()))
        if address:
            self.address_input.setText(address)

    def submit_close(self):
        self.info['city'] = self.address_input.text()
        self.info['lat'] = float(self.lat_input.text())
        self.info['lon'] = float(self.lon_input.text())
        self.accept()

    def exec_(self):
        super(Ui_SetHomeWidget, self).exec_()
        return self.info


class Ui_AddPersonWidget(QtWidgets.QDialog):
    def __init__(self, options):
        # in: options is type(list) of names for each option to input
        QtWidgets.QDialog.__init__(self)
        self.obj_list = []  # storage for dynamic variables since can't name them all..# .
        self.info = {}
        self.options = options
        self.setupUi()
        self.address_input = self.obj_list[2*self.options.index('Address')+1]
        self.lat_input = self.obj_list[2*self.options.index('Lat')+1]
        self.lon_input = self.obj_list[2*self.options.index('Lon')+1]
        self.geo_locator = Geo()

        self.address_input.editingFinished.connect(self.address_event)
        self.lat_input.editingFinished.connect(self.lat_lon_event)
        self.lon_input.editingFinished.connect(self.lat_lon_event)

    def setupUi(self):
        y_cnt = 1
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(5)
        for i in self.options:
            name = QtWidgets.QLabel(i)
            user_input = QtWidgets.QLineEdit()
            if name.text().lower() == 'date added':
                user_input.setText(datetime.date.today().strftime("%B %d, %Y"))
            self.obj_list.append(name)
            self.obj_list.append(user_input)
            grid.addWidget(name, y_cnt, 0)
            grid.addWidget(user_input, y_cnt, 1)
            y_cnt += 1


        self.buttons = QtWidgets.QDialogButtonBox()
        self.buttons.addButton("Submit", QtWidgets.QDialogButtonBox.AcceptRole)
        self.buttons.addButton("Cancel", QtWidgets.QDialogButtonBox.RejectRole)
        grid.addWidget(self.buttons)
        self.setLayout(grid)
        self.setGeometry(300, 300, 100 * y_cnt, 300)
        self.setWindowTitle("Enter Information")
        self.buttons.accepted.connect(self.submit_close)
        self.buttons.rejected.connect(self.reject)
        self.show()

    def address_event(self):
        if not self.address_input.text():
            return
        try:
            lat, lon = self.geo_locator.address_to_lat_lon(self.address_input.text())
        except TypeError:
            print("error, address not recognized, please check spelling")
            return
        self.obj_list[2*self.options.index('Lat')+1].setText(str(lat))
        self.obj_list[2*self.options.index('Lon')+1].setText(str(lon))

    def lat_lon_event(self):
        lat, lon = self._get_lat_lon()
        if not lat or not lon:
            return
        address = self.geo_locator.lat_lon_to_address(lat, lon)
        self.address_input.setText(address)

    def _get_lat_lon(self):
        lat = self.lat_input.text() if not self.lat_input.text() else float(self.lat_input.text())
        lon = self.lon_input.text() if not self.lon_input.text() else float(self.lon_input.text())
        return lat, lon

    def submit_close(self):
        #TODO: save input data to self.info first
        if not self.obj_list[1].text():
            print("Name required.")
            return
        for index in range(0, len(self.obj_list), 2):
            self.info[self.obj_list[index].text()] = self.obj_list[index + 1].text()
        self.accept()

    def exec_(self):
        super(Ui_AddPersonWidget, self).exec_()
        return self.info
