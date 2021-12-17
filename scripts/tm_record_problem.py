# -*- coding: utf-8 -*-
import os
from datetime import datetime

import pandas as pd
import utils

# 记录问题
note_file_name = os.path.dirname(os.path.dirname(__file__)
                                 ) + '/data/' + datetime.now().strftime("%Y_%m_%d") + '_record' + '.xlsx'
COLUMNS_IPX = ['NO', 'Date', 'Time', 'Problem', 'Describe', '测试人', '车辆',  'MPD', 'MPI',
               'auto-driving-version', 'planning-version', 'perception-version',  '天气','道路类型','项目类别',
               '功能大类','经纬度', '昼/夜 ',  '车辆模式','数据链接 ']


def problem_record(name):
    def wapper():
        utils.logger.info(datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + name)
        if not os.path.exists(note_file_name):
            df = pd.DataFrame(columns=COLUMNS_IPX, index=None)
            df.to_excel(note_file_name, index=False, engine='openpyxl')
        df = pd.read_excel(note_file_name, encoding='utf-8')
        num = df.shape[0]
        df.loc[num, 'NO'] = num + 1
        df.loc[num, 'Date'] = datetime.now().strftime("%Y-%m-%d")
        df.loc[num, 'Time'] = datetime.now().strftime("%H:%M:%S")
        df.loc[num, 'Problem'] = name
        df.to_excel(note_file_name, index=False, engine='openpyxl')

    return wapper


def get_all_problems():
    if not os.path.exists(note_file_name):
        df = pd.DataFrame(columns=COLUMNS_IPX,index=None)
    else:
        df = pd.read_excel(note_file_name, encoding='utf-8')
    return df
