from PySide6 import QtWidgets, QtCore
from MapWindowWidget import MapWindowWidget
from WindowWidget import WindowWidget
from Point import Point
from datetime import datetime
from Plane import Plane
from Globe3DWidget import Globe3DWidget
from MapWidget import MapWidget

class MainApp(QtWidgets.QMainWindow):
    flights_data = [
        {
            "id": 1, 
            "from": "Warszawa", 
            "from_point": Point(52.159499362, 20.966996132, datetime(2026, 3, 14, 8, 0, 0)), 
            "to": "Nowy Jork",
            "to_point": Point(40.641766, -73.780968, datetime(2026, 3, 14, 16, 0, 0))
        },
        {
            "id": 2, 
            "from": "Berlin",
            "from_point": Point(52.3666652, 13.501997992, datetime(2026, 3, 22, 15, 0, 0)),
            "to": "Londyn",
            "to_point": Point(51.460266, -0.438965, datetime(2026, 3, 22, 17, 0, 0))
        },
        {
            "id": 3, 
            "from": "Tokio", 
            "from_point": Point(35.549083, 139.784597, datetime(2026, 3, 22, 10, 0, 0)),
            "to": "Sydney",
            "to_point": Point(-33.947346, 151.177222, datetime(2026, 3, 22, 19, 45, 0))
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

        self.globe_screen = WindowWidget(Globe3DWidget())
        self.stack.addWidget(self.globe_screen)
        self.globe_screen.go_back.connect(self.show_start_screen)

        self.use_3d = True

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
            item = QtWidgets.QListWidgetItem(
                f"{flight['id']}: {flight['from']} -> {flight['to']}"
            )
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
        else:
            self.map_screen.clear()
    
    def visualize_flight(self, item):
        flight_data = item.data(QtCore.Qt.UserRole)

        plane = Plane(flight_data['from_point'], flight_data['to_point'])
        if self.use_3d:
            self.globe_screen.simulation_view.add_point(
                flight_data['from_point'].latitude, 
                flight_data['from_point'].longitude
            )
            self.globe_screen.simulation_view.add_point(
                flight_data['to_point'].latitude, 
                flight_data['to_point'].longitude
            )
            self.globe_screen.add_plane(plane)

            self.stack.setCurrentWidget(self.globe_screen)
            
        else:
            self.map_screen.simulation_view.add_point(
                flight_data['from_point'].latitude, 
                flight_data['from_point'].longitude
            )
            self.map_screen.simulation_view.add_point(
                flight_data['to_point'].latitude, 
                flight_data['to_point'].longitude
            )
            self.map_screen.add_plane(plane)

            self.stack.setCurrentWidget(self.map_screen)