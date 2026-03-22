import sys
import os
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import csv
import time
from datetime import datetime

# 导入原来的 runner.py 功能
from runner import Runner


class RealTimeDisplay(QWidget):
    """实时比赛信息显示面板"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 当前比赛状态
        status_group = QGroupBox("当前比赛状态")
        status_layout = QGridLayout()

        self.play_mode_label = QLabel("比赛模式: 等待开始")
        self.time_label = QLabel("比赛时间: 0.0")
        self.score_label = QLabel("比分: 0 - 0")

        status_layout.addWidget(self.play_mode_label, 0, 0)
        status_layout.addWidget(self.time_label, 0, 1)
        status_layout.addWidget(self.score_label, 1, 0, 1, 2)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # 比赛信息表格
        info_group = QGroupBox("比赛信息")
        info_layout = QVBoxLayout()

        self.info_table = QTableWidget()
        self.info_table.setColumnCount(5)
        self.info_table.setHorizontalHeaderLabels(["时间", "我方", "对方", "比分", "状态"])
        self.info_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        info_layout.addWidget(self.info_table)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        self.setLayout(layout)

    def update_display(self, play_mode, game_time, score_left, score_right):
        """更新显示"""
        self.play_mode_label.setText(f"比赛模式: {play_mode}")
        self.time_label.setText(f"比赛时间: {game_time}")
        self.score_label.setText(f"比分: {score_left} - {score_right}")

    def add_game_record(self, team1, team2, score1, score2, status="已完成"):
        """添加比赛记录"""
        row_position = self.info_table.rowCount()
        self.info_table.insertRow(row_position)

        current_time = datetime.now().strftime("%H:%M:%S")

        self.info_table.setItem(row_position, 0, QTableWidgetItem(current_time))
        self.info_table.setItem(row_position, 1, QTableWidgetItem(team1))
        self.info_table.setItem(row_position, 2, QTableWidgetItem(team2))
        self.info_table.setItem(row_position, 3, QTableWidgetItem(f"{score1}:{score2}"))
        self.info_table.setItem(row_position, 4, QTableWidgetItem(status))

        # 滚动到最后一行
        self.info_table.scrollToBottom()


class ConfigurationPanel(QWidget):
    """配置面板"""

    def __init__(self):
        super().__init__()
        self.config_file = "config.json"
        self.load_config()
        self.init_ui()

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            # 默认配置
            self.config = {
                "monitor": {"ip": "localhost", "port": 3200},
                "game": {
                    "max_retry_times": 2,
                    "every_play_times": 2,
                    "exchange": True,
                    "our_left": True,
                    "our_binary_dir": "binary/our",
                    "opp_binary_dir": "binary/opp"
                }
            }
            self.save_config()

    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def init_ui(self):
        layout = QVBoxLayout()

        # 监控服务器配置
        monitor_group = QGroupBox("监控服务器配置")
        monitor_layout = QGridLayout()

        monitor_layout.addWidget(QLabel("IP地址:"), 0, 0)
        self.monitor_ip = QLineEdit(self.config["monitor"]["ip"])
        monitor_layout.addWidget(self.monitor_ip, 0, 1)

        monitor_layout.addWidget(QLabel("端口:"), 1, 0)
        self.monitor_port = QSpinBox()
        self.monitor_port.setRange(1, 65535)
        self.monitor_port.setValue(self.config["monitor"]["port"])
        monitor_layout.addWidget(self.monitor_port, 1, 1)

        monitor_group.setLayout(monitor_layout)
        layout.addWidget(monitor_group)

        # 比赛参数配置
        game_group = QGroupBox("比赛参数配置")
        game_layout = QGridLayout()

        game_layout.addWidget(QLabel("最大重试次数:"), 0, 0)
        self.max_retry_times = QSpinBox()
        self.max_retry_times.setRange(1, 10)
        self.max_retry_times.setValue(self.config["game"]["max_retry_times"])
        game_layout.addWidget(self.max_retry_times, 0, 1)

        game_layout.addWidget(QLabel("每队比赛次数:"), 1, 0)
        self.every_play_times = QSpinBox()
        self.every_play_times.setRange(1, 10)
        self.every_play_times.setValue(self.config["game"]["every_play_times"])
        game_layout.addWidget(self.every_play_times, 1, 1)

        game_layout.addWidget(QLabel("是否换边:"), 2, 0)
        self.exchange_check = QCheckBox()
        self.exchange_check.setChecked(self.config["game"]["exchange"])
        game_layout.addWidget(self.exchange_check, 2, 1)

        game_layout.addWidget(QLabel("我方在左侧:"), 3, 0)
        self.our_left_check = QCheckBox()
        self.our_left_check.setChecked(self.config["game"]["our_left"])
        game_layout.addWidget(self.our_left_check, 3, 1)

        game_layout.addWidget(QLabel("我方球队目录:"), 4, 0)
        self.our_binary_dir = QLineEdit(self.config["game"]["our_binary_dir"])
        browse_our_btn = QPushButton("浏览")
        browse_our_btn.clicked.connect(lambda: self.browse_directory(self.our_binary_dir))
        game_layout.addWidget(self.our_binary_dir, 4, 1)
        game_layout.addWidget(browse_our_btn, 4, 2)

        game_layout.addWidget(QLabel("对方球队目录:"), 5, 0)
        self.opp_binary_dir = QLineEdit(self.config["game"]["opp_binary_dir"])
        browse_opp_btn = QPushButton("浏览")
        browse_opp_btn.clicked.connect(lambda: self.browse_directory(self.opp_binary_dir))
        game_layout.addWidget(self.opp_binary_dir, 5, 1)
        game_layout.addWidget(browse_opp_btn, 5, 2)

        game_group.setLayout(game_layout)
        layout.addWidget(game_group)

        # 保存配置按钮
        save_btn = QPushButton("保存配置")
        save_btn.clicked.connect(self.save_current_config)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        layout.addWidget(save_btn)

        layout.addStretch()
        self.setLayout(layout)

    def browse_directory(self, line_edit):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory:
            line_edit.setText(directory)

    def save_current_config(self):
        """保存当前配置"""
        self.config["monitor"]["ip"] = self.monitor_ip.text()
        self.config["monitor"]["port"] = self.monitor_port.value()

        self.config["game"]["max_retry_times"] = self.max_retry_times.value()
        self.config["game"]["every_play_times"] = self.every_play_times.value()
        self.config["game"]["exchange"] = self.exchange_check.isChecked()
        self.config["game"]["our_left"] = self.our_left_check.isChecked()
        self.config["game"]["our_binary_dir"] = self.our_binary_dir.text()
        self.config["game"]["opp_binary_dir"] = self.opp_binary_dir.text()

        self.save_config()
        QMessageBox.information(self, "成功", "配置已保存！")

    def get_config(self):
        """获取当前配置"""
        return {
            "max_retry_times": self.max_retry_times.value(),
            "every_play_times": self.every_play_times.value(),
            "exchange": self.exchange_check.isChecked(),
            "our_left": self.our_left_check.isChecked(),
            "our_binary_dir": self.our_binary_dir.text(),
            "opp_binary_dir": self.opp_binary_dir.text()
        }


class GameThread(QThread):
    """比赛线程"""
    update_signal = pyqtSignal(str, float, int, int)  # play_mode, time, score_left, score_right
    game_result_signal = pyqtSignal(str, str, int, int, str)  # team1, team2, score1, score2, status
    progress_signal = pyqtSignal(int, int, str)  # current, total, message
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.runner = Runner()
        self.is_running = True

        # 修改runner的配置文件
        self.update_runner_config()

    def update_runner_config(self):
        """更新runner的配置文件"""
        config_data = {
            "monitor": {
                "ip": "localhost",
                "port": 3200
            }
        }
        with open("config.json", "w") as f:
            json.dump(config_data, f)

    def get_team_lists(self):
        """获取球队列表"""
        our_dir = self.config['our_binary_dir']
        opp_dir = self.config['opp_binary_dir']

        our_list = []
        opp_list = []

        if os.path.exists(our_dir):
            our_list = [os.path.join(our_dir, name) for name in os.listdir(our_dir)
                        if os.path.isdir(os.path.join(our_dir, name))]

        if os.path.exists(opp_dir):
            opp_list = [os.path.join(opp_dir, name) for name in os.listdir(opp_dir)
                        if os.path.isdir(os.path.join(opp_dir, name))]

        return our_list, opp_list

    def run(self):
        """运行比赛"""
        try:
            our_list, opp_list = self.get_team_lists()

            if not our_list or not opp_list:
                self.error_signal.emit("球队目录为空或不存在！")
                return

            total_games = len(our_list) * len(opp_list) * self.config['every_play_times']
            game_count = 0

            # 创建结果文件
            time_str = time.strftime('%Y%m%d%H%M%S', time.localtime())
            detail_file = f"{time_str}-detail.csv"
            single_file = f"{time_str}-single.csv"

            # 初始化CSV文件
            self.init_csv_files(detail_file, single_file)

            for our_bin in our_list:
                for opp_bin in opp_list:
                    self.progress_signal.emit(game_count, total_games,
                                              f"开始比赛: {our_bin} vs {opp_bin}")

                    for a in range(self.config['every_play_times']):
                        if not self.is_running:
                            return

                        game_count += 1
                        self.progress_signal.emit(game_count, total_games,
                                                  f"第{a + 1}轮对局")

                        # 运行比赛
                        if self.config['our_left']:
                            team_left = our_bin
                            team_right = opp_bin
                        else:
                            team_left = opp_bin
                            team_right = our_bin

                        result = self.run_single_game(team_left, team_right,
                                                      self.config['exchange'])

                        if result is None:
                            status = "Error"
                            self.game_result_signal.emit(
                                os.path.basename(team_left),
                                os.path.basename(team_right),
                                0, 0, status
                            )
                        else:
                            score_left, score_right = result
                            status = "已完成"
                            self.game_result_signal.emit(
                                os.path.basename(team_left),
                                os.path.basename(team_right),
                                score_left, score_right, status
                            )

            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"比赛出错: {str(e)}")

    def run_single_game(self, team_left, team_right, exchange):
        """运行单场比赛"""
        result = None
        retry_times = 0

        while result is None and retry_times < self.config['max_retry_times']:
            if not self.is_running:
                return None

            result = self.runner.run_game(
                os.path.join(team_left, "start.sh"),
                os.path.join(team_right, "start.sh"),
                exchange
            )

            if result is None:
                retry_times += 1

        return result

    def init_csv_files(self, detail_file, single_file):
        """初始化CSV文件"""
        detail_title = ["our_bin", "opp_bin"]
        epochs = [f"epoch_{i + 1}" for i in range(self.config['every_play_times'])]
        detail_title.extend(epochs)
        detail_title.extend(["胜", "平", "负", "异常", "胜率"])

        single_title = ["our_bin", "胜", "平", "负", "异常", "胜率"]

        with open(detail_file, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(detail_title)

        with open(single_file, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(single_title)

    def stop(self):
        """停止比赛"""
        self.is_running = False
        self.runner.kill_rcssserver3d()


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.game_thread = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("3D足球比赛监控系统")
        self.setGeometry(100, 100, 1200, 800)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout()

        # 左侧配置面板
        self.config_panel = ConfigurationPanel()
        main_layout.addWidget(self.config_panel, 1)

        # 右侧显示面板
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        # 实时显示
        self.real_time_display = RealTimeDisplay()
        right_layout.addWidget(self.real_time_display, 2)

        # 控制面板
        control_panel = self.create_control_panel()
        right_layout.addWidget(control_panel)

        right_panel.setLayout(right_layout)
        main_layout.addWidget(right_panel, 2)

        central_widget.setLayout(main_layout)

        # 状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")

        # 进度条
        self.progress_bar = QProgressBar()
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.setVisible(False)

    def create_control_panel(self):
        """创建控制面板"""
        panel = QGroupBox("比赛控制")
        layout = QVBoxLayout()

        # 开始/停止按钮
        self.start_btn = QPushButton("开始比赛")
        self.start_btn.clicked.connect(self.start_game)
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")

        self.stop_btn = QPushButton("停止比赛")
        self.stop_btn.clicked.connect(self.stop_game)
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-size: 14px;")
        self.stop_btn.setEnabled(False)

        # 查看结果按钮
        self.results_btn = QPushButton("查看比赛结果")
        self.results_btn.clicked.connect(self.show_results)
        self.results_btn.setStyleSheet("background-color: #2196F3; color: white;")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.results_btn)

        layout.addLayout(button_layout)

        # 日志显示
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        panel.setLayout(layout)
        return panel

    def start_game(self):
        """开始比赛"""
        config = self.config_panel.get_config()

        # 检查目录是否存在
        if not os.path.exists(config['our_binary_dir']):
            QMessageBox.warning(self, "警告", "我方球队目录不存在！")
            return

        if not os.path.exists(config['opp_binary_dir']):
            QMessageBox.warning(self, "警告", "对方球队目录不存在！")
            return

        # 创建比赛线程
        self.game_thread = GameThread(config)
        self.game_thread.update_signal.connect(self.update_display)
        self.game_thread.game_result_signal.connect(self.add_game_record)
        self.game_thread.progress_signal.connect(self.update_progress)
        self.game_thread.finished_signal.connect(self.game_finished)
        self.game_thread.error_signal.connect(self.game_error)

        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 清空日志
        self.log_text.clear()
        self.log("开始比赛...")

        # 启动线程
        self.game_thread.start()

    def stop_game(self):
        """停止比赛"""
        if self.game_thread and self.game_thread.isRunning():
            self.game_thread.stop()
            self.game_thread.quit()
            self.game_thread.wait()
            self.log("比赛已停止")

            # 更新UI状态
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setVisible(False)

    def game_finished(self):
        """比赛完成"""
        self.log("所有比赛已完成！")

        # 更新UI状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        QMessageBox.information(self, "完成", "所有比赛已完成！")

    def game_error(self, error_msg):
        """比赛出错"""
        self.log(f"错误: {error_msg}")
        QMessageBox.critical(self, "错误", error_msg)

        # 更新UI状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

    def update_display(self, play_mode, game_time, score_left, score_right):
        """更新显示"""
        self.real_time_display.update_display(play_mode, game_time, score_left, score_right)

    def add_game_record(self, team1, team2, score1, score2, status):
        """添加比赛记录"""
        self.real_time_display.add_game_record(team1, team2, score1, score2, status)

        # 记录到日志
        self.log(f"比赛结果: {team1} {score1}:{score2} {team2} ({status})")

    def update_progress(self, current, total, message):
        """更新进度"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

        if message:
            self.status_bar.showMessage(message)

    def show_results(self):
        """显示比赛结果"""
        # 这里可以添加查看CSV文件的功能
        QMessageBox.information(self, "结果", "比赛结果已保存到CSV文件中")

    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def closeEvent(self, event):
        """关闭事件"""
        if self.game_thread and self.game_thread.isRunning():
            reply = QMessageBox.question(self, '确认',
                                         '比赛正在进行中，确定要退出吗？',
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.game_thread.stop()
                self.game_thread.quit()
                self.game_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # ==== 添加字体设置开始 ====
    # 设置应用程序支持中文
    font = QFont()

    # 尝试多个中文字体，按优先级顺序
    chinese_fonts = [
        "WenQuanYi Micro Hei",  # 文泉驿微米黑，Linux常用
        "WenQuanYi Zen Hei",  # 文泉驿正黑
        "DejaVu Sans",  # 常见字体
        "Noto Sans CJK SC",  # Google字体
        "Source Han Sans CN",  # 思源黑体
        "SimHei",  # 黑体
        "Microsoft YaHei",  # 微软雅黑
        "Arial Unicode MS"  # 备用
    ]

    # 检查系统中可用的字体
    available_fonts = QFontDatabase().families()

    # 选择第一个可用的中文字体
    selected_font = None
    for font_name in chinese_fonts:
        if font_name in available_fonts:
            selected_font = font_name
            break

    if selected_font:
        font.setFamily(selected_font)
        print(f"使用字体: {selected_font}")
    else:
        # 如果都没有，使用默认字体
        print("未找到中文字体，使用系统默认")

    font.setPointSize(10)
    app.setFont(font)
    # ==== 添加字体设置结束 ====

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()