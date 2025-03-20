import sys
import pickle
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QCheckBox, QScrollArea, QGroupBox,
                            QFileDialog, QStatusBar)
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QColor, QPainter, QPixmap, QCursor

class DiskDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.rows = 0
        self.cols = 0
        self.cell_size = 20
        self.visible_values = set()  # 可见的值集合
        self.colors = {}  # 值到颜色的映射
        self.current_disk = 0  # 当前显示的磁盘索引
        self.hover_pos = (-1, -1)  # 鼠标悬停位置
        
        # 初始化颜色映射（示例颜色，可根据需要调整）
        self.init_colormap()

    def init_colormap(self):
        """初始化17种颜色映射（包含-1）"""
        colors = [
            QColor(255,0,0), QColor(0,255,0), QColor(0,0,255),
            QColor(255,255,0), QColor(255,0,255), QColor(0,255,255),
            QColor(128,0,0), QColor(0,128,0), QColor(0,0,128),
            QColor(128,128,0), QColor(128,0,128), QColor(0,128,128),
            QColor(192,192,192), QColor(128,128,128), QColor(153,51,102),
            QColor(255,128,0), QColor(102,0,204)
        ]
        values = [-1] + list(range(16))  # 值-1对应黑色
        for val, color in zip(values, colors):
            self.colors[val] = color
        self.colors[-1] = QColor(0, 0, 0)  # 确保-1为黑色

    def set_data(self, data):
        """设置数据并更新显示"""
        if data is None:
            return
        self.data = data
        self.rows = 11  # 根据数据实际情况调整
        self.cols = 5793 // self.rows
        self.update()

    def set_visible_values(self, values):
        """设置可见的值"""
        self.visible_values = set(values)
        self.update()

    def paintEvent(self, event):
        if self.data is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算绘制区域
        start_x = 0
        start_y = 0
        
        # 绘制每个单元
        for row in range(self.rows):
            for col in range(self.cols):
                idx = row * self.cols + col
                if idx >= len(self.data):
                    continue
                val = self.data[idx]
                if val not in self.visible_values:
                    continue
                color = self.colors.get(val, QColor(0,0,0))
                painter.fillRect(
                    start_x + col * self.cell_size,
                    start_y + row * self.cell_size,
                    self.cell_size - 1,
                    self.cell_size - 1,
                    color
                )
        
        # 绘制悬停框
        if self.hover_pos != (-1, -1):
            painter.setPen(Qt.red)
            painter.drawRect(
                self.hover_pos[0] * self.cell_size,
                self.hover_pos[1] * self.cell_size,
                self.cell_size,
                self.cell_size
            )

    def mouseMoveEvent(self, event):
        pos = event.pos()
        col = pos.x() // self.cell_size
        row = pos.y() // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.hover_pos = (col, row)
            idx = row * self.cols + col
            self.parent().statusBar().showMessage(f"单元ID: {idx} 值: {self.data[idx]}")
        else:
            self.hover_pos = (-1, -1)
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_list = []
        self.current_file_idx = -1
        self.current_data = None
        self.disk_data = []  # 存储所有磁盘数据
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('磁盘数据可视化')
        self.setGeometry(100, 100, 1200, 800)
        
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # 左侧控制面板
        control_panel = QVBoxLayout()
        
        # 文件切换按钮
        btn_prev = QPushButton("上一个文件")
        btn_prev.clicked.connect(self.prev_file)
        btn_next = QPushButton("下一个文件")
        btn_next.clicked.connect(self.next_file)
        control_panel.addWidget(btn_prev)
        control_panel.addWidget(btn_next)
        
        # 颜色图例
        legend_group = QGroupBox("显示控制")
        legend_layout = QVBoxLayout()
        self.value_checkboxes = {}
        
        # 动态生成复选框
        for value in sorted(DiskDisplayWidget().colors.keys()):
            cb = QCheckBox(f"值 {value}")
            cb.setChecked(True)
            cb.stateChanged.connect(self.update_display)
            self.value_checkboxes[value] = cb
            legend_layout.addWidget(cb)
        
        legend_group.setLayout(legend_layout)
        control_panel.addWidget(legend_group)
        
        main_layout.addLayout(control_panel, stretch=1)
        
        # 右侧显示区域
        display_area = QVBoxLayout()
        self.disk_display = DiskDisplayWidget()
        display_area.addWidget(self.disk_display)
        main_layout.addLayout(display_area, stretch=4)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
        # 初始化文件列表
        self.load_initial_files()
        
    def load_initial_files(self):
        """初始化时加载当前目录下的pkl文件"""
        self.file_list = sorted([f for f in os.listdir('.') if f.endswith('.pkl')])
        if self.file_list:
            self.current_file_idx = 0
            self.load_file()
    
    def load_file(self):
        """加载当前文件数据"""
        if self.current_file_idx < 0 or self.current_file_idx >= len(self.file_list):
            return
        
        filename = self.file_list[self.current_file_idx]
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
                if isinstance(data, list) and len(data) >= 10:
                    self.disk_data = data[-10:]  # 取最后10个磁盘
                    self.disk_display.set_data(self.disk_data[0])
                    self.statusBar().showMessage(f"已加载: {filename}")
        except Exception as e:
            self.statusBar().showMessage(f"错误: {str(e)}")
    
    def prev_file(self):
        if self.file_list:
            self.current_file_idx = (self.current_file_idx - 1) % len(self.file_list)
            self.load_file()
    
    def next_file(self):
        if self.file_list:
            self.current_file_idx = (self.current_file_idx + 1) % len(self.file_list)
            self.load_file()
    
    def update_display(self):
        """更新可见的值"""
        visible_values = [val for val, cb in self.value_checkboxes.items() if cb.isChecked()]
        self.disk_display.set_visible_values(visible_values)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
