import sys
import folium  # make pretty maps
from PyQt5 import QtGui, QtWidgets, QtCore  # look at pretty maps
from geo import Geo
import pandas as pd
import time
import friend_map_ui
import popup_widgets
from PandasModel import PandasModel, ComboDelegate
# https://blog.dominodatalab.com/creating-interactive-crime-maps-with-folium/
#look into qcompleter for city autocomplete
#look into importing from contacts list on phone, then saving to phone


class VCFParser:
    def __init__(self):
        pass

class Mapping(friend_map_ui.Ui_MainWindow):
    def __init__(self, window, home_coord=(0, 0), zoom=12):
        super().__init__()
        self.setupUi(window)
        # input: tuple of starting coordinates
        self.app = QtWidgets.QApplication(sys.argv)

        self.start_lat = home_coord[0]
        self.start_lon = home_coord[1]
        self.geo_locator = Geo()
        self.m = folium.Map(location=home_coord, zoom_start=zoom)
        self.default_map_save = r'C:\Users\Eric\Documents\Python Scripts\FriendMap'
        self.save_location = None
        self.map_save_path = None
        self.unsaved_changes = False
        self.data = pd.DataFrame({  # will only be used for passthrough to model
            'Name': ['a'],  # type(str)
            'Lat': ['a'],  # type(float)
            'Lon': ['a'],  # type(float)
            'Address': ['0'],  # type(str)
            'Tags': ['0'],  # type(list)
            'Last visited': ['0'],  # type(float)
            'Dates visited': ['0'],  # type(list)
            'Date added': ['0'],  # type(float)
            'Description': ['0']  # type(str)
            })

        pandas_table_model = PandasModel(self.data)
        self.tableView_data.setModel(pandas_table_model)
        # self.tableView_data.setItemDelegateForColumn(1, ComboDelegate)
        # self.tableView_data.setColumnCount(len(self.data.keys()))
        # self.data_model = PandasModel(self.data)
        # self.tableView_data.setModel(self.data_model)
        # self.column_order = self.person_sample.keys()
        self.setup_connections()

    def setup_connections(self):
        self.pushButton_add_person.clicked.connect(self.add_person)
        self.pushButton_remove_person.clicked.connect(self.find_and_remove_person)
        self.pushButton_import.clicked.connect(self.import_from_excel)
        self.pushButton_save_data.clicked.connect(lambda: self.export_to_excel(False))
        self.pushButton_save_data_as.clicked.connect(lambda: self.export_to_excel(True))
        self.pushButton_save_map.clicked.connect(lambda: self.save_map(False))
        self.pushButton_save_map_as.clicked.connect(lambda: self.save_map(True))
        self.pushButton_set_home.clicked.connect(self.set_home)
        self.pushButton_show_map.clicked.connect(self.display_map)
        self.pushButton_return_to_main.clicked.connect(self._return_to_main)
        self.pushButton_add_row.clicked.connect(self.add_table_row)
        # self.tableView_data.dataChanged.connect(self._update_dataframe_from_table)  # variable to track last entered cell, so when it's left to save to dataframe


    def add_person(self):
        # look into vincent and altair for displaying people data whene marker is clicked
        # https://github.com/wrobstory/vincent
        # https://altair-viz.github.io/
        # for more info on popups
        # https://nbviewer.jupyter.org/github/python-visualization/folium/blob/master/examples/Popups.ipynb
        self.unsaved_changes = True

        ex = popup_widgets.Ui_AddPersonWidget(list(self.data.keys()))
        info = ex.exec_()
        if not info:
            return
        elif info['Name'] in self.data['Name']:
            print(f"{info['name']} already exists. No new entry will be added")
            return
        elif not info['Name']:
            print("No name found. Entering a name is required to add entry.")
            return

        if info['Address'] and ('Lat' not in info.keys() or 'Lon' not in info.keys()):
            info['Lat'], info['Lon'] = self.geo_locator.address_to_lat_lon(info['Address'])
        elif 'Address' not in info.keys() and info['Lat'] and info['Lon']:
            info['Address'] = self.geo_locator.lat_lon_to_address(lat=info['Lat'], lon=info['Lon'])
        df_info = pd.Series(info)
        self.data = self.data.append(df_info, ignore_index=True)  # data frames don't append in place
        self._update_table_view(info)

    def add_table_row(self):
        self._update_table_view(pd.Series())
        self.tableView_data.model().layoutChanged.emit()
        # self.tableView_data.update()

    def find_and_remove_person(self):
        pass
        # finds selected person and removes from list

    # https://stackoverflow.com/questions/18172851/deleting-dataframe-row-in-pandas-based-on-column-value
    def remove_person(self, name):
        # scan through points dictionary for person or scan through excel file for person???????
        self.unsaved_changes = True
        if name not in self.data['Name']:
            print(f"{name} not found.")
            return

        drop_index = self.data['Name'].index(name)
        self.data.drop([drop_index])

    def save_map(self, new_save=False):
        if new_save or not self.map_save_path:
            self.map_save_path = self.get_save_as()
        self.m.save(self.map_save_path)

    # pandas.pydata.org/pandas-docs/version/0.17.0/generated/pandas.DataFrame.to_dict.html#pandas.DataFrame.to_dict
    def display_map(self):
        self.stackedWidget_main.setCurrentIndex(1)
        for p_dict in self.data.to_dict('records'):
            text = self.make_html_popup_text(p_dict)
            folium.Marker([p_dict['Lat'], p_dict['Lon']], popup=text, tooltip=p_dict['Name']).add_to(self.m)

    def make_html_popup_text(self, info):
        # input: info = dictionary of all data to display
        # out: html string
        popup_text = f"<b></b>{info['Name']}\n"
        for key in info.keys():
            if key != 'Name':
                popup_text += f"<b>{key}:</b> {info[key]}\n"
        return popup_text

    def export_to_excel(self, new_save=False):
        if new_save or not self.save_location:
            self.save_location = self.get_save_as("Excel File (*.xlsx, *.xls)")
        self.data.to_excel(self.save_location)
        self.unsaved_changes = False

    def import_from_excel(self):
        self.unsaved_changes = True
        if self.data['Name'] and self.unsaved_changes:  # TODO: Add flag for unsaved
            new = QtWidgets.QMessageBox()
            reply = QtWidgets.QMessageBox.question(new, "Unsaved data found",
                                                   "Unsaved data found, would you like to merge with imported file?",
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
                                                   QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.Cancel:
                return

            import_file_path = self.get_save_as("Excel File (*.xlsx, *.xls)")
            if reply == QtWidgets.QMessageBox.Yes:
                import_data = pd.read_excel(import_file_path)
                import_names = import_data['Name'].tolist()
                data_names = self.data['Name'].tolist()
                for common_name in list(set(import_names).intersection(data_names)):
                    import_name_index = import_names.index(common_name)
                    data_name_index = data_names.index(common_name)
                    prompt_text = f"{common_name} found in both data sets. Which would you like to keep? \n " \
                        f"Existing Person: {self.data.loc[data_name_index]}\n " \
                        f"Import Data: {import_data.loc[import_name_index]}"
                    choice = self.query_import_data_question(prompt_text)
                    if choice == 'import':
                        self.data.drop([data_name_index])
                    else:
                        import_data.drop([import_name_index])
                self.data = pd.merge(self.data, import_data, on='Name', how='outer')
                # TODO: also need to check column order
            elif reply == QtWidgets.QMessageBox.No:
                self.data = pd.read_excel(import_file_path)

    #TODO check this, this was originally copied from other file
    def find_nearest_friends(self, lon=None, lat=None, city=None, distance=100):
        if not lon and not lat and not city:
            return False
        if (not lon or not lat) and city:
            lon, lat = Geo.address_to_lat_lon(city)

        # ordered = heap()
        # for i in self.friends:
        #     if dist <= distance:
        #         ordered.add(dist, friend)

    #TODO check dis shit out
    def render_map(self):
        self.map = folium.Map(location=[self.start_lat, self.start_lon], tiles="Mapbox Bright", zoom_start=2)
        # I can add marker one by one on the map
        for i in range(len(self.data)):
            lon = i['Address']
            folium.Marker([self.data.iloc[i]['Lon'], self.data.iloc[i]['Lat']], popup=self.data.iloc[i]['Name']).add_to(self.map)
        self.map.save(self.default_map_save)
        self.WebKit_map.load(self.default_map_save)

    def set_home(self):
        ex = popup_widgets.Ui_SetHomeWidget()
        info = ex.exec_()
        self.start_lat = info['Lat']
        self.start_lon = info['Lon']

    def resizeColumnsToContents(self):
        self.tableView_data.resizeColumnsToContents()()

    def _update_table_view(self, data):
        # called when add person is fininshed
        row_position = self.tableView_data.model().rowCount()
        self.tableView_data.model().insertRow(row_position, data=data)
        # self.tableView_data.setRowCount(self.tableView_data.rowCount())
        # self.tableView_data.setColumnCount(self.tableView_data.columnCount())
        # for i in

    def _update_dataframe_from_table(self):
        # gets called when data is manually entered in tableview. will update dataframe with new data
        pass

    def update_dataframe_from_table(self, prev_row, prev_col, new_row, new_col):
        # update dataframe with new data
        #if column worked with was lat/lon or address, to update the previous cells and update the dataframe accordingly
        pass


    def _return_to_main(self):
        self.stackedWidget_main.setCurrentIndex(0)

    @staticmethod
    def query_import_data_question(question):
        message = QtWidgets.QMessageBox()
        message.setText(question)
        keep_default = message.addButton('Keep Present Name', QtWidgets.QMessageBox.YesRole)
        keep_import = message.addButton('Keep Import Name', QtWidgets.QMessageBox.NoRole)
        message.exec_()
        return 'default' if message.clickedButton() == keep_default else 'import'

    @staticmethod
    def get_save_as(filetype="HTML File (*.html)"):
        filedialog = QtWidgets.QFileDialog()
        return QtWidgets.QFileDialog.getSaveFileName(filedialog, 'Save As', '', filetype)[0]


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    ui = Mapping(window)
    window.show()
    sys.exit(app.exec_())


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

todo:
add option to add info column
'''