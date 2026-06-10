from Point import Point
from scipy.optimize import root_scalar
import numpy as np
from DronePathTest import compute_path, convert_geodetic_to_ecef, convert_ecef_to_geodetic

class Plane:
    def __init__(self, points: list[Point]):
        # self.start_point = start_point
        # self.end_point = end_point

        # #Optymalizacja
        # #Liczymy wartosci ktore sie nie beda zmieniac w konstruktorze 
        # #Oszczedzamy kosztownych obliczen w trakcie wykonywania programu
        # self.start_lat_rad = np.radians(start_point.latitude)
        # self.start_lon_rad = np.radians(start_point.longitude)
        # self.end_lat_rad = np.radians(end_point.latitude)
        # self.end_lon_rad = np.radians(end_point.longitude)

        # self.sin_start_lat = np.sin(self.start_lat_rad)
        # self.cos_start_lat = np.cos(self.start_lat_rad)
        # self.sin_start_lon = np.sin(self.start_lon_rad)
        # self.cos_start_lon = np.cos(self.start_lon_rad)
        # self.sin_end_lat = np.sin(self.end_lat_rad)
        # self.cos_end_lat = np.cos(self.end_lat_rad)
        # self.sin_end_lon = np.sin(self.end_lon_rad)
        # self.cos_end_lon = np.cos(self.end_lon_rad)

        # self.delta = np.arccos(
        #     np.sin(self.start_lat_rad)*np.sin(self.end_lat_rad) +
        #     np.cos(self.start_lat_rad)*np.cos(self.end_lat_rad)*np.cos(self.end_lon_rad-self.start_lon_rad)
        # )
        # self.sin_delta = np.sin(self.delta)
        if(len(points) < 2):
            return 
        
        self.points = points
        dt = points[-1].time - points[0].time
        self.T = dt.total_seconds()
        # print(self.T)

        self.R = 6371e3 #promien Ziemi w metrach
        self.nmax = 1.2002
        # self.mean_velocity = self.calculate_mean_velocity()
        self.calculate_mean_velocity()
        self.altitude = 120

        self.calculate_path()

        self.cum_times = [0]
        for t in self.segment_times:
            self.cum_times.append(
                self.cum_times[-1] + t
            )

    def calculate_path(self):
        self.path = []
        self.segment_lengths = []
        self.segment_paths = []

        for i in range(len(self.points) - 1):
            X0 = np.array(convert_geodetic_to_ecef(self.points[i].latitude, self.points[i].longitude, 120))
            v1 = np.array([1.0, 1.0, 1.0])/np.sqrt(3)
            X1 = np.array(convert_geodetic_to_ecef(self.points[i + 1].latitude, self.points[i + 1].longitude, 120))
            v2 = np.array([1.0, 1.0, 1.0])/np.sqrt(3)

            #NIE DZIAŁA
            # if i == 0:
            #     direction = X1 - X0     
            # else: 
            #     X_prev = np.array(convert_geodetic_to_ecef(self.points[i - 1].latitude, self.points[i - 1].longitude, 120))
            #     direction = X0 - X_prev

            # direction_norm = np.linalg.norm(direction)
            # v1 = direction / direction_norm

            # if i == len(self.points)-2:
            #     direction = X1 - X0 
            # else:
            #     X_next = np.array(convert_geodetic_to_ecef(self.points[i + 2].latitude, self.points[i + 2].longitude, 120))
            #     direction = X_next - X1

            # direction_norm = np.linalg.norm(direction)
            # v2 = direction / direction_norm

            path = compute_path(X0, X1, v1, v2, self.velocities[i], self.nmax)
            line = np.linspace(path["P1"], path["P2"], 200)
            if i == 0:
                self.path.append(path["arc1"])
            else: 
                self.path.append(path["arc1"][1:])
            self.path.append(line[1:])
            self.path.append(path["arc2"][1:])

            self.segment_paths.append(path)
            self.segment_lengths.append(path["length"])

        self.trajectory = np.vstack(self.path)
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
        if t <= 0:
            s = 0
        elif t >= self.T:
            s = self.cum_s[-1]
        else:
            segment_idx = np.searchsorted(self.cum_times, t) - 1
            segment_idx = max(0, min(segment_idx, len(self.velocities) - 1))
            dt_segment = t - self.cum_times[segment_idx]
            s_base = sum(self.segment_lengths[:segment_idx])
            s = s_base + (dt_segment * self.velocities[segment_idx])

        total_length = self.cum_s[-1]
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

            if s1 == s0:
                alpha = 0
            else:
                alpha = (s - s0) / (s1 - s0)

            pos = (
                (1 - alpha) * self.trajectory[idx - 1]
                + alpha * self.trajectory[idx]
            )

        lat, lon, height = convert_ecef_to_geodetic(pos[0], pos[1], pos[2])
        
        return lat, lon
    
    def calculate_mean_velocity(self):
        # if self.mean_velocity is None:
        #     delta_lat = self.end_lat_rad - self.start_lat_rad
        #     delta_lon = self.end_lon_rad - self.start_lon_rad
        #     #Haversine formula
        #     a = np.sin(delta_lat/2) ** 2 + np.cos(self.start_lat_rad) * np.cos(self.end_lat_rad) * np.sin(delta_lon/2) ** 2
        #     c = 2 * np.atan2(np.sqrt(a), np.sqrt(1-a))

        #     d = self.R * c

        #     self.mean_velocity = d / self.T

        # return self.mean_velocity

        #Na początku zaczynam od znalezienia odpowiedniego va 
        #Ale szukam dla pierwszego fragmentu 
        #Pomyśleć jak można to potem ulepszyć żeby szukać dla większej ilości 
        #Albo dla poszczególnych odcinków
        self.velocities = []
        self.segment_times = []
        for i in range(len(self.points) - 1):
            X0 = np.array(convert_geodetic_to_ecef(self.points[i].latitude, self.points[i].longitude, 120))
            v1 = np.array([1.0, 1.0, 1.0])/np.sqrt(3)
            X1 = np.array(convert_geodetic_to_ecef(self.points[i + 1].latitude, self.points[i + 1].longitude, 120))
            v2 = np.array([1.0, 1.0, 1.0])/np.sqrt(3)

            #Poprawa tak zeby wyliczac kierunki naturanie, a nie zeby byly hard coded
            # NIE DZIAŁA
            # if i == 0:
            #     direction = X1 - X0     
            # else: 
            #     X_prev = np.array(convert_geodetic_to_ecef(self.points[i - 1].latitude, self.points[i - 1].longitude, 120))
            #     direction = X0 - X_prev

            # direction_norm = np.linalg.norm(direction)
            # v1 = direction / direction_norm

            # if i == len(self.points)-2:
            #     direction = X1 - X0 
            # else:
            #     X_next = np.array(convert_geodetic_to_ecef(self.points[i + 2].latitude, self.points[i + 2].longitude, 120))
            #     direction = X_next - X1

            # direction_norm = np.linalg.norm(direction)
            # v2 = direction / direction_norm
            t = (self.points[i + 1].time - self.points[i].time).total_seconds()

            def objective(v):
                path = compute_path(X0, X1, v1, v2, v, self.nmax)

                return path["length"] - v * t
            
            #Wymyślić coś w przypadku jeżeli dana trasa akurat nie ma rozwiązania dla tego układu
            
            sol = root_scalar(
                objective,
                bracket=[10, 400],
                method="brentq"
            )

            self.velocities.append(sol.root)
            self.segment_times.append(t)

    
    def currentStats(self):
        return {
            "latitude": "{:.4f}".format(self.current_lat),
            "longitude": "{:.4f}".format(self.current_lon),
            "mean velocity": "{:.4f}".format(self.calculate_mean_velocity()) + " m/s",
            "altitude": self.altitude
        }