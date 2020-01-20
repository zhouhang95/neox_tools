import sys
import os
from threading import Thread
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from viewer import ViewerWidget
from util import *
from extractor import unpack
from converter import saveobj, saveiqe, savepmx


class CentralWidget(QSplitter):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.listWidget = QListWidget(self)
        self.viewer = ViewerWidget(self)
        self.paths = []
        self.names = []
        self.name = ''
        self.mesh = None
        self.grabKeyboard()

        self.listWidget.itemSelectionChanged.connect(self.cb_itemSelectionChanged)

        self.initLayout()

    def cb_itemSelectionChanged(self):
        current_row = self.listWidget.currentRow()
        if len(self.paths) > current_row:
            path = self.paths[current_row]
            self.name = self.names[current_row]
            self.mesh = nxm_from_path(path)
            self.viewer.load_mesh(self.mesh)

    def init_load_mesh(self):
        if (len(self.paths) > 0):
            path = self.paths[0]
            self.name = self.names[0]
            self.mesh = nxm_from_path(path)
            self.viewer.load_mesh(self.mesh)

    def keyPressEvent(self, event):
        if event.key() in [16777235, 16777237]:
            self.listWidget.keyPressEvent(event)
        else:
            self.viewer.keyPressEvent(event)

    
    def keyReleaseEvent(self, event):
        self.viewer.keyPressEvent(event)
    
    def load_folder(self, folder_path):
        self.viewer.release_mesh()
        self.paths = file_paths_from_dir(folder_path)
        self.names = list(map(lambda s: s.split('/')[-1], self.paths))

        self.listWidget.clear()
        self.listWidget.addItems(self.names)

    def initLayout(self):
        self.addWidget(self.listWidget)
        self.addWidget(self.viewer)
        self.setStretchFactor(0, 1)
        self.setStretchFactor(1, 4)
        self.setMinimumHeight(450)


class MyApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.version = '0.0.1'
        self.title = 'NeoX Mesh Viewer'
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 300, 200)
        self.setMinimumWidth(620)
        
        self.menubar = self.menuBar()
        self.file = self.menubar.addMenu('File')
        self.file.addAction('Load Unpack Folder', self.cb_load_folder)
        self.file.addAction('Unpack', self.cb_unpack)
        self.file.addAction('Save Obj', self.cb_save_obj)
        self.file.addAction('Save Iqe', self.cb_save_iqe)
        self.file.addAction('Save Pmx', self.cb_save_pmx)

        self.about = self.menubar.addMenu('About')
        self.about.addAction('Home Page', self.cb_openHomePage)
        self.about.addAction('Help', self.cb_help)

        self.centralWidget = CentralWidget(self)
        self.setCentralWidget(self.centralWidget)

        self.statusBar = QStatusBar()
        self.statusBar.showMessage('Author: zhouhang95')
        self.setStatusBar(self.statusBar)

        self.show()

    def cb_unpack(self):
        path = QFileDialog.getOpenFileName()
        path = path[0]
        if path == '':
            return
        self.thread = Thread(target=unpack, args=(path, self.statusBar))
        self.thread.start()
    
    def cb_openHomePage(self):
        QDesktopServices.openUrl(QUrl('https://github.com/zhouhang95/neox_tools'))

    def cb_load_folder(self):
        path = QFileDialog.getExistingDirectory()
        if path == '':
            return
        self.centralWidget.load_folder(path)
        self.centralWidget.init_load_mesh()

    def cb_save_obj(self):
        if self.centralWidget.name == '':
            return
        saveobj(self.centralWidget.mesh, self.centralWidget.name)
        self.statusBar.showMessage('OBJ saved!')

    def cb_save_iqe(self):
        if self.centralWidget.name == '':
            return
        saveiqe(self.centralWidget.mesh, self.centralWidget.name)
        self.statusBar.showMessage('IQE saved!')

    def cb_save_pmx(self):
        if self.centralWidget.name == '':
            return
        savepmx(self.centralWidget.mesh, self.centralWidget.name)
        self.statusBar.showMessage('PMX saved!')

    def cb_help(self):
        QMessageBox.about(self, 'Help', help_text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_app = MyApp()
    sys.exit(app.exec_())