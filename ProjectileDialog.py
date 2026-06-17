from PySide6 import QtWidgets, QtCore, QtGui

class ProjectileDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Ustawienia pocisku")

        layout = QtWidgets.QVBoxLayout(self)

        self.pursuitCurve = QtWidgets.QRadioButton("Psia Krzywa")
        self.pip = QtWidgets.QRadioButton("Predictive Interceptive Point")
        self.proportionalNavigation = QtWidgets.QRadioButton("Proportional Navigation")

        self.pursuitCurve.setChecked(True)

        layout.addWidget(self.pursuitCurve)
        layout.addWidget(self.pip)
        layout.addWidget(self.proportionalNavigation)

        layout.addWidget(QtWidgets.QLabel("Prędkość [m/s]:"))
        self.value_edit = QtWidgets.QLineEdit()

        validator = QtGui.QDoubleValidator()
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)

        self.value_edit.setValidator(validator)
        self.value_edit.setText("0.0")

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

        value = float(self.value_edit.text() or 0)

        return option, value