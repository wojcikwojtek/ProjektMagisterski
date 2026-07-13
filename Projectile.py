import numpy as np
from Plane import Plane
from Point import Point
from scipy import optimize
import time
from DronePathTest import convert_geodetic_to_ecef, convert_ecef_to_geodetic

class Projectile():
    R = 6371e3
    EPSILON = 2.0
    N = 3.0          # Efektywna stała nawigacyjna (musi być N > 2 dla zachowania stabilności)

    def __init__(self, start_point: Point, intercepted_plane: Plane, current_time: float, method, velocity: float, disabled = False):
        self.start_point = start_point
        self.intercepted_plane = intercepted_plane
        self.disabled = disabled
        self.velocity = velocity
        self.pos_geo = [start_point.latitude, start_point.longitude, 120]
        self.pos_ecef = convert_geodetic_to_ecef(start_point.latitude, start_point.longitude, 120)
        self.method = method
        print(self.method)

        self.launch_time = current_time
        if self.method == "PredictiveInterceptivePoint":
            self.predictive_interceptive_point = self.calculate_predictive_interceptive_point(current_time)
        elif self.method == "ProportionalNavigation":
            self.v_M = self.get_starting_projectile_velocity_vector()

        self.distance = 0.0

        # if not disabled:
        #     self.calculate_intercept_angle(current_time, velocity)

    #Rozbic na mniejsze funkcje
    def calculate_current_cords(self, t, previous_t, ecef = False):
        previous_pos = np.array(self.pos_ecef)

        # psia krzywa
        if self.method == "PursuitCurve":
            plane_pos = self.intercepted_plane.get_plane_position(t, ecef=True)

            dist = np.linalg.norm(plane_pos - self.pos_ecef)
            if dist <= self.EPSILON:
                if ecef == True:
                    return self.pos_ecef
                else:
                    return self.pos_geo[0], self.pos_geo[1]
            
            direction = plane_pos - self.pos_ecef
            direction /= np.linalg.norm(direction)

            dt = t - previous_t
            self.pos_ecef += direction * (self.velocity * dt)

        # predictive interceptive point
        elif self.method == "PredictiveInterceptivePoint":
            if t < self.launch_time:
                return self.start_point.latitude, self.start_point.longitude
            
            new_intercept = self.calculate_predictive_interceptive_point(t)

            if np.linalg.norm(
                    new_intercept - self.predictive_interceptive_point
                ) > 1000:
                self.predictive_interceptive_point = new_intercept
            
            dt = t - previous_t

            direction = self.predictive_interceptive_point - self.pos_ecef
            direction /= np.linalg.norm(direction)

            self.pos_ecef += direction * self.velocity * dt

        # Proportional Navigation
        elif self.method == "ProportionalNavigation":
            dt = t - previous_t
            r_M = self.pos_ecef
            r_T = self.intercepted_plane.get_plane_position(t, ecef=True)
            v_T = self.get_velocity_vector(t)

            r = r_T - r_M
            R = np.linalg.norm(r)

            # if R < 1.0: 
            #     return self.pos_ecef

            r_1 = r / R 
            v = v_T - self.v_M

            R_dot = np.dot(v, r_1)
            V_c = -R_dot

            #Zabezpieczenie przed ujemnym V_c
            #Pewnego rodzaju oszukanie algorytmu
            V_c = max(V_c, 5.0)

            omega_LOS = np.cross(r, v) / (R**2)
            n_dot = np.cross(omega_LOS, r_1)

            a_M_command = self.N * V_c * n_dot
            max_g = 25 * 9.81
            a_M_magnitude = np.linalg.norm(a_M_command)
            if a_M_magnitude > max_g:
                a_M_command = (a_M_command / a_M_magnitude) * max_g

            self.v_M += a_M_command * dt
            # Wymuszenie stałej prędkości drona (korekta kierunku, ale utrzymanie ciągu)
            current_speed = np.linalg.norm(self.v_M)
            if current_speed > 0:
                self.v_M = (self.v_M / current_speed) * self.velocity

            self.pos_ecef += self.v_M * dt
            
        #liczenie dystansu
        step_distance = np.linalg.norm(self.pos_ecef - previous_pos)
        self.distance += step_distance

        self.pos_geo = convert_ecef_to_geodetic(self.pos_ecef[0], self.pos_ecef[1], self.pos_ecef[2])
        if ecef == True:
            return self.pos_ecef
        else:
            return self.pos_geo[0], self.pos_geo[1]

        
    def calculate_predictive_interceptive_point(self, t):
        #rozwiązujemy równanie
        #(v_t^2 - v_i^2)t^2 + 2 * (s_t - s_i) * v_t * t + (s_t - s_i)^2 = 0

        plane_start_point = self.intercepted_plane.get_plane_position(t, ecef=True)
        plane_velocity_vector = self.get_velocity_vector(t)

        projectile_start_point = np.array(self.pos_ecef)
        R = plane_start_point - projectile_start_point

        a = np.dot(plane_velocity_vector, plane_velocity_vector) - self.velocity**2
        b = 2 * np.dot(R, plane_velocity_vector)
        c = np.dot(R, R)

        delta = b**2 - 4 * a * c
        if delta < 0:
            return None
        
        t1 = (-b + np.sqrt(delta)) / (2 * a) 
        t2 = (-b - np.sqrt(delta)) / (2 * a)

        times = [t for t in (t1, t2) if t > 0]
        if not times:
            return None 
        
        t_hit = min(times)

        return plane_start_point + plane_velocity_vector * t_hit

    # def latlon_to_vector(self, lat, lon):
    #     lat_rad = np.radians(lat)
    #     lon_rad = np.radians(lon)

    #     return np.array([
    #         self.R * np.cos(lat_rad) * np.cos(lon_rad),
    #         self.R * np.cos(lat_rad) * np.sin(lon_rad),
    #         self.R * np.sin(lat_rad)
    #     ])
    
    # def find_scalar_eq_zero(self, b):
    #     b = b / np.linalg.norm(b)

    #     temp = np.array([1.0, 0.0, 0.0])
    #     if np.allclose(b, temp):
    #         temp = np.array([0.0, 1.0, 0.0])
        
    #     u1 = np.cross(b, temp)
    #     u1 /= np.linalg.norm(u1)

    #     return u1
    
    def get_velocity_vector(self, t):
        t1 = t - 15
        if t1 < 0:
            t1 = 0
        A = self.intercepted_plane.get_plane_position(t1, ecef=True)
        B = self.intercepted_plane.get_plane_position(t, ecef=True)

        # A_unit = A / np.linalg.norm(A)
        # B_unit = B / np.linalg.norm(B)

        # w = B_unit - np.dot(A_unit, B_unit) * A_unit 
        # W = w / np.linalg.norm(w)
        # return self.intercepted_plane.get_current_velocity(t) * W
        dt = t - t1 

        v = (B - A) / dt 
        return self.intercepted_plane.get_current_velocity(t) * v / np.linalg.norm(v)
    
    #Wystrzeliwyjemy pocisk w kierunku drona
    def get_starting_projectile_velocity_vector(self):
        # A = self.pos_ecef
        # B = convert_geodetic_to_ecef(self.start_point.latitude + 10, self.start_point.longitude + 10, 120)

        # A_unit = A / np.linalg.norm(A)
        # B_unit = B / np.linalg.norm(B)

        # w = B_unit - np.dot(A_unit, B_unit) * A_unit
        # W = w / np.linalg.norm(w)
        # return self.velocity * W
        target_pos_at_launch = self.intercepted_plane.get_plane_position(self.launch_time, ecef=True)

        direction = target_pos_at_launch - self.pos_ecef
        distance = np.linalg.norm(direction)

        if distance < 1.0:
            return np.array([0.0, 0.0, 0.0])
        
        direction_normalized = direction / distance

        initial_velocity_vector = direction_normalized * self.velocity

        return initial_velocity_vector
    
    # #Narazie dla a biore punkt poczatkowy potestowac co jak dam kropke w trakcie lotu i czy tego nie zmienic na aktualny punkt
    # def calculate_intercept_angle(self, current_time, velocity):
    #     start = time.perf_counter()

    #     a = self.latlon_to_vector(self.intercepted_plane.start_point.latitude, self.intercepted_plane.start_point.longitude)
    #     self.b = self.latlon_to_vector(self.start_point.latitude, self.start_point.longitude)
    #     self.t1 = current_time

    #     u1 = self.find_scalar_eq_zero(self.b)
    #     u2 = 1/self.R * (np.cross(self.b, u1))
    #     u3 = self.b / self.R

    #     # print("u1 * u2: ", np.dot(u1, u2))
    #     # print("u1 * u3: ", np.dot(u1, u3))
    #     # print("u2 * u3: ", np.dot(u2, u3))

    #     # print("u1 * u1: ", np.dot(u1, u1))
    #     # print("u2 * u2: ", np.dot(u2, u2))
    #     # print("u3 * u3: ", np.dot(u3, u3))

    #     R0 = np.column_stack((u1, u2, u3))

    #     a_hat = a / self.R
    #     v1 = self.intercepted_plane.calculate_mean_velocity()
    #     v1_vector = self.get_velocity_vector()
    #     v1_hat = v1_vector / v1
    #     omega1 = v1 / self.R
    #     self.omega2 = velocity / self.R

    #     U = R0.T @ a_hat
    #     W = R0.T @ v1_hat

    #     B = -self.omega2 * self.t1 

    #     if omega1 == self.omega2:
    #         theta1_1 = np.arctan2(np.cos(B) - U[2], W[2] + np.sin(B))
    #         theta1_2 = theta1_1 + np.pi
    #         theta_candidates = [theta1_1, theta1_2]

    #         theta1 = None
    #         best_t = float("inf")

    #         for th in theta_candidates:
    #             if th < 0:
    #                 th += 2*np.pi

    #             t = th / omega1
    #             if t > 0 and t < best_t:
    #                 best_t = t
    #                 theta1 = th

    #         self.intercept_time = best_t
    #     else:
    #         A = self.omega2 / omega1
    #         f = lambda theta: U[2]*np.cos(theta) + W[2]*np.sin(theta) - np.cos(A*theta + B)
    #         fprime = lambda theta: -U[2]*np.sin(theta) + W[2]*np.cos(theta) + A*np.sin(A*theta + B)

    #         sol = optimize.root_scalar(f, x0=0.1, fprime=fprime, method='newton')
    #         theta1 = sol.root
    #         t = theta1 / omega1
    #         self.intercept_time = t
    #     # self.intercept_time = theta1 / self.omega #czas kolizji
    #     print(self.intercept_time)

    #     self.theta = np.arctan2(U[1]*np.cos(theta1) + W[1]*np.sin(theta1), U[0]*np.cos(theta1) + W[0]*np.sin(theta1))
    #     self.v2_hat = np.cos(self.theta) * u1 + np.sin(self.theta) * u2

    #     end = time.perf_counter()
    #     print(f"Czas wykonania calculate_intercept_angle: {end - start:.6f} s")
    
    # def calculate_current_cords(self, t):
    #     # if t > self.intercept_time:
    #     #     return 0.0, 0.0
        
    #     x, y, z = self.b * np.cos(self.omega2*(t-self.t1)) + self.R * self.v2_hat * np.sin(self.omega2*(t-self.t1))

    #     self.current_lat = np.degrees(np.arctan2(z, np.sqrt(x**2 + y**2)))
    #     self.current_lon = np.degrees(np.arctan2(y, x))

    #     return self.current_lat, self.current_lon