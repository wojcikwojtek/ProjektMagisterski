from Point import Point
from PySide6.QtGui import QVector3D
import numpy as np
from DronePathTest import compute_path, convert_geodetic_to_ecef, convert_ecef_to_geodetic

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
        # print(self.T)

        self.R = 6371e3 #promien Ziemi w metrach
        #Zmienic to potem 
        self.mean_velocity = None
        self.mean_velocity = self.calculate_mean_velocity()
        self.altitude = 120

        X0 = np.array(convert_geodetic_to_ecef(self.start_point.latitude, self.start_point.longitude, 120))
        v1 = np.array([1.0, 1.0, 1.0])/np.sqrt(3)
        X1 = np.array(convert_geodetic_to_ecef(self.end_point.latitude, self.end_point.longitude, 120))
        v2 = np.array([1.0, 1.0, 1.0])/np.sqrt(3)
        nmax = 1.2002
        self.path = compute_path(X0, X1, v1, v2, self.mean_velocity, nmax)
        line = np.linspace(self.path["P1"], self.path["P2"], 200)
        self.trajectory =  np.vstack([
            self.path["arc1"],
            line[1:],
            self.path["arc2"][1:]
        ])
        self.ds = np.linalg.norm(
            np.diff(self.trajectory, axis=0),
            axis=1
        )

        self.cum_s = np.concatenate([
            [0],
            np.cumsum(self.ds)
        ])

    def get_plane_position(self, t):
        # # f = np.clip(t / self.T, 0, 1)
        # f = t / self.T

        # A = np.sin((1-f)*self.delta) / self.sin_delta
        # B = np.sin(f*self.delta) / self.sin_delta

        # x = A*self.cos_start_lat*self.cos_start_lon + B*self.cos_end_lat*self.cos_end_lon
        # y = A*self.cos_start_lat*self.sin_start_lon + B*self.cos_end_lat*self.sin_end_lon
        # z = A*self.sin_start_lat + B*self.sin_end_lat

        # self.current_lat = np.degrees(np.arctan2(z, np.sqrt(x**2 + y**2)))
        # self.current_lon = np.degrees(np.arctan2(y, x))
        # return self.current_lat, self.current_lon

        total_length = self.cum_s[-1]

        s = self.mean_velocity * t 

        if s >= total_length:
            s = total_length

        idx = np.searchsorted(self.cum_s, s)

        if idx == 0:
            pos = self.trajectory[0]

        elif idx >= len(self.trajectory):
            pos = self.trajectory[-1]

        else:
            s0 = self.cum_s[idx - 1]
            s1 = self.cum_s[idx]

            alpha = (s - s0) / (s1 - s0)

            pos = (
                (1 - alpha) * self.trajectory[idx - 1]
                + alpha * self.trajectory[idx]
            )

        lat, lon, height = convert_ecef_to_geodetic(pos[0], pos[1], pos[2])
        
        return lat, lon
    
    def calculate_mean_velocity(self):
        if self.mean_velocity is None:
            delta_lat = self.end_lat_rad - self.start_lat_rad
            delta_lon = self.end_lon_rad - self.start_lon_rad
            #Haversine formula
            a = np.sin(delta_lat/2) ** 2 + np.cos(self.start_lat_rad) * np.cos(self.end_lat_rad) * np.sin(delta_lon/2) ** 2
            c = 2 * np.atan2(np.sqrt(a), np.sqrt(1-a))

            d = self.R * c

            self.mean_velocity = d / self.T

        return self.mean_velocity
    
    def currentStats(self):
        return {
            "latitude": "{:.4f}".format(self.current_lat),
            "longitude": "{:.4f}".format(self.current_lon),
            "mean velocity": "{:.4f}".format(self.calculate_mean_velocity()) + " m/s",
            "altitude": self.altitude
        }