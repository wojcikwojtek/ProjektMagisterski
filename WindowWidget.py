from PySide6 import QtWidgets, QtCore
from Plane import Plane
from Projectile import Projectile
from SimulationClock import SimulationClock
from Point import Point
from MapWidget import MapWidget
from Globe3DWidget import Globe3DWidget
from PySide6.Qt3DRender import Qt3DRender
from DronePathTest import convert_geodetic_to_ecef
from ProjectileDialog import ProjectileDialog

class WindowWidget(QtWidgets.QWidget):
    go_back = QtCore.Signal()
    switch_view = QtCore.Signal(object, object, object)

    #dodać simulation_view: MapWidget | GlobeWidget
    def __init__(self, simulation_view: MapWidget | Globe3DWidget):
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)

        top_bar = QtWidgets.QHBoxLayout()
        layout.addLayout(top_bar)

        self.back_button = QtWidgets.QPushButton("← Powrót")
        top_bar.addWidget(self.back_button)

        self.back_button.clicked.connect(self.go_back.emit)

        self.starting_speed = 1
        self.spinbox = QtWidgets.QSpinBox()
        self.spinbox.setRange(1, 100)
        self.spinbox.setValue(self.starting_speed)
        self.spinbox.setSingleStep(1)
        top_bar.addWidget(self.spinbox)

        self.spinbox.valueChanged.connect(self.on_spinbox_value_changed)

        top_bar.addStretch()

        self.switch_view_button = QtWidgets.QPushButton("Switch View")
        top_bar.addWidget(self.switch_view_button)

        self.switch_view_button.clicked.connect(
            lambda: self.switch_view.emit(
                self.clock, 
                self.plane, 
                self.projectile if hasattr(self, "projectile") else None
            )
        )

        self.simulation_view = simulation_view
        layout.addWidget(self.simulation_view)
        if type(self.simulation_view) == MapWidget:
            self.simulation_view.view.clicked.connect(self.clicked_on_map)
        elif type(self.simulation_view) == Globe3DWidget:
            self.simulation_view.picker.clicked.connect(self.clicked_on_globe)

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

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.animate_plane)

    def add_plane(self, plane: Plane, clock: SimulationClock = None):
        self.simulation_view.add_plane(plane)

        self.timer.start(16)
        if clock is not None:
            self.clock = clock
        else:
            self.clock = SimulationClock(self.starting_speed)
        self.plane = plane
        self.last_timer_t = self.clock.now()
        self.simulation_view.on_plane_clicked.connect(self.on_plane_clicked)

    def add_projectile(self, projectile: Projectile):
        self.simulation_view.add_projectile(projectile)

        self.projectile = projectile

    def animate_plane(self):
        if type(self.simulation_view) == Globe3DWidget:
            self.simulation_view.update_camera_follow()
            
        if not (hasattr(self, "plane") or hasattr(self, "clock")):
            return
        if self.clock.paused:
            return
        
        t = self.clock.now()

        has_projectile = hasattr(self, "projectile") and self.projectile.disabled == False
        # if has_projectile:
        #     if t > self.projectile.intercept_time:
        #         return

        if t > self.plane.T:
            return
        
        #Na potrzeby badan po okreslonym czasie dodajemy pocisk
        # if t >= 60 and not has_projectile:
        #     #10 kilometrow na wschod
            # projectile_start_point = Point(52.159499362, 21.113396132, None)
        #     #25 kilometrow na wschod
            # projectile_start_point = Point(52.159499362, 21.332996132, None)
        #     #50 kilometrow na wschod
            # projectile_start_point = Point(52.159499362, 21.698996132, None)
        #     #pocisk 10% szybszy
        # ------ KURS KOLIZYJNY -------
            # projectile_start_point = Point(52.350000, 20.650000, None)
            # projectile_start_point = Point(53.000000, 19.350000, None)
            # projectile_start_point = Point(53.700000, 17.200000, None)
        # ------ PARABOLA -------------
        # if t >= 8 * 60 and not has_projectile:
        #     projectile_start_point = Point(52.120000000, 21.050000000, None)
        # if t >= 18 * 60 and not has_projectile:
        #     projectile_start_point = Point(52.330000000, 21.190000000, None)
        # if t >= 30 * 60 and not has_projectile:
        #     projectile_start_point = Point(52.210000000, 21.470000000, None)
        # ------ SINUSOIDA ------------
        # if t >= 4 * 60 and not has_projectile:
        #     projectile_start_point = Point(52.255000000, 21.080000000, None)
        # if t >= 18 * 60 and not has_projectile:
        #     projectile_start_point = Point(52.020000000, 21.300000000, None)
        # if t >= 34.5 * 60 and not has_projectile:
        #     projectile_start_point = Point(52.300000000, 21.620000000, None)
        #     projectile_velocity = self.plane.get_current_velocity(t) * 1.3
        #     self.add_projectile(Projectile(projectile_start_point, self.plane, t, 'ProportionalNavigation', projectile_velocity))
        
        lat, lon = self.plane.get_plane_position(t)
        self.simulation_view.update_plane_pos(lat, lon)
        self.change_time_label(t)

        if self.simulation_view.plane_popup.isVisible():
            text = self.get_plane_stats()
            self.simulation_view.plane_popup.set_text(text)
            self.simulation_view.update_plane_popup_position()

        # if has_projectile and t >= self.projectile.t1:
        if has_projectile and self.projectile.disabled == False and t >= self.projectile.launch_time:
            lat, lon = self.projectile.calculate_current_cords(t, self.last_timer_t)
            self.simulation_view.update_projectile_pos(lat, lon)
            #Pomyslec czy check_collision jest w ogole potrzebne jak zatrzymuje sie kiedy osiagne intercept time
            self.check_collison()

        self.last_timer_t = t
        self.change_slider((t / self.plane.T) * 10000)

    def check_collison(self):
        if not (hasattr(self, "plane") or hasattr(self, "projectile")):
            return
        
        tolerance = 0.005

        lat_close = abs(self.plane.pos_geo[0] - self.projectile.pos_geo[0]) < tolerance
        lon_close = abs(self.plane.pos_geo[1] - self.projectile.pos_geo[1]) < tolerance
        
        if lat_close and lon_close:
            # self.timer.stop()
            print("Kolizja")
            t = self.clock.now()
            print("Czas: ", t)
            print("Przebyty dystans: ", self.projectile.distance / 1000.0)
            print(self.plane.pos_geo[0], self.plane.pos_geo[1])
            print(self.projectile.pos_geo[0], self.projectile.pos_geo[1])
            exit()

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
        if hasattr(self, "projectile") and self.projectile.disabled == False:
            if t >= self.projectile.launch_time: 
                lat, lon = self.projectile.calculate_current_cords(t, t-1)
                self.simulation_view.update_projectile_pos(lat, lon)
            else:
                self.simulation_view.update_projectile_pos(
                    self.projectile.start_point.latitude,
                    self.projectile.start_point.longitude
                )
            # if t >= self.projectile.intercept_time:
            #     t = self.projectile.intercept_time
            #     self.change_slider((t / self.plane.T) * 10000)
            pass

        lat, lon = self.plane.get_plane_position(t)
        self.simulation_view.update_plane_pos(lat, lon)
        self.change_time_label(t)
        self.clock.set_value(t)

    def change_slider(self, value):
        self.slider.setValue(value)

    def clicked_on_map(self, lon, lat):
        paused_before_clicked = True
        if self.clock.paused == False:
            paused_before_clicked = False
            self.toggle_pause()

        if hasattr(self, 'projectile'):
            delattr(self, 'projectile')
            self.simulation_view.view.removeItem(self.simulation_view.projectile_item)

        method, velocity, lat, lon, t = self.show_projectile_settings_dialog(lat, lon)
        if method is None:
            if paused_before_clicked == False:
                self.toggle_pause()
            return
        
        point = Point(lat, lon, None)

        # velocity = 1.743 * self.plane.get_current_velocity(t)
        self.add_projectile(Projectile(point, self.plane, t, method, velocity))

        if paused_before_clicked == False:
            self.toggle_pause()

    def clicked_on_globe(self, event):
        if event.button() == Qt3DRender.QPickEvent.Buttons.LeftButton:
            paused_before_clicked = True
            if self.clock.paused == False:
                paused_before_clicked = False
                self.toggle_pause()

            world_pos = event.worldIntersection()
            rotation = self.simulation_view.globe_transform.rotation()
            inv_rotation = rotation.conjugated()
            local_pos = inv_rotation.rotatedVector(world_pos)

            lat, lon = self.simulation_view.xyz_to_latlon(local_pos)
            if hasattr(self, 'projectile'):
                # delattr(self, 'projectile')
                # self.simulation_view.projectile_item.setParent(None)
                # self.simulation_view.projectile_item.deleteLater()
                # delattr(self.simulation_view, 'projectile_item')
                # delattr(self.simulation_view, 'projectile_transform')
                pass
            
            method, velocity, lat, lon, t = self.show_projectile_settings_dialog(lat, lon)
            if method is None:
                if paused_before_clicked == False:
                    self.toggle_pause()
                return
            
            point = Point(lat, lon, None)
            # velocity = 1.743 * self.plane.get_current_velocity(t)
            # self.add_projectile(Projectile(point, self.plane, t, velocity))
            self.projectile.disabled = False
            self.projectile.start_point = point
            self.projectile.velocity = velocity
            self.projectile.pos_geo = [point.latitude, point.longitude, 120]
            self.projectile.pos_ecef = convert_geodetic_to_ecef(point.latitude, point.longitude, 120)
            self.projectile.method = method
            self.launch_time = t
            if self.projectile.method == "PredictiveInterceptivePoint":
                self.predictive_interceptive_point = self.projectile.calculate_predictive_interceptive_point(t)
            elif self.projectile.method == "ProportionalNavigation":
                self.v_M = self.projectile.get_starting_projectile_velocity_vector()

            # self.projectile.calculate_intercept_angle(t, velocity)
            self.simulation_view.update_projectile_pos(lat, lon)

            if paused_before_clicked == False:
                self.toggle_pause()

    def show_projectile_settings_dialog(self, lat, lon):
        t = self.clock.now()

        dialog = ProjectileDialog(
            lat=lat, 
            lon=lon, 
            time=t,
            plane_velocity=self.plane.get_current_velocity(t),
            parent=self
        )

        if dialog.exec():
            option, value, lat, lon, time = dialog.get_values()

            return option, value, lat, lon, time
        else:
            return None, 0, 0, 0, 0

    def get_plane_stats(self):
        stats = self.plane.currentStats()
        text = "\n".join(f"{k}: {v}" for k, v in stats.items())
        return text

    def on_plane_clicked(self):
        text = self.get_plane_stats()

        self.simulation_view.show_plane_popup(text)

    def on_spinbox_value_changed(self, value):
        current_time = self.clock.now()
        self.clock.set_value(current_time)
        self.clock.speed = value

    def clear(self):
        self.timer.stop()
        self.simulation_view.clear()
        self.spinbox.setValue(self.starting_speed)
        
        if(self.clock.paused):
            self.toggle_pause()

        delattr(self, 'plane')
        delattr(self, 'clock')

        if hasattr(self, 'projectile'):
            delattr(self, 'projectile')