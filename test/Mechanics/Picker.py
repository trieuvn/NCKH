import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton,
                            QFileDialog, QVBoxLayout, QHBoxLayout)
from PyQt6.QtGui import QPixmap, QPainter, QPen, QImage
from PyQt6.QtCore import Qt, QPoint

class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.points = []  # Lưu trữ các điểm được chọn
        self.quadrilaterals = []  # Lưu trữ các hình tứ giác đã vẽ
        self.delete_mode = False  # Trạng thái xóa
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 400)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.delete_mode:
                # Xóa hình tứ giác nếu click vào bên trong
                pos = event.position().toPoint()
                quad_to_remove = None
                for quad in self.quadrilaterals:
                    if self.isPointInsideQuad(pos, quad):
                        quad_to_remove = quad
                        break
                if quad_to_remove:
                    self.quadrilaterals.remove(quad_to_remove)
            elif len(self.points) < 4:
                # Thêm điểm để vẽ hình tứ giác
                self.points.append(event.position().toPoint())
                if len(self.points) == 4:
                    self.quadrilaterals.append(self.points.copy())
                    self.points.clear()
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen(Qt.GlobalColor.red, 2)
        painter.setPen(pen)

        # Vẽ các điểm đã chọn
        for point in self.points:
            painter.drawEllipse(point, 5, 5)

        # Vẽ các hình tứ giác đã hoàn thành
        for quad in self.quadrilaterals:
            if len(quad) == 4:
                painter.drawLine(quad[0], quad[1])
                painter.drawLine(quad[1], quad[2])
                painter.drawLine(quad[2], quad[3])
                painter.drawLine(quad[3], quad[0])

    def isPointInsideQuad(self, point, quad):
        """
        Kiểm tra xem điểm có nằm bên trong hình tứ giác hay không
        Sử dụng phương pháp ray-casting
        """
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
        """
        Kiểm tra xem tia từ điểm point có giao với đoạn thẳng p1-p2 không
        """
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
        self.clearPoints()  # Xóa các điểm đang chọn khi chuyển chế độ

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Quadrilateral Editor")
        self.setGeometry(100, 100, 800, 600)

        # Widget chính
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Thanh công cụ
        self.toolbar = QHBoxLayout()
        self.select_button = QPushButton("Chọn ảnh")
        self.select_button.clicked.connect(self.selectImage)
        self.delete_button = QPushButton("Xóa hình tứ giác")
        self.delete_button.setCheckable(True)  # Cho phép toggle trạng thái
        self.delete_button.toggled.connect(self.toggleDeleteMode)
        self.toolbar.addWidget(self.select_button)
        self.toolbar.addWidget(self.delete_button)
        self.toolbar.addStretch()
        self.layout.addLayout(self.toolbar)

        # Label hiển thị hình ảnh
        self.image_label = ImageLabel()
        self.layout.addWidget(self.image_label)

    def selectImage(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_name:
            pixmap = QPixmap(file_name)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.clearPoints()  # Xóa các điểm khi chọn ảnh mới
                self.delete_button.setChecked(False)  # Tắt chế độ xóa

    def toggleDeleteMode(self, checked):
        self.image_label.setDeleteMode(checked)
        if checked:
            self.delete_button.setStyleSheet("background-color: #ffcccc")
        else:
            self.delete_button.setStyleSheet("")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())