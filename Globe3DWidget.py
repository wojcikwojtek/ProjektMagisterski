from PySide6 import QtWidgets, QtCore 
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DCore import Qt3DCore
from PySide6.QtGui import QVector3D, QColor
from PySide6.Qt3DRender import Qt3DRender
import numpy as np
from Plane import Plane

class Globe3DWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.view = Qt3DExtras.Qt3DWindow()
        self.view.defaultFrameGraph().setClearColor(QColor(0, 0, 0))
        self.container = QtWidgets.QWidget.createWindowContainer(self.view)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.container)

        self.root = Qt3DCore.QEntity()
        self.view.setRootEntity(self.root)

        self.create_camera()
        self.create_globe()
        self.create_light()

        # self.timer = QtCore.QTimer()
        # self.timer.timeout.connect(self.animate_plane)

        # self.starting_speed = 100
        self.points = []

    def create_camera(self):
        camera = self.view.camera()
        camera.lens().setPerspectiveProjection(45.0, 16/9, 0.1, 1000)
        camera.setPosition(QVector3D(0, 0, 20))
        camera.setViewCenter(QVector3D(0, 0, 0))

        self.cam_controller = Qt3DExtras.QOrbitCameraController(self.root)
        self.cam_controller.setCamera(camera) 

    def create_globe(self):
        self.globe_entity = Qt3DCore.QEntity(self.root)

        mesh = Qt3DExtras.QSphereMesh(self.root)
        self.radius = 5
        mesh.setRadius(self.radius)

        material = Qt3DExtras.QPhongMaterial(self.root)
        material.setDiffuse(QColor(200, 200, 200))
        material.setAmbient(QColor(30, 30, 30))

        self.globe_entity.addComponent(mesh)
        self.globe_entity.addComponent(material)

        self.picker = Qt3DRender.QObjectPicker(self.globe_entity)
        self.picker.setHoverEnabled(True)
        self.picker.clicked.connect(self.on_globe_clicked)

        self.globe_entity.addComponent(self.picker)

    def create_light(self):
        light_entity = Qt3DCore.QEntity(self.root)

        light = Qt3DRender.QPointLight(light_entity)
        light.setIntensity(1)

        transform = Qt3DCore.QTransform(self.root)
        transform.setTranslation(QVector3D(20, 20, 20))

        light_entity.addComponent(light)
        light_entity.addComponent(transform)

    def latlon_to_xyz(self, lat, lon, radius):
        lat = np.radians(lat)
        lon = np.radians(lon)

        # y i z zamienione ze soba bo taki przyjmujemy uklad wspolrzednych gdzie z to wysokosc
        x = radius * np.cos(lat) * np.cos(lon)
        y = radius * np.sin(lat)
        z = radius * np.cos(lat) * np.sin(lon)

        return QVector3D(x, y, z)
    
    def xyz_to_latlon(self, pos):
        x = pos.x()
        y = pos.y()
        z = pos.z()

        r = (x**2 + y**2 + z**2) ** 0.5

        lat = np.degrees(np.asin(y / r))
        lon = np.degrees(np.atan2(z, x))

        return lat, lon
    
    def add_point(self, lat, lon):
        entity = Qt3DCore.QEntity(self.root)

        mesh = Qt3DExtras.QSphereMesh(self.root)
        mesh.setRadius(0.2)

        material = Qt3DExtras.QPhongMaterial(self.root)
        material.setDiffuse(QColor(255, 0, 0))

        transform = Qt3DCore.QTransform(self.root)

        pos = self.latlon_to_xyz(lat, lon, self.radius)
        transform.setTranslation(pos)

        entity.addComponent(mesh)
        entity.addComponent(material)
        entity.addComponent(transform)
        self.points.append(entity)

    def add_plane(self, plane: Plane):
        entity = Qt3DCore.QEntity(self.root)

        mesh = Qt3DExtras.QSphereMesh(self.root)
        mesh.setRadius(0.21)

        material = Qt3DExtras.QPhongMaterial(self.root)
        material.setDiffuse(QColor(0, 0, 255))

        self.plane_transform = Qt3DCore.QTransform(self.root)

        lat, lon = plane.get_plane_position(0)
        pos = self.latlon_to_xyz(lat, lon, self.radius)
        self.plane_transform.setTranslation(pos)

        entity.addComponent(mesh)
        entity.addComponent(material)
        entity.addComponent(self.plane_transform)

        self.plane_item = entity
        
        # self.timer.start(16)
        # self.clock = SimulationClock(self.starting_speed)
        # self.plane = plane

    def update_plane_pos(self, lat, lon):
        pos = self.latlon_to_xyz(lat, lon, self.radius)
        self.plane_transform.setTranslation(pos)
        
    def on_globe_clicked(self, event):
        world_pos = event.worldIntersection()

        lat, lon = self.xyz_to_latlon(world_pos)
        print(f"Lat: {lat:.4f}, Lon: {lon:.4f}")

    def clear(self):
        for p in self.points:
            p.setParent(None)
            p.deleteLater()
        self.points.clear()

        self.plane_item.setParent(None)
        self.plane_item.deleteLater()
        delattr(self, 'plane_item')
        delattr(self, 'plane_transform')