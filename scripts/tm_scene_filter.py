# -*- coding: utf-8 -*-
import os
import time

import utils
import pandas as pd


def get_scene_data(bag_path, func_list):
    file_name = utils.BASIC_NAME + "scene" + '.xlsx'
    if not os.path.exists(file_name):
        df = pd.DataFrame(columns=['NO', 'Date', 'Time', 'Problem'], index=None)
        df.to_excel(file_name, index=False, engine='openpyxl')
    for func in func_list:
        eval(func)(bag_path, file_name)


@utils.register('AEB触发场景', 'scene')
def CountAEBTimes(file_path, file_name):
    '''
    触发AEB场景数据筛选
    '''

    topic_list = ['/aeb/aebs_monitor']
    is_active = False
    activate_num = 0
    acceler_list = []
    for topic, msg, t, bag_path, bag_count in utils.get_bag_msg(file_path, topic_list):
        if topic == '/aeb/aebs_monitor':
            try:
                is_dbw = msg.ego_car_state.drive_mode
                aeb_active = msg.aeb_command.aeb_status
                obstacel_in_path = msg.aeb_obstacle_in_path.position.x
                linear_velocity = msg.ego_car_state.linear_velocity
                TTC = msg.aeb_obstacle_in_path.ttc
                acceler_x =  msg.ego_car_state.linear_acceleration
            except:
                continue
            if aeb_active == 4 and is_active == False:
                data = pd.read_excel(file_name)
                data_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t.to_sec()))
                num = data.shape[0]
                data.loc[num, 'NO'] = num + 1
                data.loc[num, 'Date'] = data_time.split(' ')[0]
                data.loc[num, 'Time'] = data_time.split(' ')[1]
                data.loc[num, 'BagPath'] = bag_path
                data.loc[num, 'Problem'] = '触发AEB'
                data.loc[num, 'Obstracel_X'] = obstacel_in_path
                data.loc[num, 'velocity'] = int(linear_velocity * 3.6)
                data.loc[num, 'TTC'] = round(TTC, 2)
                data.loc[num, 'Drive_Mode'] = is_dbw
                is_active = True
                data.to_excel(file_name, index=False, engine='openpyxl')
                activate_num += 1
                acceler_list.append(acceler_x)

            if aeb_active == 2 and is_active == True:
                data.loc[num, 'acceleration'] = max(acceler_list)
                acceler_list = []
                is_active = False
    data = pd.read_excel(file_name)
    data.loc[1, 'activate_count'] = activate_num
    data.loc[1, 'time'] = bag_count * 5
    return


@utils.register('MEB触发场景', 'scene')
def CountMEBTimes(file_path, file_name):
    '''
    触发MEB场景数据筛选
    '''

    topic_list = ['/aeb/aebs_monitor']
    is_active = False
    activate_num = 0
    for topic, msg, t, bag_path, bag_count in utils.get_bag_msg(file_path, topic_list):
        if topic == '/aeb/aebs_monitor':
            try:
                is_dbw = msg.ego_car_state.drive_mode
                meb_active = msg.meb_command.meb_status
                obstacel_in_path = msg.meb_obstacle_in_path.position.x
                linear_velocity = msg.ego_car_state.linear_velocity
                TTC = msg.meb_obstacle_in_path.ttc
            except:
                continue
            if meb_active == 4 and is_active == False:
                data = pd.read_excel(file_name)
                data_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t.to_sec()))
                num = data.shape[0]
                data.loc[num, 'NO'] = num + 1
                data.loc[num, 'Date'] = data_time.split(' ')[0]
                data.loc[num, 'Time'] = data_time.split(' ')[1]
                data.loc[num, 'BagPath'] = bag_path
                data.loc[num, 'Problem'] = '触发MEB'
                data.loc[num, 'Obstracel_X'] = obstacel_in_path
                data.loc[num, 'velocity'] = int(linear_velocity * 3.6)
                data.loc[num, 'TTC'] = round(TTC, 2)
                data.loc[num, 'Drive_Mode'] = is_dbw
                is_active = True
                data.to_excel(file_name, index=False, engine='openpyxl')
                activate_num += 1
            if meb_active == 2 and is_active == True:
                is_active = False
    data = pd.read_excel(file_name)
    data.loc[1, 'activate_count'] = activate_num
    data.loc[1, 'time'] = bag_count * 5
    return