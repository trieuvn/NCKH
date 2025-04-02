import sys
import os
import json
import cv2
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton,
                             QFileDialog, QVBoxLayout, QHBoxLayout, QMessageBox,
                             QSlider, QFrame, QScrollArea)
from PyQt6.QtGui import QPixmap, QPainter, QPen, QImage
from PyQt6.QtCore import Qt, QPoint, QTimer, QSize

file_lock = threading.Lock()
FILE_PATH = "PosList.json"

class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.points = []  # Lưu trữ các điểm được chọn
        self.quadrilaterals = []  # Lưu trữ các hình tứ giác đã vẽ
        self.delete_mode = False  # Trạng thái xóa
        self.current_media_path = ""  # Đường dẫn tới media hiện tại
        self.is_video = False  # Flag để xác định có phải đang xử lý video không
        self.video_capture = None  # Đối tượng VideoCapture
        self.current_frame = None  # Khung hình video hiện tại
        self.frame_count = 0  # Tổng số khung hình
        self.current_frame_pos = 0  # Vị trí khung hình hiện tại
        self.original_size = QSize(0, 0)  # Kích thước gốc của hình ảnh/video
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.delete_mode:
                pos = event.position().toPoint()
                quad_to_remove = None
                for quad in self.quadrilaterals:
                    if self.isPointInsideQuad(pos, quad):
                        quad_to_remove = quad
                        break
                if quad_to_remove:
                    self.quadrilaterals.remove(quad_to_remove)
            elif len(self.points) < 4:
                self.points.append(event.position().toPoint())
                if len(self.points) == 4:
                    self.quadrilaterals.append(self.points.copy())
                    quad_info = "\n".join([f"Đỉnh {i + 1}: ({p.x()}, {p.y()})" for i, p in enumerate(self.points)])
                    QMessageBox.information(self, "Hình tứ giác mới",
                                            f"Đã tạo hình tứ giác với các đỉnh:\n{quad_info}")
                    self.points.clear()
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen(Qt.GlobalColor.red, 2)
        painter.setPen(pen)

        for point in self.points:
            painter.drawEllipse(point, 5, 5)

        for quad in self.quadrilaterals:
            if len(quad) == 4:
                painter.drawLine(quad[0], quad[1])
                painter.drawLine(quad[1], quad[2])
                painter.drawLine(quad[2], quad[3])
                painter.drawLine(quad[3], quad[0])

    def isPointInsideQuad(self, point, quad):
        if len(quad) != 4:
            return False
        intersections = 0
        for i in range(4):
            p1 = quad[i]
            p2 = quad[(i + 1) % 4]
            if self.rayIntersectsSegment(point, p1, p2):
                intersections += 1
        return intersections % 2 == 1

    def rayIntersectsSegment(self, point, p1, p2):
        if p1.y() > p2.y():
            p1, p2 = p2, p1
        if point.y() == p1.y() or point.y() == p2.y():
            point = QPoint(point.x(), point.y() + 1)
        if (point.y() < p1.y() or point.y() > p2.y() or
                point.x() > max(p1.x(), p2.x())):
            return False
        if point.x() < min(p1.x(), p2.x()):
            return True
        slope = (p2.x() - p1.x()) / (p2.y() - p1.y()) if p2.y() != p1.y() else 0
        intersect_x = p1.x() + (point.y() - p1.y()) * slope
        return point.x() < intersect_x

    def clearPoints(self):
        self.points.clear()
        self.update()

    def setDeleteMode(self, enabled):
        self.delete_mode = enabled
        self.clearPoints()

    def clearQuadrilaterals(self):
        self.quadrilaterals.clear()
        self.update()

    def setCurrentMediaPath(self, path, is_video=False):
        self.current_media_path = path
        self.is_video = is_video
        if is_video:
            self.openVideoCapture(path)

    def openVideoCapture(self, video_path):
        if self.video_capture is not None:
            self.video_capture.release()
        self.video_capture = cv2.VideoCapture(video_path)
        self.frame_count = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame_pos = 0
        self.readFrame(0)

    def readFrame(self, frame_position):
        if self.video_capture is None or not self.is_video:
            return False
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
        self.current_frame_pos = frame_position
        ret, frame = self.video_capture.read()
        if ret:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.current_frame = rgb_frame
            height, width, channels = rgb_frame.shape
            bytesPerLine = channels * width
            qImg = QImage(rgb_frame.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qImg)
            self.original_size = QSize(width, height)
            self.setPixmap(pixmap)
            self.setFixedSize(self.original_size)  # Đặt kích thước cố định theo kích thước gốc
            self.update()
            return True
        return False

    def closeVideo(self):
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
            self.is_video = False
            self.current_frame = None

    def getCurrentMediaPath(self):
        return self.current_media_path

    def isVideo(self):
        return self.is_video


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Quadrilateral Editor")
        self.setGeometry(100, 100, 800, 600)
        self.poslist_file = "PosList.json"

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.toolbar = QHBoxLayout()
        self.select_image_button = QPushButton("Chọn ảnh")
        self.select_image_button.clicked.connect(self.selectImage)
        self.select_video_button = QPushButton("Chọn video")
        self.select_video_button.clicked.connect(self.selectVideo)
        self.delete_button = QPushButton("Xóa hình tứ giác")
        self.delete_button.setCheckable(True)
        self.delete_button.toggled.connect(self.toggleDeleteMode)
        self.save_button = QPushButton("Lưu vị trí")
        self.save_button.clicked.connect(self.savePositions)

        self.toolbar.addWidget(self.select_image_button)
        self.toolbar.addWidget(self.select_video_button)
        self.toolbar.addWidget(self.delete_button)
        self.toolbar.addWidget(self.save_button)
        self.toolbar.addStretch()
        self.layout.addLayout(self.toolbar)

        self.video_controls = QHBoxLayout()
        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(100)
        self.frame_slider.valueChanged.connect(self.updateFramePosition)
        self.frame_info_label = QLabel("Khung hình: 0 / 0")
        self.video_controls.addWidget(self.frame_slider)
        self.video_controls.addWidget(self.frame_info_label)

        self.video_controls_widget = QWidget()
        self.video_controls_widget.setLayout(self.video_controls)
        self.video_controls_widget.setVisible(False)
        self.layout.addWidget(self.video_controls_widget)

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(self.separator)

        # Thêm QScrollArea để chứa ImageLabel
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.image_label = ImageLabel()
        self.scroll_area.setWidget(self.image_label)
        self.layout.addWidget(self.scroll_area)

        self.initializePosList()

    def initializePosList(self):
        if not os.path.exists(self.poslist_file):
            with open(self.poslist_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
            print(f"Đã tạo file {self.poslist_file}")

    def selectImage(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_name:
            self.video_controls_widget.setVisible(False)
            self.image_label.closeVideo()

            pixmap = QPixmap(file_name)
            if not pixmap.isNull():
                self.image_label.setCurrentMediaPath(file_name, is_video=False)
                self.image_label.setPixmap(pixmap)
                self.image_label.original_size = pixmap.size()  # Lưu kích thước gốc
                self.image_label.setFixedSize(pixmap.size())  # Đặt kích thước cố định
                self.image_label.clearPoints()
                self.image_label.clearQuadrilaterals()
                self.delete_button.setChecked(False)
                self.loadPositions(file_name)

    def selectVideo(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Chọn video", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if file_name:
            self.image_label.setCurrentMediaPath(file_name, is_video=True)
            if self.image_label.video_capture is not None:
                self.video_controls_widget.setVisible(True)
                self.frame_slider.setMaximum(self.image_label.frame_count - 1)
                self.frame_slider.setValue(0)
                self.updateFrameInfoLabel()
                self.image_label.clearPoints()
                self.image_label.clearQuadrilaterals()
                self.delete_button.setChecked(False)
                self.image_label.readFrame(0)
                frame_key = f"{file_name}:0"
                self.loadPositions(frame_key)

    def updateFramePosition(self, position):
        if self.image_label.video_capture is not None:
            self.image_label.readFrame(position)
            self.updateFrameInfoLabel()
            frame_key = f"{self.image_label.getCurrentMediaPath()}:{position}"
            self.loadPositions(frame_key)

    def updateFrameInfoLabel(self):
        if self.image_label.video_capture is not None:
            frame_pos = self.image_label.current_frame_pos
            frame_count = self.image_label.frame_count
            self.frame_info_label.setText(f"Khung hình: {frame_pos} / {frame_count}")

    def toggleDeleteMode(self, checked):
        self.image_label.setDeleteMode(checked)
        if checked:
            self.delete_button.setStyleSheet("background-color: #ffcccc")
        else:
            self.delete_button.setStyleSheet("")

    def savePositions(self):
        current_media = self.image_label.getCurrentMediaPath()
        if not current_media:
            QMessageBox.warning(self, "Cảnh báo", "Chưa có ảnh hoặc video nào được chọn!")
            return
        if not self.image_label.quadrilaterals:
            QMessageBox.information(self, "Thông báo", "Không có hình tứ giác nào để lưu!")
            return
        media_key = f"{current_media}:{self.image_label.current_frame_pos}" if self.image_label.isVideo() else current_media
        try:
            with open(self.poslist_file, 'r', encoding='utf-8') as f:
                poslist_data = json.load(f)
            quads_data = [[{"x": point.x(), "y": point.y()} for point in quad] for quad in self.image_label.quadrilaterals]
            poslist_data[media_key] = quads_data
            with open(self.poslist_file, 'w', encoding='utf-8') as f:
                json.dump(poslist_data, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "Thành công",
                                    f"Đã lưu {len(quads_data)} hình tứ giác cho {('khung hình video này' if self.image_label.isVideo() else 'ảnh này')}!")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu vị trí: {str(e)}")

    def loadPositions(self, media_key):
        try:
            with open(self.poslist_file, 'r', encoding='utf-8') as f:
                poslist_data = json.load(f)
            if media_key in poslist_data:
                self.image_label.clearQuadrilaterals()
                quads_data = poslist_data[media_key]
                for quad_points in quads_data:
                    quad = [QPoint(point["x"], point["y"]) for point in quad_points]
                    self.image_label.quadrilaterals.append(quad)
                self.image_label.update()
                QMessageBox.information(self, "Thông báo",
                                        f"Đã tải {len(quads_data)} hình tứ giác từ dữ liệu đã lưu!")
        except Exception as e:
            pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())