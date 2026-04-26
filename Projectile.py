import numpy as np
from Plane import Plane
from Point import Point
from scipy import optimize

class Projectile():
    R = 6371e3

    def __init__(self, start_point: Point, intercepted_plane: Plane, current_time: float, velocity: float, disabled = False):
        self.start_point = start_point
        self.intercepted_plane = intercepted_plane
        self.disabled = disabled
        if not disabled:
            self.calculate_intercept_angle(current_time, velocity)

    def latlon_to_vector(self, lat, lon):
        lat_rad = np.radians(lat)
        lon_rad = np.radians(lon)

        return np.array([
            self.R * np.cos(lat_rad) * np.cos(lon_rad),
            self.R * np.cos(lat_rad) * np.sin(lon_rad),
            self.R * np.sin(lat_rad)
        ])
    
    def find_scalar_eq_zero(self, b):
        b = b / np.linalg.norm(b)

        temp = np.array([1.0, 0.0, 0.0])
        if np.allclose(b, temp):
            temp = np.array([0.0, 1.0, 0.0])
        
        u1 = np.cross(b, temp)
        u1 /= np.linalg.norm(u1)

        return u1
    
    def get_velocity_vector(self):
        A = self.latlon_to_vector(self.intercepted_plane.start_point.latitude, self.intercepted_plane.start_point.longitude)
        B = self.latlon_to_vector(self.intercepted_plane.end_point.latitude, self.intercepted_plane.end_point.longitude)

        # a_hat = A / np.linalg.norm(A)
        # b_hat = B / np.linalg.norm(B)

        # normal = np.cross(a_hat, b_hat)
        # normal /= np.linalg.norm(normal)

        # # v_hat = np.cross(normal, a_hat)
        # v_hat = np.cross(a_hat, normal)
        # v_hat /= np.linalg.norm(v_hat)

        # return self.intercepted_plane.calculate_mean_velocity() * v_hat
        A_unit = A / np.linalg.norm(A)
        B_unit = B / np.linalg.norm(B)

        w = B_unit - np.dot(A_unit, B_unit) * A_unit 
        W = w / np.linalg.norm(w)
        return self.intercepted_plane.calculate_mean_velocity() * W
    
    #Narazie dla a biore punkt poczatkowy potestowac co jak dam kropke w trakcie lotu i czy tego nie zmienic na aktualny punkt
    def calculate_intercept_angle(self, current_time, velocity):
        #zakladam ze omega1 = omega2 czyli ze poruszaja sie z ta sama predkoscia
        a = self.latlon_to_vector(self.intercepted_plane.start_point.latitude, self.intercepted_plane.start_point.longitude)
        self.b = self.latlon_to_vector(self.start_point.latitude, self.start_point.longitude)
        self.t1 = current_time

        u1 = self.find_scalar_eq_zero(self.b)
        u2 = 1/self.R * (np.cross(self.b, u1))
        u3 = self.b / self.R

        # print("u1 * u2: ", np.dot(u1, u2))
        # print("u1 * u3: ", np.dot(u1, u3))
        # print("u2 * u3: ", np.dot(u2, u3))

        # print("u1 * u1: ", np.dot(u1, u1))
        # print("u2 * u2: ", np.dot(u2, u2))
        # print("u3 * u3: ", np.dot(u3, u3))

        R0 = np.column_stack((u1, u2, u3))

        a_hat = a / self.R
        v1 = self.intercepted_plane.calculate_mean_velocity()
        v1_vector = self.get_velocity_vector()
        v1_hat = v1_vector / v1
        omega1 = v1 / self.R
        self.omega2 = velocity / self.R

        U = R0.T @ a_hat
        W = R0.T @ v1_hat

        B = -self.omega2 * self.t1 

        if omega1 == self.omega2:
            theta1_1 = np.arctan2(np.cos(B) - U[2], W[2] + np.sin(B))
            theta1_2 = theta1_1 + np.pi
            theta_candidates = [theta1_1, theta1_2]

            theta1 = None
            best_t = float("inf")

            for th in theta_candidates:
                if th < 0:
                    th += 2*np.pi

                t = th / omega1
                if t > 0 and t < best_t:
                    best_t = t
                    theta1 = th

            self.intercept_time = best_t
        else:
            A = self.omega2 / omega1
            f = lambda theta: U[2]*np.cos(theta) + W[2]*np.sin(theta) - np.cos(A*theta + B)
            fprime = lambda theta: -U[2]*np.sin(theta) + W[2]*np.cos(theta) + A*np.sin(A*theta + B)

            sol = optimize.root_scalar(f, x0=0.1, fprime=fprime, method='newton')
            theta1 = sol.root
            t = theta1 / omega1
            self.intercept_time = t
        # self.intercept_time = theta1 / self.omega #czas kolizji
        print(self.intercept_time)

        self.theta = np.arctan2(U[1]*np.cos(theta1) + W[1]*np.sin(theta1), U[0]*np.cos(theta1) + W[0]*np.sin(theta1))
        self.v2_hat = np.cos(self.theta) * u1 + np.sin(self.theta) * u2
    
    def calculate_current_cords(self, t):
        # if t > self.intercept_time:
        #     return 0.0, 0.0
        
        x, y, z = self.b * np.cos(self.omega2*(t-self.t1)) + self.R * self.v2_hat * np.sin(self.omega2*(t-self.t1))

        self.current_lat = np.degrees(np.arctan2(z, np.sqrt(x**2 + y**2)))
        self.current_lon = np.degrees(np.arctan2(y, x))

        return self.current_lat, self.current_lon