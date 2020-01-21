import math, pyrr
from pyrr import Matrix44, Vector4, Vector3
from util import log


class Camera:
    def __init__(self):
        self._pos = Vector4()
        self.pitch = 0.0
        self.yaw = 10.0
        self.roll = 0.0
        self.dist = 4.0
        self.fovY = 45
        self.aspect_ratio = 1
        self.perspective = True

    def pos(self):
        return self._pos

    def euler(self):
        roll = math.radians(self.roll)
        pitch = math.radians(self.pitch)
        yaw = math.radians(self.yaw)
        return pyrr.euler.create(pitch, roll, yaw)

    def rot(self):
        return Matrix44.from_eulers(self.euler())

    def view(self):
        view = Matrix44.from_translation(-self.pos())
        view = self.rot() * view
        view = Matrix44.from_translation([0.0, 0.0, -self.dist, 0.0]) * view
        return view

    def proj(self):
        if self.perspective == True:
            return Matrix44.perspective_projection(self.fovY, self.aspect_ratio, 0.1, 1000.0)
        else:
            return Matrix44.orthogonal_projection(-1, 1, -1, 1, 0.1, 1000.0)

    def view_proj(self):
        return self.proj() * self.view()
    
    def dolly(self, d):
        self.dist -= d * 0.2

    def orbit(self, dx, dy):
        self.perspective = True
        self.yaw -= dx * 0.5
        self.pitch -= dy * 0.5

    def pan(self, dx, dy):
        dx *= -0.01
        dy *= 0.01
        dv = Vector4([dx, dy, 0.0, 0.0])
        dv = ~self.rot() * dv
        self._pos += dv

    def orthogonal(self, direct, ctrl):
        self.perspective = False
        self.yaw, self.pitch, self.roll = 0.0, 0.0, 0.0
        if direct == 1:
            self.yaw = 0.0 if ctrl == False else 180.0
        elif direct == 3:
            self.yaw = 90.0 if ctrl == False else -90.0
        elif direct == 7:
            self.pitch = -90.0 if ctrl == False else 90.0

