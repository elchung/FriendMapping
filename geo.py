from geopy.distance import vincenty
from geopy.geocoders import Nominatim  # address to lat lon for pretty maps
import geopy


class Geo:
    def __init__(self):
        self.geo_locator = Nominatim(user_agent="poor_memory")

    def address_to_lat_lon(self, address):
        try:
            location = self.geo_locator.geocode(address)
            return location.latitude, location.longitude
        except:
            print("Get info failed. Please check the address or internet connection.")
            return None

    def lat_lon_to_address(self, lat, lon):
        try:
            return self.geo_locator.reverse((lat, lon), language='en').address
        except geopy.exc.GeocodeServiceError:
            print("Get info failed. Please check the address or internet connection.")
            return None

    # def get_city_autocomplete(self, name):
    #     list taken from https://simplemaps.com/data/world-cities.


    @staticmethod
    def get_distance(start, end):
        # start and end should be tuple of (lat, lon)
        return vincenty(start, end)
