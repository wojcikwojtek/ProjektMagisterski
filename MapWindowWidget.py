import numpy as np
from PySide6 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from Plane import Plane
from SimulationClock import SimulationClock

class MapWindowWidget(QtWidgets.QWidget):
    go_back = QtCore.Signal()

    def __init__(self):
        super().__init__()
        # self.setWindowTitle("Natural Earth - wektorowa mapa")
        # self.resize(1000, 600)

        # central = QtWidgets.QWidget()
        #self.setCentralWidget(central)

        layout = QtWidgets.QVBoxLayout(self)

        top_bar = QtWidgets.QHBoxLayout()
        layout.addLayout(top_bar)

        self.back_button = QtWidgets.QPushButton("← Powrót")
        top_bar.addWidget(self.back_button)

        self.back_button.clicked.connect(self.go_back.emit)

        top_bar.addStretch()

        self.graph_widget = pg.GraphicsLayoutWidget()
        layout.addWidget(self.graph_widget)

        controls = QtWidgets.QHBoxLayout()
        layout.addLayout(controls)

        self.pause_button = QtWidgets.QPushButton("Pause")
        controls.addWidget(self.pause_button)

        self.time_label = QtWidgets.QLabel("00:00:00")
        self.time_label.setMinimumWidth(80)
        self.time_label.setAlignment(QtCore.Qt.AlignCenter)
        controls.addWidget(self.time_label)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(0)
        #Mozna dac wiecej by bylo plynniejsze przesuwanie
        self.slider.setMaximum(10000)
        self.slider.setValue(0)
        controls.addWidget(self.slider)

        self.pause_button.clicked.connect(self.toggle_pause)
        self.slider.sliderMoved.connect(self.slider_moved)

        self.view = self.graph_widget.addViewBox()
        self.view.setAspectLocked(True)
        self.view.setRange(xRange=(-180, 180),
                           yRange=(-90, 90))
        self.view.setLimits(
            xMin=-180, xMax=180,
            yMin=-90, yMax=90,
            minXRange=1,
            maxXRange=360,
            minYRange=1,
            maxYRange=180
        )
        
        self.graph_widget.setBackground('#0f172a')

        self.draw_world()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.animate_plane)
        self.timer.start(16) #16 ms ~60 fps

        self.points = []

    def draw_world(self):
        world = gpd.read_file("ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp")

        pen = pg.mkPen(color=(200, 200, 200), width=0.5)
        brush = pg.mkBrush(60, 60, 60)

        for geom in world.geometry:
            if isinstance(geom, Polygon):
                self.add_polygon(geom, pen, brush)
            elif isinstance(geom, MultiPolygon):
                for poly in geom.geoms:
                    self.add_polygon(poly, pen, brush)
    
    def add_polygon(self, polygon, pen, brush):
        path = QtGui.QPainterPath()
        coords = np.array(polygon.exterior.coords)

        path.moveTo(coords[0][0], coords[0][1])
        for x,y in coords[1:]:
            path.lineTo(x, y)
        path.closeSubpath()

        item = QtWidgets.QGraphicsPathItem(path)
        item.setPen(pen)
        item.setBrush(brush)
        self.view.addItem(item)

    def add_point(self, latitude, longitude):
        # self.points.append((latitude, longitude))

        point_item = pg.ScatterPlotItem(
            x=[longitude],
            y=[latitude],
            size=12,
            brush='red',
            pen=pg.mkPen('white', width=1)
        )
        self.view.addItem(point_item)
        self.points.append(point_item)

    def add_plane(self, plane: Plane):
        lat, lon = plane.get_plane_position(0)
        self.plane_item = pg.ScatterPlotItem(
            x=[lon],
            y=[lat],
            size=8,
            brush='blue',
            pen=pg.mkPen('white', width=1)
        )

        self.view.addItem(self.plane_item)

        self.clock = SimulationClock()
        self.plane = plane

    def update_plane_pos(self, t):
        lat, lon = self.plane.get_plane_position(t)
        self.plane_item.setData(x=[lon], y=[lat])
        self.change_time_label(t)

    def animate_plane(self):
        if not (hasattr(self, "plane") or hasattr(self, "clock")):
            return
        if self.clock.paused:
            return
        
        t = self.clock.now()
        if t > self.plane.T:
            return
        self.update_plane_pos(t)
        self.change_slider((t / self.plane.T) * 10000)

    def toggle_pause(self):
        if(self.clock.paused):
            self.pause_button.setText("Pause")
            self.clock.resume()
        else:
            self.pause_button.setText("Resume")
            self.clock.pause()

    def change_time_label(self, seconds):
        seconds = int(seconds)

        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60

        self.time_label.setText(f"{h:02}:{m:02}:{s:02}")

    def slider_moved(self, value):
        t = (value * self.plane.T) / 10000
        self.update_plane_pos(t)
        self.clock.set_value(t)

    def change_slider(self, value):
        self.slider.setValue(value)

    def clear(self):
        for p in self.points:
            self.view.removeItem(p)
        self.points.clear()

        self.view.removeItem(self.plane_item)
        delattr(self, 'plane_item')
        delattr(self, 'plane')
        delattr(self, 'clock')