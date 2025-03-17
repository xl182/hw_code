import sys
import pickle
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

class DiskVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()
        self.colors = {i: QColor(*self.generate_color(i)) for i in range(17)}
        self.colors[-1] = QColor(0, 0, 0)  # -1 is black
        self.display_disks()

    def initUI(self):
        self.setWindowTitle('Disk Visualizer')
        self.layout = QVBoxLayout()
        self.grid_layout = QGridLayout()
        self.layout.addLayout(self.grid_layout)
        self.setLayout(self.layout)

        self.control_layout = QHBoxLayout()
        self.layout.addLayout(self.control_layout)

        self.buttons = {}
        for i in range(17):
            button = QPushButton(f'Class {i}')
            button.setCheckable(True)
            button.setChecked(True)
            button.clicked.connect(self.update_display)
            self.control_layout.addWidget(button)
            self.buttons[i] = button

        self.black_button = QPushButton('Class -1')
        self.black_button.setCheckable(True)
        self.black_button.setChecked(True)
        self.black_button.clicked.connect(self.update_display)
        self.control_layout.addWidget(self.black_button)

    def load_data(self):
        with open('disk.pkl', 'rb') as f:
            self.data = pickle.load(f)

    def generate_color(self, index):
        # Simple color generation based on index
        return (index * 15 % 256, index * 30 % 256, index * 45 % 256)

    def display_disks(self):
        for i in range(10):
            for j in range(579):
                label = QLabel()
                label.setFixedSize(5, 5)
                label.setAlignment(Qt.AlignCenter)
                self.grid_layout.addWidget(label, i, j)
                self.update_label(label, i, j)

    def update_label(self, label, row, col):
        value = self.data[row][col]
        if value in self.colors:
            label.setStyleSheet(f'background-color: {self.colors[value].name()};')

    def update_display(self):
        for i in range(10):
            for j in range(579):
                label = self.grid_layout.itemAtPosition(i, j).widget()
                value = self.data[i][j]
                if (value in self.buttons and self.buttons[value].isChecked()) or \
                   (value == -1 and self.black_button.isChecked()):
                    self.update_label(label, i, j)
                else:
                    label.setStyleSheet('background-color: transparent;')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DiskVisualizer()
    ex.show()
    sys.exit(app.exec_())
