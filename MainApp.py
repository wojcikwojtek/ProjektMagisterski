from PySide6 import QtWidgets, QtCore
from MapWindowWidget import MapWindowWidget
from WindowWidget import WindowWidget
from Point import Point
from datetime import datetime
from Plane import Plane
from Globe3DWidget import Globe3DWidget
from MapWidget import MapWidget
from Projectile import Projectile

class MainApp(QtWidgets.QMainWindow):
    flights_data = [
        {
            "id": 1, 
            "waypoints": [
                {
                    "name": "Warszawa", 
                    "point": Point(52.159499362, 20.966996132, datetime(2026, 3, 14, 8, 0, 0))
                },
                {
                    "name": "Nowy Jork",
                    "point": Point(40.641766, -73.780968, datetime(2026, 3, 14, 16, 0, 0))
                }
            ]
        },
        {
            "id": 2, 
            "waypoints": [
                {
                    "name": "Warszawa", 
                    "point": Point(52.159499362, 20.966996132, datetime(2026, 3, 14, 8, 0, 0))
                },
                {
                    "name": "Gdańsk",
                    "point": Point(54.3775, 18.466111, datetime(2026, 3, 14, 8, 28, 0)) 
                },
                {
                    "name": "Szczecin",
                    "point": Point(53.4285, 14.5528, datetime(2026, 3, 14, 8, 56, 0))
                },
                {
                    "name": "Berlin",
                    "point": Point(52.3666652, 13.501997992, datetime(2026, 3, 14, 9, 9, 0))
                }
            ]
        },
        {
            "id": 3, 
            "waypoints": [
                {
                    "name": "Tokio", 
                    "point": Point(35.549083, 139.784597, datetime(2026, 3, 22, 10, 0, 0))
                },
                {
                    "name": "Sydney",
                    "point": Point(-33.947346, 151.177222, datetime(2026, 3, 22, 19, 45, 0))
                }
            ]
        }
    ]

    def __init__(self):
        super().__init__()

        self.setWindowTitle("App")
        self.resize(1000, 700)

        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.start_screen = self.create_start_screen()
        self.stack.addWidget(self.start_screen)

        # self.map_screen = MapWindowWidget()
        self.map_screen = WindowWidget(MapWidget())
        self.stack.addWidget(self.map_screen)
        self.map_screen.go_back.connect(self.show_start_screen)
        self.map_screen.switch_view.connect(self.switch_view)

        self.globe_screen = WindowWidget(Globe3DWidget())
        self.stack.addWidget(self.globe_screen)
        self.globe_screen.go_back.connect(self.show_start_screen)
        self.globe_screen.switch_view.connect(self.switch_view)

        self.use_3d = False

    def create_start_screen(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        title = QtWidgets.QLabel("Wybierz lot do wizualizacji")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px;")

        # button = QtWidgets.QPushButton("Start")
        # button.clicked.connect(self.visualize_flight)

        self.flight_list = QtWidgets.QListWidget()
        for flight in self.flights_data:
            flight_label = f"{flight['id']}:"
            for i in range(len(flight["waypoints"])):
                waypoint = flight['waypoints'][i]
                flight_label += f" {waypoint['name']}"
                if i != len(flight["waypoints"]) - 1:
                    flight_label += " ->"
            item = QtWidgets.QListWidgetItem(flight_label)
            item.setData(QtCore.Qt.UserRole, flight)
            self.flight_list.addItem(item)

        self.flight_list.itemClicked.connect(self.visualize_flight)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(self.flight_list)
        layout.addStretch()

        return widget
    
    def show_start_screen(self):
        self.stack.setCurrentIndex(0)
        if self.use_3d:
            self.globe_screen.clear()
            if self.globe_screen.simulation_view.plane_popup.isVisible():
                self.globe_screen.simulation_view.plane_popup.hide()
        else:
            self.map_screen.clear()
            if self.map_screen.simulation_view.plane_popup.isVisible():
                self.map_screen.simulation_view.plane_popup.hide()
    
    def visualize_flight(self, item):
        flight_data = item.data(QtCore.Qt.UserRole)
        points = [wp["point"] for wp in flight_data["waypoints"]]

        plane = Plane(points)
        if self.use_3d:
            for point in points:
                self.globe_screen.simulation_view.add_point(
                    point.latitude,
                    point.longitude
                )
            self.globe_screen.add_plane(plane)
            self.globe_screen.add_projectile(Projectile(Point(0.0, 0.0, None), plane, 0, 0, disabled=True))

            self.stack.setCurrentWidget(self.globe_screen)            
        else:
            for point in points:
                self.map_screen.simulation_view.add_point(
                    point.latitude,
                    point.longitude
                )
            self.map_screen.add_plane(plane)
            self.stack.setCurrentWidget(self.map_screen)

    def switch_view(self, clock, plane, projectile):
        if self.use_3d:
            if hasattr(self.map_screen, "plane"):
                self.map_screen.clock = clock
            else:
                for point in plane.points:
                    self.map_screen.simulation_view.add_point(
                        point.latitude,
                        point.longitude
                    )
                self.map_screen.add_plane(plane, clock)
            if projectile is not None and projectile.disabled == False:
                if not hasattr(self.map_screen, "projectile"):
                    self.map_screen.add_projectile(projectile)
            if self.map_screen.clock.paused:
                self.map_screen.toggle_pause()
                self.map_screen.animate_plane()
                self.map_screen.toggle_pause()
            if self.globe_screen.simulation_view.plane_popup.isVisible():
                self.globe_screen.simulation_view.plane_popup.hide()
            self.map_screen.spinbox.setValue(self.globe_screen.spinbox.value())
            self.stack.setCurrentWidget(self.map_screen)
            self.use_3d = False 
        else:
            if hasattr(self.globe_screen, "plane"):
                self.globe_screen.clock = clock
            else:
                for point in plane.points:
                    self.globe_screen.simulation_view.add_point(
                        point.latitude,
                        point.longitude
                    )
                self.globe_screen.add_plane(plane, clock)
                self.globe_screen.add_projectile(Projectile(Point(0.0, 0.0, None), plane, 0, 0, disabled=True))
            if projectile is not None and projectile.disabled == False:
                self.globe_screen.projectile = projectile
            if self.globe_screen.clock.paused:
                self.globe_screen.toggle_pause()
                self.globe_screen.animate_plane()
                self.globe_screen.toggle_pause()
            if self.map_screen.simulation_view.plane_popup.isVisible():
                self.map_screen.simulation_view.plane_popup.hide()
            self.globe_screen.spinbox.setValue(self.map_screen.spinbox.value())
            self.stack.setCurrentWidget(self.globe_screen)
            self.use_3d = True