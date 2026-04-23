import numpy as np
from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtGui import QVector3D, QQuaternion

class PlaneCameraController(QObject):
    def __init__(self, camera, view, parent=None):
        super().__init__(parent)
        self.camera = camera 
        self.view = view

        self.distance = 5.0
        self.yaw = 0.0
        self.pitch = 30.0

        self.min_dist = 1.0
        self.max_dist = 20.0

        self.last_mouse_pos = None
        self.is_dragging = False

        self.view.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.RightButton:
                self.is_dragging = True 
                self.last_mouse_pos = event.position()
                return True 
            
        elif event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.RightButton:
                self.is_dragging = False
                return True 
            
        elif event.type() == QEvent.MouseMove:
            if self.is_dragging and self.last_mouse_pos:
                delta = event.position() - self.last_mouse_pos

                self.yaw -= delta.x() * 0.5
                self.pitch -= delta.y() * 0.5

                self.pitch = max(5.0, min(85.0, self.pitch))

                self.last_mouse_pos = event.position()
                return True 
            
        elif event.type() == QEvent.Wheel:
            scroll_delta = event.angleDelta().y() / 120.0
            self.distance -= scroll_delta * 0.5
            self.distance = max(self.min_dist, min(self.max_dist, self.distance))
            return True 
        
        return super().eventFilter(obj, event)
    
    def update_camera(self, plane_pos):
        normal = plane_pos.normalized()

        rad_yaw = np.radians(self.yaw)
        rad_pitch = np.radians(self.pitch)

        x = self.distance * np.cos(rad_pitch) * np.sin(rad_yaw)
        y = self.distance * np.sin(rad_pitch)
        z = self.distance * np.cos(rad_pitch) * np.cos(rad_yaw)
        local_offset = QVector3D(x, y, z)

        surface_rotation = QQuaternion.rotationTo(QVector3D(0, 1, 0), normal)
        world_offset = surface_rotation.rotatedVector(local_offset)

        self.camera.setPosition(plane_pos + world_offset)
        self.camera.setViewCenter(plane_pos)

        self.camera.setUpVector(normal)