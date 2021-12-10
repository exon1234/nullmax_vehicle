# -*- coding: utf-8 -*-
import os
import re
import shutil
import time
import traceback

import rosbag
import pandas as pd
import utils
class ExtractMoudle(object):
    def __init__(self, file_path, excel_path):
        self.file_path = file_path
        self.excel_path = excel_path
        self.timestamp_log_files = utils.get_all_files(self.file_path, 'vc1.log')
        self.GetAllBagInfo()

    def GetAllBagInfo(self):
        """
        获取所有rosbag开始和结束时间
        """
        self.bags_info = {}
        bag_files = utils.get_all_files(self.file_path, '.bag')
        if not bag_files:
            return None
        for bag in bag_files:
            time_pattern = re.compile(
                r'(\d{4}-\d{1,2}-\d{1,2}-\d{1,2}-\d{1,2}-\d{1,2})')
            matched_time = time_pattern.search(bag)
            if matched_time:
                bag_start_time = matched_time.group()
                bag_start_timestamp = int(
                    time.mktime(time.strptime(bag_start_time,
                                              "%Y-%m-%d-%H-%M-%S")))
                bag_end_timestamp = bag_start_timestamp + 300
            else:
                try:
                    bag_data = rosbag.Bag(bag)
                    bag_start_timestamp = bag_data.get_start_time()
                    bag_end_timestamp = bag_data.get_end_time()
                except (ValueError, rosbag.ROSBagException,
                        rosbag.ROSBagFormatException,
                        rosbag.ROSBagUnindexedException):
                    continue
            self.bags_info[bag] = (bag_start_timestamp, bag_end_timestamp)

    def createSavePath(self, data, problem_name):
        '''
        定义问题数据存储目录
        problem_name 要存储的问题数据文件夹名
        save_input_path 图片存储目录
        save_output_path 图片存储目录
        save_log_path log存储目录
        save_rbg_path rosbag存储目录
        save_plot_path  分析图存储目录
        :return:
        '''
        base_path = os.path.dirname(self.excel_path)
        save_path = os.path.join(base_path, data, problem_name)

        save_img_path = save_path + '/rawdata'
        save_log_path = save_path + '/log'
        save_rbg_path = save_path + '/rosbag'
        save_plot_path = save_path + '/plot'

        # if not os.path.exists(save_img_path):
        #     os.makedirs(save_img_path)
        # if not os.path.exists(save_log_path):
        #     os.makedirs(save_log_path)
        # if not os.path.exists(save_rbg_path):
        #     os.makedirs(save_rbg_path)
        # if not os.path.exists(save_plot_path):
        #     os.makedirs(save_plot_path)

        return save_img_path, save_log_path, save_rbg_path, save_plot_path

    def get_problem_time(self, problem_strtime):

        '''
        获取问题前后15s时间'
        problem_strtime: 问题时间
        '''
        start_timestamp = time.mktime(time.strptime(problem_strtime, "%Y-%m-%d%H:%M:%S")) - 15
        end_timestamp = start_timestamp + 30
        if self.excel_path.endswith('perception.xlsx'):
            start_timestamp = time.mktime(time.strptime(problem_strtime, "%Y-%m-%d%H:%M:%S")) - 2
            end_timestamp = start_timestamp + 4

        return start_timestamp, end_timestamp

    def CopyRawdataToPath(self, save_img_path, problem_strtime):
        """
        拷贝图片
        timestamp_log_files, 图片log文件
        start_timestamp,  问题数据开始时间
        end_timestamp, 问题数据结束时间
        save_img_path, 问题图片存储路径
        """

        start_timestamp, end_timestamp = self.get_problem_time(problem_strtime)
        match_pattern = re.compile(r'([0-9]{16}) frame_id = ([0-9]{1,9})')
        if not self.timestamp_log_files:
            return
        for log_file in self.timestamp_log_files:
            save_path = os.path.join(save_img_path, os.path.abspath(log_file).split('/')[-3])
            with open(log_file, 'r') as fp:
                matched_list = match_pattern.findall(fp.read())
                if not matched_list:
                    continue
                rawdata_start_timestamp = int(matched_list[0][0][:10])
                rawdata_end_timestamp = int(matched_list[-1][0][:10])
                if start_timestamp < rawdata_end_timestamp and end_timestamp > rawdata_start_timestamp:
                    if not os.path.exists(save_path):
                        os.makedirs(save_path)
                    shutil.copy(log_file, save_path)
                    for timestamp, frame_id in matched_list:
                        if int(timestamp[:10]) < start_timestamp:
                            continue
                        if int(timestamp[:10]) > end_timestamp:
                            break
                        rawdata_source_name = os.path.join(
                            os.path.dirname(log_file), 'frame_vc1_' + frame_id + '.bmp')
                        if os.path.exists(rawdata_source_name):
                            shutil.copy(rawdata_source_name, save_path)
            # 感知log数据拷贝
            try:
                log_name = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(log_file))),
                                        'vehicle_state.log')
                camera_extrinsic = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(log_file))),
                                                'camera_extrinsic.txt')
                if os.path.exists(log_name):
                    shutil.copy(log_name, save_img_path)

                if os.path.exists(camera_extrinsic):
                    shutil.copy(camera_extrinsic, save_img_path)
            except:
                pass

    def CopyRosbagToPath(self, save_rbg_path, problem_strtime):
        """
        拷贝rosbag文件
        """
        bag_path = []
        start_timestamp, end_timestamp = self.get_problem_time(problem_strtime)
        if not self.bags_info:
            return
        for bag, info in self.bags_info.items():
            if start_timestamp < info[1] and end_timestamp > info[0]:
                if not os.path.exists(save_rbg_path):
                    os.makedirs(save_rbg_path)
                save_name = os.path.join(save_rbg_path, os.path.basename(bag))
                path = shutil.copyfile(bag, save_name)
                bag_path.append(path)
        return bag_path if bag_path else None

    def __call__(self, *args, **kwargs):
        df = pd.read_excel(self.excel_path)
        for row in df.index.values:
            try:
                utils.logger.info('开始处理问题数据%s' % df.iloc[row, 0])
                problem_time = str(df.iloc[row, 2])
                problem_data = str(df.iloc[row, 1])
                problem_name = 'FAULT-' + str(df.iloc[row, 0])
                problem_strtime = problem_data + problem_time
                save_img_path, save_log_path, save_rbg_path, save_plot_path = self.createSavePath(
                    problem_data, problem_name)
                self.CopyRawdataToPath(save_img_path, problem_strtime)
                if not self.excel_path.endswith('perception.xlsx'):
                    self.CopyRosbagToPath(save_rbg_path, problem_strtime)
            except:
                utils.logger.error(traceback.format_exc())
                print('数据分拣失败%s' % df.iloc[row, 0])
                continue
        utils.logger.info('全部数据分拣完成')
