import sys 
from PySide6 import QtWidgets
from MainApp import MainApp

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())