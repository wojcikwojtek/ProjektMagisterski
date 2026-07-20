from PySide6 import QtWidgets, QtCore, QtGui

class ProjectileDialog(QtWidgets.QDialog):
    def __init__(self, lat, lon, time, plane_velocity, parent=None):
        super().__init__(parent)

        self.lat = lat 
        self.lon = lon

        self.setWindowTitle("Ustawienia pocisku")

        layout = QtWidgets.QVBoxLayout(self)

        validator = QtGui.QDoubleValidator()
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)

        layout.addWidget(QtWidgets.QLabel("Szerokość geograficzna:"))
        self.lat_edit = QtWidgets.QLineEdit()
        self.lat_edit.setValidator(validator)
        self.lat_edit.setText(f"{lat}")
        layout.addWidget(self.lat_edit)

        layout.addWidget(QtWidgets.QLabel("Długość geograficza:"))
        self.lon_edit = QtWidgets.QLineEdit()
        self.lon_edit.setValidator(validator)
        self.lon_edit.setText(f"{lon}")
        layout.addWidget(self.lon_edit)

        layout.addWidget(QtWidgets.QLabel("Czas wystrzału:"))
        self.time_edit = QtWidgets.QLineEdit()
        self.time_edit.setValidator(validator)
        self.time_edit.setText(f"{time}")
        layout.addWidget(self.time_edit)

        self.pursuitCurve = QtWidgets.QRadioButton("Psia Krzywa")
        self.pip = QtWidgets.QRadioButton("Predictive Interceptive Point")
        self.proportionalNavigation = QtWidgets.QRadioButton("Proportional Navigation")

        self.pursuitCurve.setChecked(True)

        layout.addWidget(self.pursuitCurve)
        layout.addWidget(self.pip)
        layout.addWidget(self.proportionalNavigation)

        layout.addWidget(QtWidgets.QLabel("Prędkość [m/s]:"))
        self.value_edit = QtWidgets.QLineEdit()

        self.value_edit.setValidator(validator)
        self.value_edit.setText(f"{plane_velocity}")

        layout.addWidget(self.value_edit)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok |
            QtWidgets.QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_values(self):
        if self.pursuitCurve.isChecked():
            option = "PursuitCurve"
        elif self.pip.isChecked():
            option = "PredictiveInterceptivePoint"
        else:
            option = "ProportionalNavigation"

        value = float(self.value_edit.text() or 0.0)
        lat = float(self.lat_edit.text() or 0.0)
        lon = float(self.lon_edit.text() or 0.0)
        time = float(self.time_edit.text() or 0.0)

        return option, value, lat, lon, time