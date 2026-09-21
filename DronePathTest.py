import numpy as np
from scipy.optimize import root
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def compute_heading_vectors(points):
    headings = []

    for i in range(len(points)-1):
        d = points[i+1] - points[i]
        headings.append(d / np.linalg.norm(d))

    headings.append(headings[-1])

    return headings

def turning_radius(phi, va, load_factor, g = 9.81):
    return va**2 / (g * (-np.sin(phi) + np.sqrt(load_factor**2 + np.sin(phi)**2 - 1.0)))

def residual(
    X,
    X0,
    Xf,
    v1,
    v2,
    va,
    nmax
):
    x = X / np.linalg.norm(X)

    gamma1 = np.arccos(
        np.clip(v1 @ x, -1.0, 1.0)
    )

    gamma2 = np.arccos(
        np.clip(v2 @ x, -1.0, 1.0)
    )

    U1 = np.cross(x, v1)

    u1 = U1 / np.linalg.norm(U1)

    phi1 = np.arccos(
        np.clip(u1[2], -1.0, 1.0)
    )

    r1 = turning_radius(phi1, va, nmax)

    U2 = np.cross(x, v2)

    u2 = U2 / np.linalg.norm(U2)

    phi2 = np.arccos(
        np.clip(u2[2], -1.0, 1.0)
    )

    r2 = turning_radius(phi2, va, nmax)

    rhs = Xf - X0 - r1 * np.tan(gamma1/2) * (x + v1) - r2 * np.tan(gamma2/2) * (x + v2)

    lam = rhs @ x

    lhs = lam * x

    return lhs - rhs

    # return X - rhs

def compute_path(X0, Xf, v_start, v_end, va, nmax):
    guess = Xf - X0
    guess /= np.linalg.norm(guess)

    sol = root(
        residual,
        guess,
        args=(
            X0,
            Xf,
            v_start,
            v_end,
            va,
            nmax
        )
    )

    x = sol.x
    x /= np.linalg.norm(x)

    gamma1 = np.arccos(v_start @ x)
    gamma2 = np.arccos(v_end @ x)

    U1 = np.cross(x, v_start)
    U2 = np.cross(x, v_end)

    u1 = U1 / np.linalg.norm(U1)
    u2 = U2 / np.linalg.norm(U2)

    phi1 = np.arccos(u1[2])
    phi2 = np.arccos(u2[2])

    r1 = turning_radius(phi1, va, nmax)
    r2 = turning_radius(phi2, va, nmax)

    W1 = np.cross(v_start, U1)
    W2 = np.cross(-v_end, U2)

    w1 = W1 / np.linalg.norm(W1)
    w2 = W2 / np.linalg.norm(W2)

    O1 = X0 + r1*w1
    O2 = Xf + r2*w2

    Y1 = np.cross(x, U1)
    Y2 = np.cross(-x, U2)

    y1 = Y1 / np.linalg.norm(Y1)
    y2 = Y2 / np.linalg.norm(Y2)

    P1 = O1 - r1*y1
    P2 = O2 - r2*y2

    length = (
        r1*gamma1
        +
        np.linalg.norm(P2-P1)
        +
        r2*gamma2
    )

    t_vals = np.linspace(0, 1, 50)

    # Łuk 1 (Arc 1): od X0 do P1 za pomocą interpolacji sferycznej (SLERP)
    vec_start1 = X0 - O1
    vec_end1 = P1 - O1
    arc1 = np.array([
        O1 + (np.sin((1 - t) * gamma1) / np.sin(gamma1)) * vec_start1 + 
            (np.sin(t * gamma1) / np.sin(gamma1)) * vec_end1 
        for t in t_vals
    ])

    # Łuk 2 (Arc 2): od P2 do Xf za pomocą interpolacji sferycznej (SLERP)
    vec_start2 = P2 - O2
    vec_end2 = Xf - O2
    arc2 = np.array([
        O2 + (np.sin((1 - t) * gamma2) / np.sin(gamma2)) * vec_start2 + 
            (np.sin(t * gamma2) / np.sin(gamma2)) * vec_end2 
        for t in t_vals
    ])

    return {
        "arc1": arc1, 
        "arc2": arc2, 
        "P1": P1,
        "P2": P2,
        "length": length
    }

def convert_geodetic_to_ecef(lat, lon, height):
    a = 6378137.0 #equatorial radius in m
    b = 6356752.3 #polar radius in km

    lat = np.radians(lat)
    lon = np.radians(lon)

    N = a**2 / np.sqrt((a**2 * np.cos(lat)**2) + (b**2 * np.sin(lat)**2))

    X = (N + height)*np.cos(lat)*np.cos(lon)
    Y = (N + height)*np.cos(lat)*np.sin(lon)
    Z = ((b**2/a**2)*N + height)*np.sin(lat)

    return (X, Y, Z)

