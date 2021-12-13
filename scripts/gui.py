# -*- coding: utf-8 -*-
"""
程序主窗口
"""
import os
import sys
import traceback

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import tm_format_conversion
import tm_record_problem
import tm_extract_data
import tm_scene_filter
import tm_perception_filter
import tm_replay_analyer
import tm_planning_filter
import utils


def singleton(cls, *args, **kwargs):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


# 回放数据分析
@singleton
class KPIWindows(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.InitUI()
        self.InitLayout()
        self.perce_file_path = ''
        self.label_file_path = ''
        self.label_json_files = None
        self.perce_json_files = None

    def InitUI(self):
        self.setWindowTitle('KPI Windows')
        self.setGeometry(600, 400, 480, 500)
        self.btn_back = QPushButton('返回主页')
        self.btn_analy_KPI = QPushButton('开始处理数据')
        self.file_label_perce = DropArea('拖入回放结果或原图目录')
        self.file_label_label = DropArea('拖入标注真值数据目录')
        self.btn_analy_KPI.clicked.connect(self.KPIAnaly)
        self.btn_back.clicked.connect(self.slot_show_main)
        self.file_label_perce.path_signal.connect(self.FilePerceCallback)
        self.file_label_label.path_signal.connect(self.FileLabelCallback)
        self.cb = {}
        for key, value in utils.FUNCTION_SET.items():
            if value[1] == 'KPI':
                btn = QCheckBox(key, self)
                self.cb[key] = btn

    def InitLayout(self):
        vbox = QVBoxLayout(QWidget(self))
        gbox = QGridLayout()
        positions = [(i, j) for i in range(8) for j in range(3)]
        for temp, position in zip(self.cb.values(), positions):
            gbox.addWidget(temp, *position)
        vbox.addWidget(self.file_label_perce)
        vbox.addWidget(self.file_label_label)
        vbox.addLayout(gbox)
        vbox.addWidget(self.btn_analy_KPI)
        vbox.addWidget(self.btn_back)
        self.setLayout(vbox)

    def FilePerceCallback(self, path):
        self.perce_json_files = utils.get_all_files(path, '.json')
        if self.perce_json_files:
            self.perce_file_path = path
            return
        if not self.perce_json_files:
            # self.perce_json_files = utils.get_all_files(path, '.png') + utils.get_all_files(path, '.yuv')
            self.perce_json_files = utils.get_all_files(path, '.png')
            self.perce_file_path = path
            return
        self.file_label_perce.setText('拖入回放结果或原图目录')
        print('No json in path!')

    def FileLabelCallback(self, path):
        self.label_json_files = utils.get_all_files(path, '.json')
        if self.label_json_files:
            self.label_file_path = path
            return
        self.file_label_label.setText('拖入标注真值数据目录')
        print('No json in path!')

    def KPIAnaly(self):
        if not self.perce_json_files:
            return
        func_list = []
        for key, value in self.cb.items():
            if value.isChecked():
                func_list.append(utils.FUNCTION_SET[key][0])
        if func_list:
            tm_replay_analyer.get_replay_result(self.label_json_files, self.perce_json_files, func_list)

    def slot_show_main(self):
        self.hide()
        self.mainwindows = MainWindows()
        self.mainwindows.show()


# 实车感知问
@singleton
class PerceptionWindows(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.InitUI()
        self.InitLayout()
        self.file_path = ''

    def InitUI(self):
        self.setWindowTitle('Perception Windows')
        self.setGeometry(600, 400, 480, 360)
        self.btn_back = QPushButton('返回主页')
        self.btn_analy_perception = QPushButton('开始处理数据')
        self.file_label = DropArea('拖入数据目录')
        self.btn_back.clicked.connect(self.slot_show_main)
        self.btn_analy_perception.clicked.connect(self.perception_problem_filter)
        self.file_label.path_signal.connect(self.FileCallback)
        self.cb = {}
        for key, value in utils.FUNCTION_SET.items():
            if value[1] == 'perception':
                btn = QCheckBox(key, self)
                self.cb[key] = btn

    def InitLayout(self):
        vbox = QVBoxLayout(QWidget(self))
        gbox = QGridLayout()
        positions = [(i, j) for i in range(8) for j in range(3)]
        for temp, position in zip(self.cb.values(), positions):
            gbox.addWidget(temp, *position)
        vbox.addWidget(self.file_label)
        vbox.addLayout(gbox)
        vbox.addWidget(self.btn_analy_perception)
        vbox.addWidget(self.btn_back)
        self.setLayout(vbox)

    def FileCallback(self, path):
        self.rosbag_files = utils.get_all_files(path, '.bag')
        if self.rosbag_files:
            self.file_path = path
            return
        self.file_label.setText('拖入数据目录')
        print('No rosbag in path!')

    def perception_problem_filter(self):
        if not os.path.isdir(self.file_path):
            return
        func_list = []
        for key, value in self.cb.items():
            if value.isChecked():
                func_list.append(utils.FUNCTION_SET[key][0])
        if func_list:
            tm_perception_filter.get_perception_problem(self.file_path, func_list)

    def slot_show_main(self):
        self.hide()
        self.mainwindows = MainWindows()
        self.mainwindows.show()


# 浏览数据(delay)
@singleton
class BrowseWindows(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.InitUI()
        self.InitLayout()

    def InitUI(self):
        self.setWindowTitle('Browse Windows')
        self.setGeometry(600, 400, 480, 240)
        self.btn0 = QPushButton('返回主页', self)
        self.btn1 = QPushButton('open')
        self.label1 = QLabel("add a image file")
        self.btn0.clicked.connect(self.slot_show_main)

    def InitLayout(self):
        v_box = QVBoxLayout()
        v_box.addWidget(self.label1)
        v_box.addWidget(self.btn1)
        v_box.addWidget(self.btn0)
        self.setLayout(v_box)

    def slot_show_main(self):
        self.hide()
        self.mainwindows = MainWindows()
        self.mainwindows.show()


# 格式转换
@singleton
class FormatWindows(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.InitUI()
        self.InitLayout()
        self.file_path = ''
        self.save_file_path = ''

    def InitUI(self):
        self.setWindowTitle('Format Windows')
        self.setGeometry(600, 400, 800, 240)
        self.btn_back = QPushButton('返回主页', self)
        self.btn_img2avi = QPushButton('img_2_avi', self)
        self.btn_png2yuv = QPushButton('png_2_yuv', self)
        self.btn_png2bmp = QPushButton('png_2_bmp', self)
        # self.btn_label2split = QPushButton('label_split', self)
        self.file_label = DropArea('拖入数据目录')
        self.result_label = DropArea('拖入目标目录')
        self.btn_back.clicked.connect(self.slot_show_main)
        self.btn_img2avi.clicked.connect(self.img_conversed_video)
        self.btn_png2yuv.clicked.connect(self.png_conversed_yuv)
        self.btn_png2bmp.clicked.connect(self.png_conversed_bmp)
        # self.btn_label2split.clicked.connect(self.label_split_more)
        self.file_label.path_signal.connect(self.FileCallback)
        self.result_label.path_signal.connect(self.SavePathCallback)

    def InitLayout(self):
        w_box = QVBoxLayout(QWidget(self))
        hbox = QHBoxLayout()
        vbox1 = QVBoxLayout()
        vbox2 = QVBoxLayout()
        vbox1.addWidget(self.btn_img2avi)
        vbox1.addWidget(self.btn_png2yuv)
        vbox1.addWidget(self.btn_png2bmp)
        # vbox1.addWidget(self.btn_label2split)
        vbox2.addWidget(self.file_label)
        vbox2.addWidget(self.result_label)
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)
        w_box.addLayout(hbox)
        w_box.addWidget(self.btn_back)
        self.setLayout(w_box)

    def FileCallback(self, path):
        if os.path.exists(path):
            self.file_path = path
            return
        self.file_label.setText('拖原始数据目录')
        print('数据不存在')

    def SavePathCallback(self, path):
        if os.path.isdir(path):
            self.save_file_path = path
            return
        self.file_label.setText('拖入目标目录')
        print('数据不存在')

    def img_conversed_video(self):
        if not os.path.isdir(self.file_path):
            print('请拖入数据目录')
            return
        tm_format_conversion.img_to_video(self.file_path, '.bmp', self.save_file_path)
        tm_format_conversion.img_to_video(self.file_path, '.png', self.save_file_path)

    def png_conversed_bmp(self):
        if not self.file_path:
            return
        tm_format_conversion.png_to_bmp(self.file_path, self.save_file_path)

    def png_conversed_yuv(self):
        if not self.file_path:
            return
        tm_format_conversion.png_to_yuv(self.file_path, self.save_file_path)

    # def label_split_more(self):
    #     if not self.file_path:
    #         return
    #     tm_format_conversion.split_label_file(self.file_path, self.save_file_path)

    def slot_show_main(self):
        self.hide()
        self.mainwindows = MainWindows()
        self.mainwindows.show()


# 规划问题分析(delay)
@singleton
class FilterWindows(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.InitUI()
        self.InitLayout()

    def InitUI(self):
        self.setWindowTitle('Screen Windows')
        self.setGeometry(600, 400, 480, 240)
        self.filter_problem = QPushButton('开始处理数据')
        self.btn_back = QPushButton('返回主页')
        self.filter_problem.clicked.connect(self.filter_planning_problem)
        self.btn_back.clicked.connect(self.slot_show_main)
        self.file_label = DropArea('拖入数据目录')
        self.file_label.path_signal.connect(self.FileCallback)
        self.cb = {}
        for key, value in utils.FUNCTION_SET.items():
            if value[1] == 'planning':
                btn = QCheckBox(key, self)
                self.cb[key] = btn

    def InitLayout(self):
        vbox = QVBoxLayout()
        gbox = QGridLayout()
        positions = [(i, j) for i in range(8) for j in range(3)]
        for temp, position in zip(self.cb.values(), positions):
            gbox.addWidget(temp, *position)
        vbox.addWidget(self.file_label)
        vbox.addLayout(gbox)
        vbox.addWidget(self.filter_problem)
        vbox.addWidget(self.btn_back)
        self.setLayout(vbox)

    def FileCallback(self, path):
        self.timestamp_log_files = utils.get_all_files(path, '.log')
        self.rosbag_files = utils.get_all_files(path, '.bag')
        if self.timestamp_log_files or self.rosbag_files:
            self.file_path = path
            return
        self.file_label.setText('拖入数据目录')
        print('No rosbag and log in path!')

    def filter_planning_problem(self):
        if os.path.isdir(self.file_path):
            func_list = []
            for key, value in self.cb.items():
                if value.isChecked():
                    func_list.append(utils.FUNCTION_SET[key][0])
            if func_list:
                tm_planning_filter.get_planning_problem(self.file_path, func_list)

    def slot_show_main(self):
        self.hide()
        self.mainwindows = MainWindows()
        self.mainwindows.show()


# 场景数据分析(delay)
@singleton
class SceneWindows(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.InitUI()
        self.InitLayout()
        self.file_path = ''

    def InitUI(self):
        self.setWindowTitle('Screen Windows')
        self.setGeometry(600, 400, 480, 240)
        self.btn_back = QPushButton('返回主页')
        self.btn_analy_scene = QPushButton('开始处理数据')
        self.file_label = DropArea('拖入数据目录')
        self.btn_back.clicked.connect(self.slot_show_main)
        self.btn_analy_scene.clicked.connect(self.filter_scene)
        self.file_label.path_signal.connect(self.FileCallback)
        self.cb = {}
        for key, value in utils.FUNCTION_SET.items():
            if value[1] == 'scene':
                btn = QCheckBox(key, self)
                self.cb[key] = btn

    def InitLayout(self):
        vbox = QVBoxLayout()
        gbox = QGridLayout()
        positions = [(i, j) for i in range(8) for j in range(3)]
        for temp, position in zip(self.cb.values(), positions):
            gbox.addWidget(temp, *position)
        vbox.addWidget(self.file_label)
        vbox.addLayout(gbox)
        vbox.addWidget(self.btn_analy_scene)
        vbox.addWidget(self.btn_back)
        self.setLayout(vbox)

    def FileCallback(self, path):
        self.rosbag_files = utils.get_all_files(path, '.bag')
        if not self.rosbag_files:
            self.file_label.setText('拖入数据目录')
            print('No rosbag in path!')
            return
        self.file_path = path

    def filter_scene(self):
        if os.path.isdir(self.file_path):
            func_list = []
            for key, value in self.cb.items():
                if value.isChecked():
                    func_list.append(utils.FUNCTION_SET[key][0])
            if func_list:
                tm_scene_filter.get_scene_data(self.file_path, func_list)

    def slot_show_main(self):
        self.hide()
        self.mainwindows = MainWindows()
        self.mainwindows.show()


# 问题数据切片
@singleton
class ExtractWindows(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.InitUI()
        self.InitLayout()
        self.excel_path = ''
        self.file_path = ''

    def InitUI(self):
        self.setWindowTitle('Extract Windows')
        self.setGeometry(600, 400, 480, 360)
        self.btn_back = QPushButton('返回主页', self)
        self.btn_extract = QPushButton('数据分拣', self)
        self.excel_label = DropArea('拖入问题记录表')
        self.file_label = DropArea('拖入数据目录')
        self.btn_back.clicked.connect(self.slot_show_main)
        self.btn_extract.clicked.connect(self.ExtractPrbolem)
        self.excel_label.path_signal.connect(self.ExcelCallback)
        self.file_label.path_signal.connect(self.FileCallback)

    def InitLayout(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.excel_label)
        vbox.addWidget(self.file_label)
        vbox.addWidget(self.btn_extract)
        vbox.addWidget(self.btn_back)
        self.setLayout(vbox)

    def ExcelCallback(self, path):
        if str(path).endswith('xlsx'):
            self.excel_path = path
            return
        self.excel_label.setText('拖入问题记录表')
        print('Not excel file!')

    def FileCallback(self, path):
        self.timestamp_log_files = utils.get_all_files(path, '.log')
        self.rosbag_files = utils.get_all_files(path, '.bag')
        if self.timestamp_log_files or self.rosbag_files:
            self.file_path = path
            return
        self.file_label.setText('拖入数据目录')
        print('No rosbag and log in path!')

    def ExtractPrbolem(self):
        try:
            tm_extract_data.ExtractMoudle(self.file_path, self.excel_path)()
        except:
            utils.logger.info(traceback.format_exc())

    def slot_show_main(self):
        self.hide()
        self.mainwindows = MainWindows()
        self.mainwindows.show()


# 实车记录问题
@singleton
class RecordWindows(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.InitUI()
        self.InitLayout()
        self.row_dict = {}

    def InitUI(self):
        self.setWindowTitle('Record Windows')
        self.setGeometry(600, 400, 900, 400)
        self.names = ['跑偏', '重刹', 'cutin不减速',
                      '变道超调', '跟车不刹车', '新增问题']
        self.btn_back = QPushButton('返回主页', self)
        self.btn_flush = QPushButton('更新记录')
        self._problem_list = QTableWidget()
        self.init_problem_list_module()
        self.btn_back.clicked.connect(self.slot_show_main)
        self.btn_flush.clicked.connect(self.flush_problem_describe)

    def InitLayout(self):
        global_box = QHBoxLayout()
        w_box = QVBoxLayout(QWidget(self))
        vbox = QVBoxLayout()
        gbox = QGridLayout()
        gbox.SizeConstraint()
        positions = [(i, j) for i in range(8) for j in range(3)]
        for name, position in zip(self.names, positions):
            btn = QPushButton(name, self)
            btn.clicked.connect(tm_record_problem.problem_record(name))
            btn.clicked.connect(self.append_problem_line)
            gbox.addWidget(btn, *position)
        vbox.addWidget(self._problem_list)
        vbox.addWidget(self.btn_flush)
        global_box.addLayout(gbox)
        global_box.addLayout(vbox)
        w_box.addLayout(global_box)
        w_box.addWidget(self.btn_back)
        self.setLayout(w_box)

    def init_problem_list_module(self):
        """
        初始化问题处理列表
        """
        self._problem_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._problem_list.horizontalHeader().setStretchLastSection(True)
        self._problem_list.setSelectionMode(QAbstractItemView.NoSelection)
        self._problem_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._problem_list.setColumnCount(5)
        self._problem_list.setHorizontalHeaderLabels(['NO', 'Date', 'Time', 'Problem', 'Describe'])

    def append_problem_line(self):
        """
        界面右侧增加当前问题行
        """
        row_count = self._problem_list.rowCount()
        self._problem_list.setRowCount(row_count + 1)
        df = tm_record_problem.get_all_problems()
        row = df.shape[0] - 1
        self.row_dict[str(row_count)] = row
        self._problem_list.setItem(row_count, 0, QTableWidgetItem(str(df.iloc[row, 0])))
        self._problem_list.setItem(row_count, 1, QTableWidgetItem(df.iloc[row, 1]))
        self._problem_list.setItem(row_count, 2, QTableWidgetItem(df.iloc[row, 2]))
        self._problem_list.setItem(row_count, 3, QTableWidgetItem(df.iloc[row, 3]))
        self._problem_list.setCellWidget(row_count, 4, QLineEdit())

    def flush_problem_describe(self):
        df = tm_record_problem.get_all_problems()
        for row_count in range(self._problem_list.rowCount()):
            try:
                df.iloc[self.row_dict[str(row_count)], 4] = self._problem_list.cellWidget(row_count, 4).text()
            except Exception as E:
                utils.logger.info(E)
                continue
            df.to_excel(tm_record_problem.note_file_name, index=False, engine='openpyxl')

    def slot_show_main(self):
        self.hide()
        self.mainwindows = MainWindows()
        self.mainwindows.show()


# 主窗口
@singleton
class MainWindows(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.InitUI()
        self.InitLayout()
        self.timestamp_log_path = ''
        self.rosbag_sequence_path = ''

    def InitUI(self):
        self.setWindowTitle('NM TestTool')
        # self.setGeometry(600, 400, 900, 400)
        self.setGeometry(600, 400, 180, 400)
        self.btn_record_wd = QPushButton('实车问题记录', self)
        self.btn_extract_wd = QPushButton('数据切片', self)
        self.btn_planning_wd = QPushButton('规划问题筛选', self)
        self.btn_scene_wd = QPushButton('场景数据筛选', self)
        self.btn_format_wd = QPushButton('数据格式转换', self)
        self.btn_browse_wd = QPushButton('查询数据', self)
        self.btn_perception_wd = QPushButton('感知问题筛选', self)
        self.btn_kpi_wd = QPushButton('KPI数据分析', self)
        # self.timestamp_label = DropArea('拖入图片目录')
        # self.sequence_label = DropArea('拖入rosbag目录')
        # self.timestamp_label.path_signal.connect(self.TimestampCallback)
        # self.sequence_label.path_signal.connect(self.SequeneCallback)
        self.btn_record_wd.clicked.connect(self.slot_show_record)
        self.btn_extract_wd.clicked.connect(self.slot_show_extract)
        self.btn_planning_wd.clicked.connect(self.slot_show_filter)
        self.btn_scene_wd.clicked.connect(self.slot_show_scene)
        self.btn_format_wd.clicked.connect(self.slot_show_format)
        self.btn_browse_wd.clicked.connect(self.slot_show_browse)
        self.btn_perception_wd.clicked.connect(self.slot_show_perception)
        self.btn_kpi_wd.clicked.connect(self.slot_show_KPI)

    def InitLayout(self):
        wbox = QHBoxLayout(QWidget(self))
        vbox = QVBoxLayout()
        vbox2 = QVBoxLayout()
        vbox.addWidget(self.btn_browse_wd)
        vbox.addWidget(self.btn_extract_wd)
        vbox.addWidget(self.btn_format_wd)
        vbox.addWidget(self.btn_record_wd)
        vbox.addWidget(self.btn_planning_wd)
        vbox.addWidget(self.btn_scene_wd)
        vbox.addWidget(self.btn_perception_wd)
        vbox.addWidget(self.btn_kpi_wd)
        # 预保留功能，主窗口添加数据分析使用
        # vbox2.addWidget(self.timestamp_label)
        # vbox2.addWidget(self.sequence_label)
        wbox.addLayout(vbox)
        wbox.addLayout(vbox2)
        self.setLayout(wbox)

    def TimestampCallback(self, path):
        if utils.get_all_files(path, '.log'):
            self.rosbag_sequence_path = path
            return
        self.timestamp_label.setText('拖入图片目录')
        print('No rosbag in path!')

    def SequeneCallback(self, path):
        if utils.get_all_files(path, '.bag'):
            self.rosbag_sequence_path = path
            return
        self.sequence_label.setText('拖入rosbag目录')
        print('No rosbag in path!')

    def slot_show_record(self):
        self.hide()
        self.other = RecordWindows()
        self.other.show()

    def slot_show_extract(self):
        self.hide()
        self.other = ExtractWindows()
        self.other.show()

    def slot_show_filter(self):
        self.hide()
        self.other = FilterWindows()
        self.other.show()

    def slot_show_scene(self):
        self.hide()
        self.other = SceneWindows()
        self.other.show()

    def slot_show_format(self):
        self.hide()
        self.other = FormatWindows()
        self.other.show()

    def slot_show_browse(self):
        self.hide()
        self.other = BrowseWindows()
        self.other.show()

    def slot_show_perception(self):
        self.hide()
        self.other = PerceptionWindows()
        self.other.show()

    def slot_show_KPI(self):
        self.hide()
        self.other = KPIWindows()
        self.other.show()


class DropArea(QLabel):
    path_signal = pyqtSignal(str)

    def __init__(self, text):
        super(DropArea, self).__init__()
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setAutoFillBackground(True)
        pe = QPalette()
        pe.setColor(QPalette.WindowText, Qt.blue)
        pe.setColor(QPalette.Window, Qt.gray)
        self.setPalette(pe)
        self.setText(text)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.EditText(event.mimeData().urls()[0].toString())

    def EditText(self, path):
        if 0 == path.find('file:///'):
            path = path.replace('file:///', '/')
        self.setText(path)
        self.path_signal.emit(path)


def main():
    app = QApplication(sys.argv)
    Main = MainWindows()
    Main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
