import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

from Plane import Plane
from Point import Point
from Projectile import Projectile
from DronePathTest import convert_ecef_to_geodetic


def plot_interception(
    points,
    projectile_start,
    projectile_velocity,
    launch_time,
    method="PursuitCurve"
):
    """
    Wizualizacja trajektorii samolotu oraz pocisku.

    points              - punkty trasy samolotu
    projectile_start    - punkt startowy pocisku
    projectile_velocity - prędkość pocisku [m/s]
    launch_time         - czas rozpoczęcia pościgu [s]
    method              - PursuitCurve / PredictiveInterceptivePoint /
                          ProportionalNavigation
    """

    # ==========================================================
    # SAMOLOT
    # ==========================================================

    plane = Plane(points)

    # Pobranie wygenerowanej trajektorii samolotu
    trajectory_ecef = plane.trajectory

    plane_lat = []
    plane_lon = []
    velocities = []

    for i, position in enumerate(trajectory_ecef):
        lat, lon, alt = convert_ecef_to_geodetic(
            position[0],
            position[1],
            position[2]
        )

        plane_lat.append(lat)
        plane_lon.append(lon)

        # Czas odpowiadający danemu punktowi trajektorii
        t = i * (plane.T / (len(trajectory_ecef) - 1))

        # Aktualna prędkość samolotu
        velocity = plane.get_current_velocity(t)
        velocities.append(velocity)

    # Średnia prędkość
    average_velocity = sum(velocities) / len(velocities)

    print(f"Średnia prędkość samolotu: {average_velocity:.2f} m/s")
    print(f"Średnia prędkość samolotu: {average_velocity * 3.6:.2f} km/h")
        

    # ==========================================================
    # POCISK
    # ==========================================================

    # plane_velocity = plane.get_current_velocity(launch_time)
    # projectile_velocity = plane_velocity * (velocity_percent / 100.0)

    projectile = Projectile(
        start_point=projectile_start,
        intercepted_plane=plane,
        current_time=launch_time,
        method=method,
        velocity=projectile_velocity
    )

    method = "Proportional Navigation"

    projectile_lat = []
    projectile_lon = []

    collision_lat = None
    collision_lon = None

    # Czas symulacji
    dt = 1.0

    t = launch_time

    previous_t = launch_time

    while t <= plane.T:

        # Aktualna pozycja pocisku
        pos_ecef = projectile.calculate_current_cords(
            t,
            previous_t,
            ecef=True
        )

        # Konwersja na współrzędne geograficzne
        lat, lon, alt = convert_ecef_to_geodetic(
            pos_ecef[0],
            pos_ecef[1],
            pos_ecef[2]
        )

        projectile_lat.append(lat)
        projectile_lon.append(lon)

        # Aktualna pozycja samolotu
        plane_pos = plane.get_plane_position(
            t,
            ecef=True
        )

        # Odległość pomiędzy pociskiem a samolotem
        distance = np.linalg.norm(
            plane_pos - pos_ecef
        )

        # Wykrycie przechwycenia
        if distance < 1000:
            collision_lat = lat
            collision_lon = lon
            break

        previous_t = t
        t += dt

    # ==========================================================
    # WYKRES
    # ==========================================================

    fig, ax = plt.subplots(figsize=(12, 7))

    # ----------------------------------------------------------
    # Trajektoria samolotu
    # ----------------------------------------------------------

    ax.plot(
        plane_lon,
        plane_lat,
        linewidth=2,
        label="Trajektoria obiektu ściganego"
    )

    # ----------------------------------------------------------
    # Waypointy
    # ----------------------------------------------------------

    waypoint_lon = [
        point.longitude
        for point in points
    ]

    waypoint_lat = [
        point.latitude
        for point in points
    ]

    ax.scatter(
        waypoint_lon,
        waypoint_lat,
        s=50,
        zorder=3,
        label="Punkty trasy"
    )

    # Numeracja waypointów
    for i, point in enumerate(points):
        ax.annotate(
            f"P{i + 1}",
            (point.longitude, point.latitude),
            xytext=(6, 6),
            textcoords="offset points"
        )

    # ----------------------------------------------------------
    # Trajektoria pocisku
    # ----------------------------------------------------------

    ax.plot(
        projectile_lon,
        projectile_lat,
        linestyle="--",
        linewidth=2,
        label=f"Trajektoria obiektu ścigającego ({method})"
    )

    # ----------------------------------------------------------
    # Punkt startowy pocisku
    # ----------------------------------------------------------

    ax.scatter(
        projectile_start.longitude,
        projectile_start.latitude,
        marker="o",
        s=140,
        zorder=5,
        label="Start obiektu ścigającego"
    )

    # ----------------------------------------------------------
    # Punkt kolizji
    # ----------------------------------------------------------

    if collision_lat is not None:

        ax.scatter(
            collision_lon,
            collision_lat,
            marker="X",
            s=120,
            color="red",
            zorder=6,
            label="Punkt przechwycenia"
        )

        ax.annotate(
            "Przechwycenie",
            (collision_lon, collision_lat),
            xytext=(8, 8),
            textcoords="offset points"
        )

    # ----------------------------------------------------------
    # Opisy
    # ----------------------------------------------------------

    ax.set_xlabel("Długość geograficzna [°]")
    ax.set_ylabel("Szerokość geograficzna [°]")

    ax.set_title(
        f"Trajektoria przechwycenia – {method}"
    )

    ax.grid(True, alpha=0.3)
    ax.legend()

    ax.set_aspect(
        "equal",
        adjustable="box"
    )

    plt.tight_layout()
    plt.show()

# ==========================================================
# URUCHOMIENIE WIZUALIZACJI
# ==========================================================


points = [
    Point(
        52.159499362,
        20.966996132,
        datetime(2026, 3, 14, 8, 0, 0)
    ),
    Point(
        40.641766,
        -73.780968,
        datetime(2026, 3, 14, 16, 0, 0)
    )
]


# Punkt startowy pocisku
projectile_start = Point(50.25841, 19.02754, None)


plot_interception(
    points=points,
    projectile_start=projectile_start,
    projectile_velocity=600,
    launch_time=60,
    method="ProportionalNavigation"
)