def convert_ecef_to_geodetic(X, Y, Z):
    a = 6378137.0      # promień równikowy [m]
    b = 6356752.3      # promień biegunowy [m]

    e2 = 1 - (b**2 / a**2)      # pierwsza mimośrodowość²
    ep2 = (a**2 / b**2) - 1     # druga mimośrodowość²

    lon = np.arctan2(Y, X)

    p = np.sqrt(X**2 + Y**2)

    theta = np.arctan2(Z * a, p * b)

    lat = np.arctan2(
        Z + ep2 * b * np.sin(theta)**3,
        p - e2 * a * np.cos(theta)**3
    )

    N = a / np.sqrt(1 - e2 * np.sin(lat)**2)

    height = p / np.cos(lat) - N

    lat = np.degrees(lat)
    lon = np.degrees(lon)

    return lat, lon, height

# waypoints = [
#     ("Warsaw",   52.2297, 21.0122, 120),
#     ("Gdansk",   54.3520, 18.6466, 120),
#     ("Szczecin", 53.4285, 14.5528, 120),
#     ("Berlin",   52.5200, 13.4050, 120),
# ]

# va = 15.0      # m/s
# nmax = 1.2002
# g = 9.81

# X0 = np.array([0.0, 0.0, 0.0])
# # # X0 = np.array(convert_geodetic_to_ecef(52.2297, 21.0122, 120))
# v1 = np.array([1.0, 1.0, 1.0])/np.sqrt(3)
# X1 = np.array([-300.0, 400.0, 500.0])
# # # X1 = np.array(convert_geodetic_to_ecef(54.3520, 18.6466, 120))
# v2 = np.array([1.0, 1.0, 1.0])/np.sqrt(3)
# # # X2 = np.array([100.0, 200.0, 600.0])
# # # X2 = np.array(convert_geodetic_to_ecef(53.4285, 14.5528, 120))
# # # v3 = np.array([1.0, 1.0, 1.0])/np.sqrt(3)

# # # direction_raw = X1 - X0 
# # # up_0 = X0 / np.linalg.norm(X0)
# # # v1_local = direction_raw - np.dot(direction_raw, up_0) * up_0
# # # v1 = v1_local / np.linalg.norm(v1_local)

# # # up_1 = X1 / np.linalg.norm(X1)
# # # v2_local = direction_raw - np.dot(direction_raw, up_1) * up_1
# # # v2 = v2_local / np.linalg.norm(v2_local)

# result = compute_path(X0, X1, v1, v2, va, nmax)

# arc1 = result["arc1"]
# arc2 = result["arc2"]
# P1 = result["P1"]
# P2 = result["P2"]
# length = result["length"]

# # result1 = compute_path(X1, X2, v2, v3, va, nmax)
# # arc2_1 = result1["arc1"]
# # arc3 = result1["arc2"]
# # P2_1 = result1["P1"]
# # P3 = result1["P2"]
# # length_1 = result1["length"]

# line = np.linspace(P1, P2, 200)


# #[1:] żeby nie powielać puntków
# trajectory = np.vstack([
#     arc1,
#     line[1:],
#     arc2[1:],
# #     arc2_1[1:],
# #     line_1[1:],
# #     arc3[1:]
# ])

# #dlugosc skumulowana
# ds = np.linalg.norm(
#     np.diff(trajectory, axis=0),
#     axis=1
# )

# cum_s = np.concatenate([
#     [0],
#     np.cumsum(ds)
# ])


# # 3. Konfiguracja wykresu 3D
# fig = plt.figure(figsize=(10, 8))
# ax = fig.add_subplot(111, projection='3d')

# # Rysowanie poszczególnych segmentów
# ax.plot(arc1[:, 0], arc1[:, 1], arc1[:, 2], 'r-', linewidth=2.5, label='Zakręt początkowy')
# ax.plot(line[:, 0], line[:, 1], line[:, 2], 'g-', linewidth=2.5, label='Lot prostoliniowy')
# ax.plot(arc2[:, 0], arc2[:, 1], arc2[:, 2], 'b-', linewidth=2.5, label='Zakręt końcowy')

# # ax.plot(arc2_1[:, 0], arc2_1[:, 1], arc2_1[:, 2], 'r-', linewidth=2.5, label='Zakręt początkowy1')
# # ax.plot(line_1[:, 0], line_1[:, 1], line_1[:, 2], 'g-', linewidth=2.5, label='Lot prostoliniowy1')
# # ax.plot(arc3[:, 0], arc3[:, 1], arc3[:, 2], 'b-', linewidth=2.5, label='Zakręt końcowy1')

# # Zaznaczenie punktów kluczowych
# ax.scatter(*X0, color='black', s=60, label='X0 (Start)', zorder=5)
# ax.scatter(*X1, color='black', s=60, label='Xf (Koniec)', zorder=5)
# ax.scatter(*P1, color='orange', s=40, label='P1 (Koniec zakrętu 1)')
# ax.scatter(*P2, color='purple', s=40, label='P2 (Początek zakrętu 2)')

