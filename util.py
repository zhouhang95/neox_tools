import os
import numpy as np
from PyQt5 import QtCore, QtOpenGL
import moderngl

from converter import parse_mesh
from onmyoji_converter import _parse_mesh


class QModernGLWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent=None):
        fmt = QtOpenGL.QGLFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QtOpenGL.QGLFormat.CoreProfile)
        fmt.setSampleBuffers(True)
        self.timer = QtCore.QElapsedTimer()
        super().__init__(fmt, parent=parent)

    def initializeGL(self):
        pass

    def paintGL(self):
        self.ctx = moderngl.create_context()
        self.screen = self.ctx.detect_framebuffer()
        self.init()
        self.render()
        self.paintGL = self.render

    def init(self):
        pass

    def render(self):
        pass


def data_from_path(path):
    data = None
    with open(path, 'rb') as f:
        data = f.read()
    return data

def text_from_path(path):
    text = None
    with open(path) as f:
        text = f.read()
    return text

def shader_from_path(path):
    return text_from_path('shader/' + path)

def res_from_path(path):
    return data_from_path('res/' + path)

def mesh_from_path(path):
    try:
        mesh = parse_mesh(path)
    except Exception as _:
        mesh = _parse_mesh(path)
    pos = np.array(mesh['position'])
    pos[:,0] = -pos[:,0]
    norm = np.array(mesh['normal'])
    norm[:,0] = -norm[:,0]
    dat = np.hstack((pos, norm))
    mesh['gldat'] = dat
    index = np.array(mesh['face'])
    index = index[:,[1,0,2]]
    mesh['glindex'] = index
    return mesh

def log(*args, **kwargs):
    print('log: ', *args, **kwargs)

def grid(size, steps):
    u = np.repeat(np.linspace(-size, size, steps), 2)
    v = np.tile([-size, size], steps)
    w = np.zeros(steps * 2)
    return np.concatenate([np.dstack([u, w, v]), np.dstack([v, w, u])])

def file_names_from_dir(path):
    file_names = os.listdir(path)
    file_names = list(filter(lambda s: s.endswith('.mesh'), file_names))
    return file_names

def file_paths_from_dir(path):
    file_names = file_names_from_dir(path)
    file_paths = list(map(lambda s: path + '/' + s, file_names))
    return file_paths

help_text = '''
Key Up: change to prev mesh
Key Down: change to next mesh

Mouse Middle: Orbit
Mouse Middle Scroll: Dolly
Dhift + Mouse Middle: Pan
'''