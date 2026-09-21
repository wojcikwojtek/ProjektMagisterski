from PySide6 import QtWidgets, QtCore
from MapWindowWidget import MapWindowWidget
from WindowWidget import WindowWidget
from Point import Point
from datetime import datetime
from Plane import Plane
from Globe3DWidget import Globe3DWidget
from MapWidget import MapWidget
from Projectile import Projectile
from DbConnector import DbConnector

class MainApp(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.dbConnector = DbConnector()

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
        widget.setObjectName("startScreen")

        main_layout = QtWidgets.QVBoxLayout(widget)
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setSpacing(25)

        # =========================================================
        # HEADER
        # =========================================================

        header_layout = QtWidgets.QVBoxLayout()
        header_layout.setSpacing(8)

        title = QtWidgets.QLabel("Wizualizacja lotów")
        title.setObjectName("title")
        title.setAlignment(QtCore.Qt.AlignCenter)

        subtitle = QtWidgets.QLabel(
            "Wybierz lot, aby rozpocząć symulację i analizę jego przebiegu"
        )
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        main_layout.addLayout(header_layout)

        # =========================================================
        # FLIGHT CARD
        # =========================================================

        card = QtWidgets.QFrame()
        card.setObjectName("flightCard")

        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(15)

        list_header = QtWidgets.QLabel("Dostępne loty")
        list_header.setObjectName("listHeader")

        self.flight_list = QtWidgets.QListWidget()
        self.flight_list.setObjectName("flightList")

        self.flight_list.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )

        self.flight_list.setVerticalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel
        )

        self.flight_list.setSpacing(8)

        flights_data = self.dbConnector.getFlights()

        for flight in flights_data:
            flight_label = f"{flight[0]}    {flight[1]}  →  {flight[2]}"

            item = QtWidgets.QListWidgetItem(flight_label)
            item.setData(QtCore.Qt.UserRole, flight)

            self.flight_list.addItem(item)

        self.flight_list.itemClicked.connect(self.visualize_flight)

        card_layout.addWidget(list_header)
        card_layout.addWidget(self.flight_list)

        main_layout.addWidget(card, stretch=1)

        # =========================================================
        # FOOTER
        # =========================================================

        info = QtWidgets.QLabel(
            "Wybierz lot z listy, aby przejść do wizualizacji."
        )
        info.setObjectName("info")
        info.setAlignment(QtCore.Qt.AlignCenter)

        main_layout.addWidget(info)

        # =========================================================
        # STYLE
        # =========================================================

        widget.setStyleSheet("""
            #startScreen {
                background-color: #0a0a0a;
            }

            #title {
                color: #f5f5f5;
                font-size: 34px;
                font-weight: 600;
            }

            #subtitle {
                color: #8a8a8a;
                font-size: 15px;
            }

            #flightCard {
                background-color: #111111;
                border: 1px solid #242424;
                border-radius: 14px;
            }

            #listHeader {
                color: #e5e5e5;
                font-size: 18px;
                font-weight: 600;
                padding-bottom: 5px;
            }

            #flightList {
                background-color: #0a0a0a;
                border: 1px solid #242424;
                border-radius: 10px;
                padding: 8px;
                outline: none;
                color: #e5e5e5;
                font-size: 15px;
            }

            #flightList::item {
                background-color: #161616;
                border: 1px solid #252525;
                border-radius: 8px;
                padding: 14px;
                margin: 2px 0px;
            }

            #flightList::item:hover {
                background-color: #202020;
                border: 1px solid #353535;
            }

            #flightList::item:selected {
                background-color: #2a2a2a;
                border: 1px solid #505050;
                color: #ffffff;
            }

            #info {
                color: #666666;
                font-size: 13px;
            }
        """)

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
        flightId = flight_data[0]
        points_data = self.dbConnector.getPoints(flightId)
        points = [Point(wp[2], wp[3], wp[4]) for wp in points_data]

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
                self.globe_screen.add_projectile(Projectile(Point(0.0, 0.0, None), plane, 0, "", 0, disabled=True))
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