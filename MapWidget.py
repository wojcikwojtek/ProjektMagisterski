import numpy as np
from PySide6 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from Plane import Plane
from Projectile import Projectile
from SimulationClock import SimulationClock
from MapViewBox import MapViewBox
from Point import Point

class MapWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)

        self.graph_widget = pg.GraphicsLayoutWidget()
        layout.addWidget(self.graph_widget)

        self.view = MapViewBox()
        self.graph_widget.addItem(self.view)
        # self.view.clicked.connect(self.clicked_on_map)
        
        self.graph_widget.setBackground('#0f172a')

        self.draw_world()

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
    
    def add_projectile(self, projectile: Projectile):
        lat, lon = projectile.start_point.latitude, projectile.start_point.longitude
        self.projectile_item = pg.ScatterPlotItem(
            x=[lon],
            y=[lat],
            size=8,
            brush='yellow',
            pen=pg.mkPen('white', width=1)
        )

        self.view.addItem(self.projectile_item)

    def update_plane_pos(self, lat, lon):
        self.plane_item.setData(x=[lon], y=[lat])

    def update_projectile_pos(self, lat, lon):
        self.projectile_item.setData(x=[lon], y=[lat])

    def clear(self):
        for p in self.points:
            self.view.removeItem(p)
        self.points.clear()

        self.view.removeItem(self.plane_item)
        delattr(self, 'plane_item')

        if hasattr(self, 'projectile_item'):
            self.view.removeItem(self.projectile_item)