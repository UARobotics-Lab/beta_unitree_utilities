import csv
from datetime import datetime
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QCheckBox, QHBoxLayout, QLabel, QScrollArea

class CSVOfflineVisualizer(QMainWindow):
    def __init__(self, csv_file):
        super().__init__()
        self.setWindowTitle("Visualización Offline: q y τ por articulación")

        self.csv_file = csv_file
        self.joint_data = defaultdict(lambda: {'q': [], 'tau': [], 'time': []})
        self.joint_names = []

        self.load_csv()

        # GUI
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.canvas = FigureCanvas(plt.Figure(figsize=(10, 8)))
        self.ax_q = self.canvas.figure.add_subplot(211)
        self.ax_tau = self.canvas.figure.add_subplot(212, sharex=self.ax_q)

        layout = QHBoxLayout(self.main_widget)
        self.checkboxes_layout = QVBoxLayout()
        self.checkboxes = []

        # Scroll para muchos joints
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.checkboxes_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)

        for i, joint in enumerate(self.joint_names):
            cb = QCheckBox(f"Joint {i} ({joint})")
            cb.setChecked(True)
            cb.stateChanged.connect(self.update_plot)
            self.checkboxes.append(cb)
            self.checkboxes_layout.addWidget(cb)

        layout.addWidget(scroll_area)
        layout.addWidget(self.canvas)

        self.update_plot()

    def load_csv(self):
        with open(self.csv_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            labels = header[1:]

            self.joint_names = [f"J{i}" for i in range(len(labels)//2)]

            for row in reader:
                if len(row) < 2:
                    continue
                timestamp = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S.%f")
                values = list(map(float, row[1:]))

                for i, joint in enumerate(self.joint_names):
                    q = values[2*i]
                    tau = values[2*i + 1]
                    self.joint_data[joint]['q'].append(q)
                    self.joint_data[joint]['tau'].append(tau)
                    self.joint_data[joint]['time'].append(timestamp)

    def update_plot(self):
        self.ax_q.clear()
        self.ax_tau.clear()

        for i, cb in enumerate(self.checkboxes):
            if cb.isChecked():
                joint = self.joint_names[i]
                t = [(ts - self.joint_data[joint]['time'][0]).total_seconds() for ts in self.joint_data[joint]['time']]
                q = self.joint_data[joint]['q']
                tau = self.joint_data[joint]['tau']

                self.ax_q.plot(t, q, label=f"q{i}")
                self.ax_tau.plot(t, tau, label=f"τ{i}", linestyle='--')

        self.ax_q.set_title("Posición (q)")
        self.ax_q.set_ylabel("q [rad]")
        self.ax_q.legend()
        self.ax_q.grid(True)

        self.ax_tau.set_title("Torque estimado (τ)")
        self.ax_tau.set_xlabel("Tiempo [s]")
        self.ax_tau.set_ylabel("τ [Nm]")
        self.ax_tau.legend()
        self.ax_tau.grid(True)

        self.canvas.draw()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    viewer = CSVOfflineVisualizer("datos_robot.csv")
    viewer.resize(1200, 800)
    viewer.show()
    sys.exit(app.exec_())
