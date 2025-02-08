import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QFileDialog, QVBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PIL import Image

def pil_to_qpixmap(pil_image):
    image = pil_image.convert("RGBA")
    data = image.tobytes("raw", "RGBA")
    qimage = QImage(data, image.width, image.height, QImage.Format_RGBA8888)
    return QPixmap.fromImage(qimage)

class ImageSplitterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("RGBA Image Splitter")
        self.setGeometry(100, 100, 800, 600)
        self.setAcceptDrops(True)

        self.label_original = QLabel("Drop Image Here", self)
        self.label_rgb = QLabel("RGB Image")
        self.label_alpha = QLabel("Alpha Channel")

        self.label_original.setAlignment(Qt.AlignCenter)
        self.label_rgb.setAlignment(Qt.AlignCenter)
        self.label_alpha.setAlignment(Qt.AlignCenter)

        self.label_original.setFixedSize(250, 250)
        self.label_rgb.setFixedSize(250, 250)
        self.label_alpha.setFixedSize(250, 250)

        layout_main = QVBoxLayout()
        layout_main.addWidget(self.label_original)
        layout_main.addWidget(self.label_rgb)
        layout_main.addWidget(self.label_alpha)
        self.setLayout(layout_main)

        self.image = None
        self.rgb_image = None
        self.alpha_image = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.load_image(file_path)

    def load_image(self, file_path):
        self.image = Image.open(file_path).convert("RGBA")
        self.update_images()
        self.save_images(file_path)

    def update_images(self):
        if self.image:
            self.rgb_image = self.image.convert("RGB")
            self.alpha_image = self.image.getchannel("A")
            
            self.label_original.setPixmap(pil_to_qpixmap(self.image).scaled(250, 250))
            self.label_rgb.setPixmap(pil_to_qpixmap(self.rgb_image).scaled(250, 250))
            self.label_alpha.setPixmap(pil_to_qpixmap(self.alpha_image.convert("L")).scaled(250, 250))

    def save_images(self, file_path):
        base_name = file_path.rsplit(".", 1)[0]
        rgb_path = f"{base_name}_rgb.png"
        alpha_path = f"{base_name}_alpha.png"
        
        if self.rgb_image:
            self.rgb_image.save(rgb_path)
        if self.alpha_image:
            self.alpha_image.save(alpha_path)
        print(f"RGB Image saved: {rgb_path}")
        print(f"Alpha Image saved: {alpha_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ImageSplitterApp()
    ex.show()
    sys.exit(app.exec_())

'''
image_path = "1089_buzhihuo/00000095_Out.png"
image = Image.open(image_path).convert("RGBA")

rgb_image = Image.new("RGB", image.size)
rgb_image.paste(image, mask=None)

alpha_image = image.getchannel("A")

rgb_image.save("output_rgb.png")

alpha_image.save("output_alpha.png")

'''