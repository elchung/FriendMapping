import sys
import folium  # make pretty maps
from PyQt5 import QtGui, QtWidgets, QtCore, QtWebEngineWidgets  # look at pretty maps
from geo import Geo
from os import path
import pandas as pd
import pickle
import friend_map_ui
import popup_widgets
from PandasModel import PandasModel, cellValidationDelegate
from datetime import datetime
# https://blog.dominodatalab.com/creating-interactive-crime-maps-with-folium/
# look into qcompleter for city autocomplete
# look into importing from contacts list on phone, then saving to phone


class Mapping(friend_map_ui.Ui_MainWindow):
    def __init__(self, window, zoom=12):
        super().__init__()
        self.setupUi(window)
        # input: tuple of starting coordinates
        self.app = QtWidgets.QApplication(sys.argv)

        # dataframe header names for better referencing
        self.addr_name = 'Address'
        self.lat_name = 'Lat'
        self.lon_name = 'Lon'

        self.start_lat = 38.6268039
        self.start_lon = -90.1994097
        self.geo_locator = Geo()
        self.map = folium.Map(location=(self.start_lat, self.start_lon), zoom_start=zoom)
        self.default_map_save = path.dirname(path.abspath(__file__)) + r"\map.html"
        self.address_pickle_location = path.dirname(path.abspath(__file__)) + r"\cities_dictionary.pkl"
        self.city_lookup_dict = None
        self.save_location = None
        self.map_save_path = None
        self.unsaved_changes = False
        self.editing_cells = False
        self.last_edited_data = None
        self.data = pd.DataFrame({  # will only be used for passthrough to model
            'Name': ['Eric Chung'],  # type(str)
            self.addr_name: ['Saint Louis, MO'],  # type(str)
            'Tags': ['Me, Myself, I'],  # type(list)
            self.lat_name: str(self.start_lat),  # type(float)
            self.lon_name: str(self.start_lon),  # type(float)
            'Last visited': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],  # type(float)
            'Dates visited': ['All the time'],  # type(list)
            'Date added': [datetime.fromtimestamp(777186000).strftime('%Y-%m-%d %H:%M:%S')],  # type(float)
            'Description': ['0']  # type(str)
            })
        self._setup_map()
        self._setup_column_delegates()
        self._setup_connections()
        self._setup_column_width_rules()
        self._load_address_dict_from_pickle()
        self.stackedWidget_main.setCurrentIndex(0)

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
            self.print_output(f"{info['name']} already exists. No new entry will be added")
            return
        elif not info['Name']:
            self.print_output("No name found. Entering a name is required to add entry.")
            return

        if info[self.addr_name] and ('Lat' not in info.keys() or 'Lon' not in info.keys()):
            info[self.lat_name], info[self.lon_name] = self._get_coordinates_from_address(info[self.addr_name])
        elif 'Address' not in info.keys() and info['Lat'] and info['Lon']:
            info[self.addr_name] = self._get_address_from_coordinates(lat=info[self.lat_name], lon=info[self.lon_name])
        df_info = pd.Series(info)
        self.data = self.data.append(df_info, ignore_index=True)  # data frames don't append in place
        self._update_table_view(info)
        self.print_output(f"{info['Name']} added!")

    def add_table_row(self):
        self._update_table_view(pd.Series())
        self.tableView_data.model().layoutChanged.emit()
        # self.tableView_data.update()

    def find_and_remove_person(self):
        print(self.tableView_data.currentIndex().row())
        self.tableView_data.model().removeRow(self.tableView_data.currentIndex().row())
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

    # TODO
    def save_map(self, new_save=False):
        if new_save or not self.map_save_path:
            self.map_save_path = self.get_save_as()
            if not self.map_save_path:
                return
        self.map.save(self.map_save_path)

    def display_map(self):
        self.render_map()
        self.stackedWidget_main.setCurrentIndex(1)

    def render_map(self):
        # # if not self.map....
        # # if no map, make new one. If map, check what markers have been added and only add new ones

        self.map = folium.Map(location=[self.start_lat, self.start_lon], tiles="OpenStreetMap", zoom_start=12)
        for p_dict in self.tableView_data.model().dataFrame.to_dict('records'):
            text = self.make_html_popup_text(p_dict)
            folium.Marker([float(p_dict['Lat']), float(p_dict['Lon'])], popup=text, tooltip=p_dict['Name']).add_to(self.map)
        self.map.save(self.default_map_save)
        self.webKit_map.load(QtCore.QUrl.fromLocalFile(self.default_map_save))

    def make_html_popup_text(self, info):
        # input: info = dictionary of all data to display
        # out: html string
        popup_text = f"<b></b>{info['Name']}\n\n"
        for key in info.keys():
            if key != 'Name':
                popup_text += f"<b>{key}:</b> {info[key]}\n\n"
        return popup_text

    def export_to_excel(self, new_save=False):
        if new_save or not self.save_location:
            self.save_location = self.get_save_as("Excel File (*.xlsx)")
            if not self.save_location:
                return
        self.tableView_data.model().dataFrame.to_excel(self.save_location, index=None, header=True)
        self.unsaved_changes = False
        self.print_output("Saved!")

    #Todo
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
            lon, lat = self.geo_locator.address_to_lat_lon(city)

        # ordered = heap()
        # for i in self.friends:
        #     if dist <= distance:
        #         ordered.add(dist, friend)

    def set_home(self):
        ex = popup_widgets.Ui_SetHomeWidget()
        info = ex.exec_()
        if not info:
            return
        self.start_lat = info['Lat']
        self.start_lon = info['Lon']

    def resizeColumnsToContents(self):
        self.tableView_data.resizeColumnsToContents()

    def check_location(self, index=None):
        '''check index
        check if lat lon changed or city
        updated other'''
        if self.editing_cells or not index or self._get_cell_data(index.row(), index.column()) == 'nan':
            return False
        self.editing_cells = True

        if index.column() in (self._get_lat_col_index(), self._get_lon_col_index()):
            lat_data = self._get_cell_data(index.row(), self._get_lat_col_index())
            lon_data = self._get_cell_data(index.row(), self._get_lon_col_index())
            address = self._get_address_from_coordinates(lat_data, lon_data)
            self.set_cell_data(index.row(), self._get_addr_col_index(), address)
        elif index.column() == self._get_addr_col_index():
            print(self._get_cell_data(index.row(), self._get_addr_col_index()))
            lat, lon = self._get_coordinates_from_address(self._get_cell_data(index.row(), self._get_addr_col_index()))
            self.set_cell_data(index.row(), self._get_lat_col_index(), lat)
            self.set_cell_data(index.row(), self._get_lon_col_index(), lon)
        self.editing_cells = False
        return True

    def set_cell_data(self, row, column, data):
        self.tableView_data.model().dataFrame.iloc[row][column] = data
        return True

    def print_output(self, text):
        self.textEdit_output.moveCursor(QtGui.QTextCursor.End)  # make sure cursor is at end before pasting new text
        text = f"<b>[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}]:</b> {str(text)}"
        self.textEdit_output.insertHtml(text)
        self.textEdit_output.append("")
        self.textEdit_output.scrollToAnchor(text)
        self.textEdit_output.moveCursor(QtGui.QTextCursor.End)
        QtWidgets.QApplication.processEvents()

    def _get_address_from_coordinates(self, lat, lon):
        return self.geo.locator.lat_lon_to_address(lat, lon)

    def _get_coordinates_from_address(self, address):
        return self.geo_locator.address_to_lat_lon(address)

    def _get_cell_data(self, row, column):
        return self.tableView_data.model().dataFrame.iloc[row][column]

    def _setup_map(self):
        # added since qt creator doesn't have webengineview built in
        self.webKit_map = QtWebEngineWidgets.QWebEngineView(self.page_map)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.webKit_map.sizePolicy().hasHeightForWidth())
        self.webKit_map.setSizePolicy(sizePolicy)
        self.webKit_map.setObjectName("webKit_map")
        self.gridLayout_3.addWidget(self.webKit_map, 0, 1, 2, 1)


    def _setup_column_delegates(self):
        pandas_table_model = PandasModel(self.data)
        self.tableView_data.setModel(pandas_table_model)
        self.lat_delegate = cellValidationDelegate(max=90, min=-90)
        self.lon_delegate = cellValidationDelegate(max=180, min=-180)
        self.tableView_data.setItemDelegateForColumn(self._get_lat_col_index(), self.lat_delegate)
        self.tableView_data.setItemDelegateForColumn(self._get_lon_col_index(), self.lon_delegate)

    def _setup_column_width_rules(self):
        header = self.tableView_data.horizontalHeader()
        for column in range(len(self.data.keys()) - 1):
            header.setSectionResizeMode(column, QtWidgets.QHeaderView.Interactive)
        header.setStretchLastSection(True)
        self.resizeColumnsToContents()

    def _setup_connections(self):
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
        self.tableView_data.model().dataChanged.connect(self.check_location)

    def _load_address_dict_from_pickle(self):
        with open(self.address_pickle_location, 'rb') as f:
            self.city_lookup_dict = pickle.load(f)

    def _get_lat_col_index(self):
        return self.tableView_data.model().dataFrame.columns.tolist().index(self.lat_name)

    def _get_lon_col_index(self):
        return self.tableView_data.model().dataFrame.columns.tolist().index(self.lon_name)

    def _get_addr_col_index(self):
        return self.tableView_data.model().dataFrame.columns.tolist().index(self.addr_name)

    def _return_to_main(self):
        self.stackedWidget_main.setCurrentIndex(0)
        return True

    def _update_table_view(self, data):
        # called when add person is finished
        row_position = self.tableView_data.model().rowCount()
        self.tableView_data.model().insertRow(row_position, data=data)

    def _no_cell_edited(self, index):
        return self.tableView_data.model().last_edited == self._get_cell_data(index.row(), index.column())

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