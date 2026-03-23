from Point import Point
import numpy as np

class Plane:
    def __init__(self, start_point: Point, end_point: Point):
        self.start_point = start_point
        self.end_point = end_point

        #Optymalizacja
        #Liczymy wartosci ktore sie nie beda zmieniac w konstruktorze 
        #Oszczedzamy kosztownych obliczen w trakcie wykonywania programu
        self.start_lat_rad = np.radians(start_point.latitude)
        self.start_lon_rad = np.radians(start_point.longitude)
        self.end_lat_rad = np.radians(end_point.latitude)
        self.end_lon_rad = np.radians(end_point.longitude)

        self.sin_start_lat = np.sin(self.start_lat_rad)
        self.cos_start_lat = np.cos(self.start_lat_rad)
        self.sin_start_lon = np.sin(self.start_lon_rad)
        self.cos_start_lon = np.cos(self.start_lon_rad)
        self.sin_end_lat = np.sin(self.end_lat_rad)
        self.cos_end_lat = np.cos(self.end_lat_rad)
        self.sin_end_lon = np.sin(self.end_lon_rad)
        self.cos_end_lon = np.cos(self.end_lon_rad)

        self.delta = np.arccos(
            np.sin(self.start_lat_rad)*np.sin(self.end_lat_rad) +
            np.cos(self.start_lat_rad)*np.cos(self.end_lat_rad)*np.cos(self.end_lon_rad-self.start_lon_rad)
        )
        self.sin_delta = np.sin(self.delta)

        dt = end_point.time - start_point.time
        self.T = dt.total_seconds()
        print(self.T)

        self.R = 6371e3 #promien Ziemi w metrach
        
    def get_plane_position(self, t):
        # f = np.clip(t / self.T, 0, 1)
        f = t / self.T

        A = np.sin((1-f)*self.delta) / self.sin_delta
        B = np.sin(f*self.delta) / self.sin_delta

        x = A*self.cos_start_lat*self.cos_start_lon + B*self.cos_end_lat*self.cos_end_lon
        y = A*self.cos_start_lat*self.sin_start_lon + B*self.cos_end_lat*self.sin_end_lon
        z = A*self.sin_start_lat + B*self.sin_end_lat

        lat = np.degrees(np.arctan2(z, np.sqrt(x**2 + y**2)))
        lon = np.degrees(np.arctan2(y, x))
        return lat, lon
    
    def calculate_mean_velocity(self):
        delta_lat = self.end_lat_rad - self.start_lat_rad
        delta_lon = self.end_lon_rad - self.start_lon_rad
        #Haversine formula
        a = np.sin(delta_lat/2) ** 2 + np.cos(self.start_lat_rad) * np.cos(self.end_lat_rad) * np.sin(delta_lon/2) ** 2
        c = 2 * np.atan2(np.sqrt(a), np.sqrt(1-a))

        d = self.R * c

        return d / self.T