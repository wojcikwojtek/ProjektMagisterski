from PySide6 import QtWidgets, QtCore

class PlaneInfoPopup(QtWidgets.QFrame):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setWindowFlags(QtCore.Qt.SubWindow)

        self.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 20, 220);
                border: 1px solid white;
                border-radius: 6px;
            }
            QLabel {
                color: white;
                padding: 6px;
            }
        """)

        self.label = QtWidgets.QLabel()
        self.label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.label)

    def set_text(self, text):
        self.label.setText(text)
        self.adjustSize()