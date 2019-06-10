import sys
import folium  # make pretty maps
from PyQt5 import QtGui, QtWidgets  # look at pretty maps
from geopy.distance import vincenty
from geopy.geocoders import Nominatim  # address to lat lon for pretty maps
from IPython.display import display
import xlrd
import pandas as pd

# https://blog.dominodatalab.com/creating-interactive-crime-maps-with-folium/


class Mapping:
    def __init__(self, home_coord, zoom=12):
        self.app = QtWidgets.QApplication(sys.argv)
        self.start_lat = home_coord[0]
        self.start_lon = home_coord[1]
        self.m = folium.Map(location=home_coord, zoom_start=zoom)
        self.save_location = None  # TODO Rename to self.data_save_path
        self.map_save_path = None
        self.geolocator = Nominatim(user_agent="poor_memory")
        self.unsaved_changes = False
        self.data = pd.DataFrame({
            'name': [],  # type(str)
            'lat': [],  # type(float)
            'lon': [],  # type(float)
            'city': [],  # type(str)
            'tags': [],  # type(list)
            'last visited': [],  # type(float)
            'dates visited': [],  # type(list)
            'date added': [],  # type(float)
            'description': []  # type(str)
            })
        self.column_order = self.person_sample.keys()

    #TODO
    @self.reset_save_flag
    def add_point(self, address):
        # look into vincent and altair for displaying people data whene marker is clicked
        # https://github.com/wrobstory/vincent
        # https://altair-viz.github.io/
        # for more info on popups
        # https://nbviewer.jupyter.org/github/python-visualization/folium/blob/master/examples/Popups.ipynb
        if address:
            lat, lon = self.address_to_lat_lon(address)
        point = folium.Marker([lat, lon], popup=text)
        self.points.append(point)
        point.add_to(self.m)

    #TODO: how to fil, in/
    @self.reset_save_flag
    def add_person(self, info):
        # look into vincent and altair for displaying people data whene marker is clicked
        # https://github.com/wrobstory/vincent
        # https://altair-viz.github.io/
        # for more info on popups
        # https://nbviewer.jupyter.org/github/python-visualization/folium/blob/master/examples/Popups.ipynb
        if info['name'] in self.people.keys():
            print(f"{person.name} already exists. No new entry will be added")
            return
        elif not info['name']:
            print("No name found. Entering a name is required to add entry.")
            return

        if info['city'] and not (info['lat'] or info['lon']):
            info['lat'], info['lon'] = address_to_lat_lon(address)
        elif not info['city'] and info['lat'] and info['lon']:
            info['city'] = self.lat_lon_to_city(lat=info['lat'], lon=info['lon'])
        self.data.append(info)

    def add_person_from_widget(self):
        dialog = Ui_AddPersonWidget()
        if dialog.exec_():
            # when done, save information locally
            info = dialog.info

    @self.reset_save_flag
    def merge_data_with_import(self):
        # if importing data and data already in current list, merge

    @self.reset_save_flag
    def remove_person(self, name):
        # scan through points dictionary for person or scan through excel file for person???????
        if name not in self.data['name']:
            print(f"{name} not found.")
            return

        drop_index = self.data['name'].index(name)
        self.data.drop([drop_index])

    #TODO
    def display_map(self):
        pass

    def set_map_save_path(self):
        self.map_save_path = self.get_save_as()

    def save_map(self):
        if not self.map_save_path:
            self.set_map_save_path()
        self.m.save(self.map_save_path)

    def export_to_excel(self, new_save=False):
        if new_save or not self.save_location:
            self.save_location = self.get_save_as("Excel File (*.xlsx, *.xls)")
        self.data.to_excel(self.save_location)  # TODO change this from pandadata to dicitonary import
        self.unsaved_changes = False

    def import_from_excel(self):
        if self.data['name'] and self.unsaved_changes:  # TODO: Add flag for unsaved
            new = QtWidgets.QMessageBox()
            reply = QtWidgets.QMessageBox.question(new, "Unsaved data found",
                                                   "Unsaved data found, would you like to merge with imported file?",
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel,
                                                   QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                return

            self.save_location = self.get_save_as("Excel File (*.xlsx, *.xls)")
            if reply == QtWidgets.QMessageBox.Yes:
                import_data = pd.read_excel(import_file_path)
                import_names = import_data['name'].tolist()
                data_names = self.data['name'].tolist()
                for common_name in list(set(import_names).intersection(data_names)):
                    import_name_index = import_names.index(common_name)
                    data_name_index = data_names.index(common_name)
                    prompt_text = f"{common_name} found in both data sets. Which would you like to keep? \n Existing Person: {self.data.loc[data_name_index]}\n Import Data: {import_data.loc[import_name_index]}"
                    choice = self.query_import_data_question(prompt_text)
                    if choice == 'import':
                        self.data.drop([data_name_index])
                    else:
                        import_data.drop([import_name_index])
                self.data = pd.merge(self.data, import_data, on='name', how='outer')
                # TODO: also need to check column order
            elif reply == QtWidgets.QMessageBox.No:
                self.data = pd.read_excel(import_file_path)

    def reset_save_flag(self):
        self.unsaved_changes = True

    @staticmethod
    def query_import_data_question(question):
        message = QtWidgets.QMessageBox()
        message.setText(question)
        keep_default = message.addButton('Keep Present Name', QtWidgets.QMessageBox.YesRole)
        keep_import = message.addButton('Keep Import Name', QtWidgets.QMessageBox.NoRole)
        message.exec_()
        return 'default' if message.clickedButton() == keep_default else 'import'

    @staticmethod
    def get_distance(start, end):
        # start and end should be tuple of (lat, lon)
        return vincenty(start, end)

    @staticmethod
    def get_save_as(filetype="HTML File (*.html)"):
        filedialog = QtWidgets.QFileDialog()
        return QtWidgets.QFileDialog.getSaveFileName(filedialog, 'Save As', '', filetype)[0]

    @staticmethod
    def address_to_lat_lon(address):
        location = self.geolocator.geocode(address)
        return location.latitude, location.longitude

    @staticmethod
    def lat_lon_to_city(lat, lon):
        return self.geolocator.reverse((lat, lon), language='en').raw['address']['city']


class Ui_AddPersonWidget(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.info = {}
        self.Submit.clicked.connect(self.submitclose)

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

    def setupUi(self, ShowGroupWidget):
        #sets up submit button

    def submitclose(self):
        #TODO: save input data to self.info first
        self.info = {




        }
        self.accept()


# class Person:
#     def __init__(self, address, name, tags=None, latitude=None, longitude=None, description=None):
#         if not name:
#             print("Error, name required!?")
#         if not address:
#             print("Error, address required!?")

#         coordinates = address_to_lat_lon(address)

#         self._address = address
#         self._name = name
#         self._tags = tags if tags else []
#         self._latitude = latitude if latitude else coordinates[0]
#         self._longitude = longitude if longitude else coordinates[1]
#         self._description = description

#     def make_popup(self):
#         # returns html readable text for folium popups
#         html = f" \
#             <b>{self.name}</b>\n \
#                 <b>Address:</b> {self._address}\n \
#                 <b>Tags:</b> {self._tags}\n \
#                 <b>Description:</b> {self._description}\n \
#         "
#         return html

#     def add_tag(self, val):
#         self._tags.append(val)

#     def remove_tag(self, val):
#         if val in self._tags:
#             self._tags.remove(val)
#         else:
#             print(f"No tag corresponding to {val} found")

#     def clear_tags(self):
#         self._tags = []

#     @property
#     def tags(self):
#         return self._tags

#     @tags.setter
#     def tags(self, tag_list):
#         if type(tag_list) is not list:
#             print("Error, input must be type List")
#         else:
#             self._tags = tag_list

#     @property
#     def address(self):
#         return self._address

#     @address.setter
#     def address(self, new_address):
#         self._address = new_address

#     @property
#     def name(self):
#         return self._name

#     @name.setter
#     def name(self, new_name):
#         self._name = new_name

#     @property
#     def longitude(self):
#         return self._longitude

#     @longitude.setter
#     def longitude(self, new_longitude):
#         self._longitude = new_longitude

#     @property
#     def latitude(self):
#         return self._latitude

#     @latitude.setter
#     def latitude(self, new_latitude):
#         self._latitude = new_latitude

#     @property
#     def description(self):
#         return self._description

#     @description.setter
#     def description(self, new_description):
#         self._description = new_description




def main():
    mapper = Mapping(address_to_lat_lon('412 broadway Seattle WA'))
    mapper.save()

'''
long term additions:
custom markers
filter people by tags
click to add person
create polygon to get list of people in area

https://mybinder.org/v2/gh/ipython/ipython-in-depth/master?filepath=binder/Index.ipynb

https://ipython.org/  for interactive uses
https://jupyter.org/  for interactive uses

https://blog.dominodatalab.com/creating-interactive-crime-maps-with-folium/
https://app.dominodatalab.com/u/r00sj3/crimemaps/view/examples.ipynb
https://app.dominodatalab.com/u/r00sj3/crimemaps/view/crimemap.ipynb
https://python-visualization.github.io/folium/quickstart.html#Vincent/Vega-and-Altair/VegaLite-Markers


'''

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main()
    sys.exit(app.exec_())
