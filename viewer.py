import sys
import moderngl as mgl
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from util import *
from camera import Camera
from scene import Scene


class ViewerWidget(QModernGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = None
        self.last_x = None
        self.last_y = None

        self.mouse_middle_pressed = False
        self.shift_pressed = False
        self.ctrl_pressed = False

    def init(self):
        self.ctx.viewport = self.viewport
        self.scene = Scene(self.ctx)
        self.ctx_init()

    def render(self):
        self.screen.use()
        self.scene.clear()
        self.scene.draw()
    
    def ctx_init(self):
        self.ctx.enable(mgl.DEPTH_TEST)
        self.ctx.enable(mgl.CULL_FACE)

    def mousePressEvent(self, event):
        self.last_x = event.x()
        self.last_y = event.y()
        if event.button() == 4:
            self.mouse_middle_pressed = True
        self.update()

    def mouseReleaseEvent(self, event):
        self.last_x = None
        self.last_y = None
        if event.button() == 4:
            self.mouse_middle_pressed = False
        self.update()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.last_x
        dy = event.y() - self.last_y
        self.last_x = event.x()
        self.last_y = event.y()
        if self.mouse_middle_pressed == True:
            if self.shift_pressed == False:
                self.scene.camera.orbit(dx, dy)
            else:
                self.scene.camera.pan(dx, dy)
        self.update()
    
    def wheelEvent(self, event):
        offset = event.angleDelta().y() / 120
        self.scene.camera.dolly(offset)
        self.update()
    
    def resizeEvent(self, event):
        width = event.size().width()
        height = event.size().height()
        if width > height:
            self.viewport = (int((width - height) / 2), 0, height, height)
        else:
            self.viewport = (0, int((height - width) / 2), width, width)
        if hasattr(self, 'ctx') and hasattr(self.ctx, 'viewport'):
            self.ctx.viewport = self.viewport

    def keyPressEvent(self, event):
        if event.key() == 16777248:
            self.shift_pressed = True
        elif event.key() == 16777249:
            self.ctrl_pressed = True
        elif event.key() == ord('1'):
            self.scene.camera.orthogonal(1, self.ctrl_pressed)
        elif event.key() == ord('3'):
            self.scene.camera.orthogonal(3, self.ctrl_pressed)
        elif event.key() == ord('7'):
            self.scene.camera.orthogonal(7, self.ctrl_pressed)
        self.update()

    def keyReleaseEvent(self, event):
        if event.key() == 16777248:
            self.shift_pressed = False
        elif event.key() == 16777249:
            self.ctrl_pressed = False
    
    def load_mesh(self, mesh):
        self.scene.load_mesh(mesh)
        self.update()

    def release_mesh(self):
        self.scene.release_mesh()
        self.update()


def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = ViewerWidget()
    widget.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
