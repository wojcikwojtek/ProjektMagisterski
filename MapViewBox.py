import pyqtgraph as pg
from PySide6 import QtCore
from PySide6.QtCore import Qt

class MapViewBox(pg.ViewBox):
    clicked = QtCore.Signal(float, float)

    def __init__(self):
        super().__init__()
        self.setAspectLocked(True)
        self.setRange(xRange=(-180, 180),
                           yRange=(-90, 90))
        self.setLimits(
            xMin=-180, xMax=180,
            yMin=-90, yMax=90,
            minXRange=1,
            maxXRange=360,
            minYRange=1,
            maxYRange=180
        )

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            pos = ev.scenePos()
            mouse_point = self.mapSceneToView(pos)
            #Po nacisnieciu myszki na mapie dodajemy projectile
            x = mouse_point.x()
            y = mouse_point.y()

            self.clicked.emit(x, y)

            # if hasattr(self, 'projectile_item'):
            #     self.removeItem(self.projectile_item)

            # self.projectile_item = pg.ScatterPlotItem(
            #     x=[x],
            #     y=[y],
            #     size=8,
            #     brush='yellow',
            #     pen=pg.mkPen('white', width=1)
            # )
            # self.addItem(self.projectile_item)

        super().mouseClickEvent(ev)