import sys 
from PySide6 import QtWidgets
from datetime import datetime
from MapWindowWidget import MapWindowWidget
from MainApp import MainApp
from Point import Point
from Plane import Plane

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    # window = MapWindowWidget()
    # warszawa = Point(52.159499362, 20.966996132, datetime(2026, 3, 14, 8, 0, 0))
    # newyork = Point(40.641766, -73.780968, datetime(2026, 3, 14, 16, 0, 0))
    # window.add_point(warszawa.latitude, warszawa.longitude)
    # window.add_point(newyork.latitude, newyork.longitude)
    # plane = Plane(warszawa, newyork)
    # window.add_plane(plane)
    window.show()
    sys.exit(app.exec())