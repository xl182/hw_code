import sys
import pickle
from collections import defaultdict
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QComboBox, QCheckBox, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
                             QGroupBox, QScrollArea, QLabel, QHBoxLayout as QHBox)
from PyQt5.QtGui import QColor, QBrush, QPainter
from PyQt5.QtCore import Qt, QSize, QRectF

class DiskVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = self.load_data()
        self.current_disk = 0  # 当前磁盘索引
        self.cell_size = 10    # 单元格大小
        self.colors = self.create_colormap()
        self.checkboxes = [0 for i in range(100)]
        self.init_ui()

    def load_data(self):
        """加载pickle数据并提取后10个磁盘"""
        with open('disk.pkl', 'rb') as f:
            data = pickle.load(f)
        return data[-10:]  # 正确截取最后10个磁盘

    def create_colormap(self):
        """创建17种颜色的映射表（包含-1）"""
        colors = {-1: QColor(0, 0, 0)}  # -1对应黑色
        hues = [i*360//16 for i in range(16)]  # 16种色调均匀分布
        for idx, hue in enumerate(hues):
            colors[idx] = QColor.fromHsv(hue, 255, 255)
        return colors

    def init_ui(self):
        """初始化界面组件"""
        main_widget = QWidget()
        main_layout = QHBoxLayout()

        # 控制面板
        control_panel = QVBoxLayout()
        self.disk_selector = QComboBox()
        self.disk_selector.addItems([f"Disk {i+1}" for i in range(10)])
        self.disk_selector.currentIndexChanged.connect(self.update_disk)

        # 颜色筛选复选框（带颜色标记）
        color_group = QGroupBox("显示类别")
        color_layout = QVBoxLayout()
        for value in sorted(self.colors.keys()):
            hbox = QHBox()
            # 颜色标签
            color_label = QLabel()
            color_label.setFixedSize(20, 20)
            color_label.setStyleSheet(f"background-color: {self.colors[value].name()}")
            # 复选框
            cb = QCheckBox(f"值 {value}", self)
            cb.setChecked(True)
            cb.stateChanged.connect(self.update_display)
            hbox.addWidget(color_label)
            hbox.addWidget(cb)
            hbox.addStretch()
            color_layout.addLayout(hbox)
            self.checkboxes[value] = cb
        color_group.setLayout(color_layout)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidget(color_group)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(220)

        control_panel.addWidget(self.disk_selector)
        control_panel.addWidget(scroll)

        # 图形显示区域
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing, False)  # 禁用抗锯齿
        self.view.setRenderHint(QPainter.SmoothPixmapTransform, False)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)     # 拖动手势
        self.view.setOptimizationFlags(QGraphicsView.DontSavePainterState | 
                                      QGraphicsView.DontAdjustForAntialiasing)

        main_layout.addLayout(control_panel, 1)
        main_layout.addWidget(self.view, 4)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.setWindowTitle('磁盘存储可视化')
        self.setMinimumSize(QSize(800, 600))
        self.update_disk(0)

    def update_disk(self, index):
        """更新当前显示的磁盘数据"""
        self.current_disk = index
        disk_data = self.data[index]
        self.value_items = defaultdict(list)
        self.scene.clear()

        cols = 100  # 每行显示100个单元
        rows = (len(disk_data) + cols - 1) // cols

        # 预计算场景边界
        total_width = cols * self.cell_size
        total_height = rows * self.cell_size
        self.scene.setSceneRect(0, 0, total_width, total_height)

        # 批量创建矩形项
        for i, value in enumerate(disk_data):
            row = i // cols
            col = i % cols
            rect = QGraphicsRectItem(
                col * self.cell_size,
                row * self.cell_size,
                self.cell_size - 1,
                self.cell_size - 1
            )
            color = self.colors.get(value, Qt.black)
            rect.setBrush(QBrush(color))
            rect.setVisible(self.checkboxes[value].isChecked())
            self.scene.addItem(rect)
            self.value_items[value].append(rect)

        # 自动调整视图比例
        self.view.fitInView(QRectF(0, 0, total_width, total_height), Qt.KeepAspectRatio)

    def update_display(self):
        """更新显示过滤条件"""
        for value, items in self.value_items.items():
            visible = self.checkboxes[value].isChecked()
            for item in items:
                item.setVisible(visible)

    def resizeEvent(self, event):
        """窗口大小变化时保持视图比例"""
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        super().resizeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DiskVisualizer()
    ex.show()
    sys.exit(app.exec_())
    