import os
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtOpenGL import QGLWidget
from PIL import Image


class GLWidget(QGLWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.image_folder = "kw_pano_images"  # 이미지 파일들이 있는 폴더 경로
        self.image_files = self.get_image_files()
        self.current_image_index = 0
        print("Current image index:", self.current_image_index)
        self.load_current_image()
        self.yaw = 0
        self.pitch = 0
        self.prev_dx = 0
        self.prev_dy = 0
        self.fov = 90
        self.moving = False
        self.setFocusPolicy(QtCore.Qt.StrongFocus)  # OpenGL 위젯에 포커스 설정

    def get_image_files(self):
        image_files = []
        for file in os.listdir(self.image_folder):
            if file.endswith(".jpg") or file.endswith(".png"):
                image_files.append(os.path.join(self.image_folder, file))
        return image_files

    def load_current_image(self):
        try:
            self.image = Image.open(self.image_files[self.current_image_index])
            self.image_width, self.image_height = self.image.size
        except Exception as e:
            print("Error loading image:", e)

    def initializeGL(self):
        glEnable(GL_TEXTURE_2D)
        self.texture = glGenTextures(1)
        self.update_texture()  # 텍스처 초기화
        self.sphere = gluNewQuadric()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(90, self.width() / self.height(), 0.1, 1000)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def update_texture(self):
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.image_width, self.image_height, 0, GL_RGB, GL_UNSIGNED_BYTE,
                     self.image.tobytes())
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        glRotatef(self.pitch, 1, 0, 0)
        glRotatef(self.yaw, 0, 1, 0)
        glRotatef(90, 1, 0, 0)
        glRotatef(-90, 0, 0, 1)

        glBindTexture(GL_TEXTURE_2D, self.texture)  # 텍스처를 바인딩
        gluQuadricTexture(self.sphere, True)
        gluSphere(self.sphere, 1, 100, 100)

        glPopMatrix()

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, self.width() / self.height(), 0.1, 1000)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.mouse_x, self.mouse_y = event.pos().x(), event.pos().y()
            self.moving = True

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.moving = False

    def mouseMoveEvent(self, event):
        if self.moving:
            dx = event.pos().x() - self.mouse_x
            dy = event.pos().y() - self.mouse_y
            dx *= 0.1
            dy *= 0.1
            self.yaw -= dx
            self.pitch -= dy
            self.pitch = min(max(self.pitch, -90), 90)
            self.mouse_x, self.mouse_y = event.pos().x(), event.pos().y()
            self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.fov -= delta * 0.1
        self.fov = max(30, min(self.fov, 90))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, self.width() / self.height(), 0.1, 1000)
        self.update()

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Up:
            self.change_image(1)
        elif key == QtCore.Qt.Key_Down:
            self.change_image(-1)

    def change_image(self, step):
        new_index = self.current_image_index + step
        if 0 <= new_index < len(self.image_files):
            prev_image = Image.open(self.image_files[self.current_image_index])
            next_image = Image.open(self.image_files[new_index])

            # 이미지 랜더링 및 보간
            num_frames = 3  # 중간 프레임 개수 (조정 가능)
            for i in range(num_frames):
                progress = i / num_frames
                interpolated_image = Image.blend(prev_image, next_image, progress)

                # PIL 이미지로 변환 후 텍스처 업데이트
                self.image = interpolated_image
                self.update_texture()
                self.update()
                QtWidgets.QApplication.processEvents()

            self.current_image_index = new_index
            print("Current image index:", self.current_image_index)
            self.load_current_image()
            self.update_texture()
            self.update()
        else:
            print("Index out of range")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("360° 뷰어")
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.gl_widget = GLWidget(self)
        self.setCentralWidget(self.gl_widget)

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Left:
            self.gl_widget.yaw += 10
            self.gl_widget.update()
        elif key == QtCore.Qt.Key_Right:
            self.gl_widget.yaw -= 10
            self.gl_widget.update()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.setGeometry(0, 0, 1600, 900)
    window.show()
    app.exec_()
