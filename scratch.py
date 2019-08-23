'''
First view, show world map with heatmap of where people are
can zoom in based on creating square of land.
User can click "bubbles" to bring up a list of people. Clicking on the names will open text that describes city they live in, last updated
search function to show nearby people in the city visiting?
"add friend - location"
"move friend(name, move_to)"
"get friend" --check name spelling?

maybe have the ability to import information from facebook, or instagram, or other? linkedin for work info?
'''
import sys
import folium  # make pretty maps
from PyQt5 import QtGui, QtWidgets, QtCore  # look at pretty maps
from PyQt5.QtWidgets import QApplication
from geopy.distance import vincenty
from geopy.geocoders import Nominatim  # address to lat lon for pretty maps
# from IPython.display import display
import xlrd
import pandas as pd
import time

class Ui_AddPersonWidget(QtWidgets.QDialog):
    def __init__(self, options):
        # in: options is type(list) of names for each option to input
        QtWidgets.QDialog.__init__(self)
        self.obj_list = []  # storage for dynamic variables since can't name them all..# .
        self.info = {}
        self.setupUi(options)
        # self.Submit.clicked.connect(self.submitclose)
        '''
            'name': [],
            'lat': [],
            'lon': [],
            'city': [],
            'tags': [],
            'last visited': [],
            'dates visited': [],
            'description': []
        '''

    def setupUi(self, options):
        y_counter = 1
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(5)
        for i in options:
            name = QtWidgets.QLabel(i)
            user_input = QtWidgets.QLineEdit()
            self.obj_list.append(name)
            self.obj_list.append(user_input)
            grid.addWidget(name, y_counter, 0)
            grid.addWidget(user_input, y_counter, 1)
            y_counter += 1

        self.buttons = QtWidgets.QDialogButtonBox()
        self.buttons.addButton("Submit", QtWidgets.QDialogButtonBox.AcceptRole)
        self.buttons.addButton("Cancel", QtWidgets.QDialogButtonBox.RejectRole)
        grid.addWidget(self.buttons)
        self.setLayout(grid)
        self.setGeometry(300, 300, 100*y_counter, 300)
        self.setWindowTitle("Enter Information")
        self.buttons.accepted.connect(self.submitclose)
        self.buttons.rejected.connect(self.reject)

        self.show()

    def submitclose(self):
        #TODO: save input data to self.info first
        for index in range(0, len(self.obj_list), 2):
            self.info[self.obj_list[index].text()] = self.obj_list[index + 1].text()
        self.accept()

    def exec_(self):
        super(Ui_AddPersonWidget, self).exec_()
        return self.info

if __name__ == "__main__":
    op = ['l1', '2', '3', '4', '5']

    app = QApplication(sys.argv)
    ex = Ui_AddPersonWidget(op)

    val = ex.exec_()
    print(val)

    sys.exit(app.exec_())