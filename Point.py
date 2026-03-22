from datetime import datetime

class Point():
    def __init__(self, latitude, longitude, time: datetime):
        self.latitude = latitude
        self.longitude = longitude
        self.time = time