# # ax.scatter(*X1, color='black', s=60, label='X1 (Start)', zorder=5)
# # ax.scatter(*X2, color='black', s=60, label='X2 (Koniec)', zorder=5)
# # ax.scatter(*P2_1, color='orange', s=40, label='P2_1 (Koniec zakrętu 1)')
# # ax.scatter(*P3, color='purple', s=40, label='P3 (Początek zakrętu 2)')

# # Opisy osi i legenda
# ax.set_xlabel('Oś X [m]')
# ax.set_ylabel('Oś Y [m]')
# ax.set_zlabel('Oś Z [m]')
# ax.set_title('Wizualizacja Trajektorii Lotu Drona 3D')
# ax.legend()

# # Wyświetlenie wykresu
# plt.tight_layout()

# # # # total_length = cum_s[-1]
# # # # total_time = total_length / va

# # # # drone, = ax.plot(
# # # #     [trajectory[0,0]],
# # # #     [trajectory[0,1]],
# # # #     [trajectory[0,2]],
# # # #     'ro',
# # # #     markersize=15
# # # # )

# # # # fps = 30
# # # # nframes = int(total_time * fps)

# # # # def update(frame):
# # # #     t = frame / fps 

# # # #     t = t * 1000

# # # #     s = va * t 

# # # #     if s >= total_length:
# # # #         s = total_length

# # # #     idx = np.searchsorted(cum_s, s)

# # # #     if idx == 0:
# # # #         pos = trajectory[0]

# # # #     elif idx >= len(trajectory):
# # # #         pos = trajectory[-1]

# # # #     else:
# # # #         s0 = cum_s[idx - 1]
# # # #         s1 = cum_s[idx]

# # # #         alpha = (s - s0) / (s1 - s0)

# # # #         pos = (
# # # #             (1 - alpha) * trajectory[idx - 1]
# # # #             + alpha * trajectory[idx]
# # # #         )
    
# # # #     drone.set_data([pos[0]], [pos[1]])
# # # #     drone.set_3d_properties([pos[2]])

# # # #     return drone,

# # # # ani = FuncAnimation(
# # # #     fig,
# # # #     update,
# # # #     frames=nframes,
# # # #     interval=1000/fps,
# # # #     blit=False
# # # # )

# # # plt.show()

# # fig = plt.figure(figsize=(12, 10))
# # ax = fig.add_subplot(111, projection='3d')

# # # trajektoria myszy (drona)
# # ax.plot(
# #     trajectory[:,0],
# #     trajectory[:,1],
# #     trajectory[:,2],
# #     'b',
# #     linewidth=3,
# #     label='Mysz (trajektoria drona)'
# # )

# # # trajektoria kota
# # ax.plot(
# #     cat_path[:,0],
# #     cat_path[:,1],
# #     cat_path[:,2],
# #     'r',
# #     linewidth=3,
# #     label='Kot (krzywa pościgu)'
# # )

# # # pozycje startowe
# # ax.scatter(
# #     *trajectory[0],
# #     color='blue',
# #     s=80,
# #     label='Start myszy'
# # )

# # ax.scatter(
# #     *cat_path[0],
# #     color='red',
# #     s=80,
# #     label='Start kota'
# # )

# # # pozycje końcowe
# # ax.scatter(
# #     *mouse_path[-1],
# #     color='cyan',
# #     s=80,
# #     label='Pozycja myszy'
# # )

# # ax.scatter(
# #     *cat_path[-1],
# #     color='darkred',
# #     s=80,
# #     label='Pozycja kota'
# # )

# # ax.set_xlabel('X [m]')
# # ax.set_ylabel('Y [m]')
# # ax.set_zlabel('Z [m]')

# # ax.set_title('Pościg kota za myszą')

# # ax.legend()

# # # zachowanie proporcji osi
# # all_points = np.vstack([
# #     trajectory,
# #     cat_path
# # ])

# # x_limits = [all_points[:,0].min(), all_points[:,0].max()]
# # y_limits = [all_points[:,1].min(), all_points[:,1].max()]
# # z_limits = [all_points[:,2].min(), all_points[:,2].max()]

# # x_range = x_limits[1] - x_limits[0]
# # y_range = y_limits[1] - y_limits[0]
# # z_range = z_limits[1] - z_limits[0]

# # max_range = max(x_range, y_range, z_range)

# # x_mid = np.mean(x_limits)
# # y_mid = np.mean(y_limits)
# # z_mid = np.mean(z_limits)

# # ax.set_xlim(x_mid - max_range/2, x_mid + max_range/2)
# # ax.set_ylim(y_mid - max_range/2, y_mid + max_range/2)
# # ax.set_zlim(z_mid - max_range/2, z_mid + max_range/2)

# # plt.tight_layout()
# plt.show()