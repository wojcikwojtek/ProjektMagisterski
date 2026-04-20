from PySide6 import QtWidgets, QtCore 
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DCore import Qt3DCore
from PySide6.QtGui import QVector3D, QColor, QQuaternion
from PySide6.Qt3DRender import Qt3DRender
import numpy as np
from Plane import Plane
from Projectile import Projectile

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

        self.radius = 10

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
        camera.setPosition(QVector3D(0, 0, self.radius * 4))
        camera.setViewCenter(QVector3D(0, 0, 0))

        self.cam_controller = Qt3DExtras.QOrbitCameraController(self.root)
        self.cam_controller.setCamera(camera) 

    def create_globe(self):
        self.globe_entity = Qt3DCore.QEntity(self.root)

        mesh = Qt3DExtras.QSphereMesh(self.root)
        mesh.setRadius(self.radius)

        texture = Qt3DRender.QTextureLoader(self.root)
        texture.setSource(QtCore.QUrl.fromLocalFile("Land_ocean_ice_2048.jpg"))

        # material = Qt3DExtras.QPhongMaterial(self.root)
        # material.setDiffuse(QColor(200, 200, 200))
        # material.setAmbient(QColor(30, 30, 30))
        material = Qt3DExtras.QDiffuseMapMaterial(self.root)
        material.setDiffuse(texture)

        self.globe_entity.addComponent(mesh)
        self.globe_entity.addComponent(material)

        self.picker = Qt3DRender.QObjectPicker(self.globe_entity)
        self.picker.setHoverEnabled(True)
        # self.picker.clicked.connect(self.on_globe_clicked)

        self.globe_entity.addComponent(self.picker)

        self.globe_transform = Qt3DCore.QTransform()
        # self.globe_transform.setRotationX(45)
        self.globe_entity.addComponent(self.globe_transform)
        self.globe_transform.setRotationY(180)
        self.rotate_globe()

    def rotate_globe(self):
        v_front = self.latlon_to_xyz(0, 0, self.radius).normalized() #punkt ktory ma patrzec na kamere, czyli punkt (0, 0) na globie
        v_north = self.latlon_to_xyz(90, 0, self.radius).normalized() #biegun północny

        target_front = QVector3D(0, 0, 1) #w strone kamery
        target_up = QVector3D(0, 1, 0) #gora ekranu

        #Rotacja frontu na target_front
        q1 = QQuaternion.rotationTo(v_front, target_front)

        #Wektor bieguna północnego po rotacji
        rotated_north = q1.rotatedVector(v_north)

        #Rotacja bieguna pólnocnego na target_up
        q2 = QQuaternion.rotationTo(rotated_north, target_up)

        final_rotation = q2 * q1
        self.globe_transform.setRotation(final_rotation)

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
        #przesuniecie o 180 bo tekstura jest zwalona
        lon = np.radians(-lon - 180) #odwracamy bo idk taki dziwny układ wspolrzednych jest w 3D

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
        lon = -np.degrees(np.atan2(z, x)) + 180 #tu tez musimy odwrocic

        return lat, lon
    
    def add_point(self, lat, lon):
        entity = Qt3DCore.QEntity(self.root)

        mesh = Qt3DExtras.QSphereMesh(self.root)
        mesh.setRadius(0.03)

        material = Qt3DExtras.QPhongMaterial(self.root)
        material.setDiffuse(QColor(255, 0, 0))

        transform = Qt3DCore.QTransform(self.root)

        pos = self.latlon_to_xyz(lat, lon, self.radius)
        pos = self.globe_transform.rotation().rotatedVector(pos)
        transform.setTranslation(pos)

        entity.addComponent(mesh)
        entity.addComponent(material)
        entity.addComponent(transform)
        self.points.append(entity)

    def add_plane(self, plane: Plane):
        entity = Qt3DCore.QEntity(self.root)

        mesh = Qt3DExtras.QSphereMesh(self.root)
        mesh.setRadius(0.03)

        material = Qt3DExtras.QPhongMaterial(self.root)
        material.setDiffuse(QColor(0, 0, 255))

        self.plane_transform = Qt3DCore.QTransform(self.root)

        lat, lon = plane.get_plane_position(0)
        pos = self.latlon_to_xyz(lat, lon, self.radius)
        pos = self.globe_transform.rotation().rotatedVector(pos)
        self.plane_transform.setTranslation(pos)

        entity.addComponent(mesh)
        entity.addComponent(material)
        entity.addComponent(self.plane_transform)

        self.plane_item = entity
        
        # self.timer.start(16)
        # self.clock = SimulationClock(self.starting_speed)
        # self.plane = plane

    def add_projectile(self, projectile: Projectile):
        entity = Qt3DCore.QEntity(self.root)

        mesh = Qt3DExtras.QSphereMesh(self.root)
        mesh.setRadius(0.03)

        material = Qt3DExtras.QPhongMaterial(self.root)
        material.setDiffuse(QColor(255, 255, 0))

        self.projectile_transform = Qt3DCore.QTransform(self.root)

        lat, lon = projectile.start_point.latitude, projectile.start_point.longitude
        pos = self.latlon_to_xyz(lat, lon, self.radius)
        pos = self.globe_transform.rotation().rotatedVector(pos)
        self.projectile_transform.setTranslation(pos)

        entity.addComponent(mesh)
        entity.addComponent(material)
        entity.addComponent(self.projectile_transform)

        self.projectile_item = entity

    def update_plane_pos(self, lat, lon):
        pos = self.latlon_to_xyz(lat, lon, self.radius)
        pos = self.globe_transform.rotation().rotatedVector(pos)
        self.plane_transform.setTranslation(pos)

        self.update_camera_follow()

    def update_projectile_pos(self, lat, lon):
        pos = self.latlon_to_xyz(lat, lon, self.radius)
        pos = self.globe_transform.rotation().rotatedVector(pos)
        self.projectile_transform.setTranslation(pos)

    def update_camera_follow(self):
        if not hasattr(self, "plane_transform"):
            return
        
        plane_pos = self.plane_transform.translation()

        offset = QVector3D(0, 2, 5)

        camera = self.view.camera()
        camera.setPosition(plane_pos + offset)
        camera.setViewCenter(plane_pos)

    def clear(self):
        for p in self.points:
            p.setParent(None)
            p.deleteLater()
        self.points.clear()

        self.plane_item.setParent(None)
        self.plane_item.deleteLater()
        delattr(self, 'plane_item')
        delattr(self, 'plane_transform')

        if hasattr(self, 'projectile_item'):
            self.projectile_item.setParent(None)
            self.projectile_item.deleteLater()
            delattr(self, 'projectile_item')
            delattr(self, 'projectile_transform')