# -*- coding: utf-8 -*-
import json
import os
import time
from datetime import datetime

import pandas as pd
import utils


def get_planning_problem(bag_path, func_list):
    file_name = utils.BASIC_NAME + "planning" + '.xlsx'
    if not os.path.exists(file_name):
        df = pd.DataFrame(columns=['NO', 'Date', 'Time', 'Problem'], index=None)
        df.to_excel(file_name, index=False, engine='openpyxl')
    for func in func_list:
        eval(func)(bag_path, file_name)


@utils.register('示例', 'planning')
def CountMEBTimes(file_path, file_name):
    '''
    示例
    '''
    pass
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
                data = pd.read_excel(file_name, encoding='utf-8')
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
    data = pd.read_excel(file_name, encoding='utf-8')
    data.loc[1, 'activate_count'] = activate_num
    data.loc[1, 'time'] = bag_count * 5
    return


def CountCutinTimes(self, bag_data, bag_path):
    '''
    cutin场景数筛选
    '''
    is_active = True
    data = pd.read_excel('筛选记录表.xlsx', encoding='utf-8')

    for topic, msg, t in bag_data.read_messages(
            topics='/planning/vehicle_monitor'):
        if topic == '/planning/vehicle_monitor':
            try:
                obstacel_in_path = msg.obstacle_state.obstacle_in_path.position.x
                is_dbw_enabled = msg.ego_car_state.is_dbw_enabled
                cut_in_and_out = msg.obstacle_state.obstacle_in_path.cut_in_and_out
                linear_velocity = msg.ego_car_state.linear_velocity
                TTC = msg.obstacle_state.obstacle_in_path.ttc

            except:
                break

            if cut_in_and_out == 3 and is_dbw_enabled == 1 and is_active == False and TTC <= 3.5:
                is_active = True
                data_time = time.strftime("%Y%m%d %H:%M:%S", time.localtime(t.to_sec()))
                num = data.shape[0]
                data.loc[num, 'NO'] = num + 1
                data.loc[num, 'Date'] = data_time.split(' ')[0]
                data.loc[num, 'Time'] = data_time.split(' ')[1]
                data.loc[num, 'BagPath'] = bag_path
                data.loc[num, 'type'] = 'cutin场景'
                data.loc[num, 'Obstracel_X'] = obstacel_in_path
                data.loc[num, 'velocity'] = int(linear_velocity * 3.6)
                data.loc[num, 'TTC'] = round(TTC, 2)
                self.cutin += 1

            if cut_in_and_out != 3 and is_active == True:
                is_active = False

    data.to_excel('筛选记录表.xlsx', index=False, engine='openpyxl')
    return self.cutin


def CountDangerDistance(self, bag_data, bag_path):
    '''
    危险驾驶，距离前车过近
    '''

    is_active = False
    data = pd.read_excel('筛选记录表.xlsx', encoding='utf-8')

    for topic, msg, t in bag_data.read_messages(
            topics='/planning/vehicle_monitor'):
        if topic == '/planning/vehicle_monitor':
            try:
                obstacel_in_path = msg.obstacle_state.obstacle_in_path.position.x
                is_dbw_enabled = msg.ego_car_state.is_dbw_enabled
                cut_in_and_out = msg.obstacle_state.obstacle_in_path.cut_in_and_out
                linear_velocity = msg.ego_car_state.linear_velocity
                TTC = msg.obstacle_state.obstacle_in_path.ttc

            except:
                break

            if cut_in_and_out == 0 and is_dbw_enabled == 1 and is_active == False and obstacel_in_path <= 10:
                is_active = True
                data_time = time.strftime("%Y%m%d %H:%M:%S", time.localtime(t.to_sec()))
                num = data.shape[0]
                data.loc[num, 'NO'] = num + 1
                data.loc[num, 'Date'] = data_time.split(' ')[0]
                data.loc[num, 'Time'] = data_time.split(' ')[1]
                data.loc[num, 'BagPath'] = bag_path
                data.loc[num, 'type'] = '距前车过近'
                data.loc[num, 'Obstracel_X'] = obstacel_in_path
                data.loc[num, 'velocity'] = int(linear_velocity * 3.6)
                data.loc[num, 'TTC'] = round(TTC, 2)

                self.cutin += 1

            if obstacel_in_path >= 20 and is_active == True:
                is_active = False

    data.to_excel('筛选记录表.xlsx', index=False, engine='openpyxl')
    return self.cutin


def CountLaneDeviate(self, bag_data, bag_path):
    '''
    车道保持不居中
    '''
    is_active = False
    data = pd.read_excel('筛选记录表.xlsx', encoding='utf-8')

    for topic, msg, t in bag_data.read_messages(
            topics='/planning/vehicle_monitor'):
        if topic == '/planning/vehicle_monitor':
            try:
                obstacel_in_path = msg.obstacle_state.obstacle_in_path.position.x
                is_dbw_enabled = msg.ego_car_state.is_dbw_enabled
                cut_in_and_out = msg.obstacle_state.obstacle_in_path.cut_in_and_out
                linear_velocity = msg.ego_car_state.linear_velocity
                TTC = msg.obstacle_state.obstacle_in_path.ttc

            except:
                break

            if cut_in_and_out == 0 and is_dbw_enabled == 1 and is_active == False and obstacel_in_path <= 10:
                is_active = True
                data_time = time.strftime("%Y%m%d %H:%M:%S", time.localtime(t.to_sec()))
                num = data.shape[0]
                data.loc[num, 'NO'] = num + 1
                data.loc[num, 'Date'] = data_time.split(' ')[0]
                data.loc[num, 'Time'] = data_time.split(' ')[1]
                data.loc[num, 'BagPath'] = bag_path
                data.loc[num, 'type'] = '距前车过近'
                data.loc[num, 'Obstracel_X'] = obstacel_in_path
                data.loc[num, 'velocity'] = int(linear_velocity * 3.6)
                data.loc[num, 'TTC'] = round(TTC, 2)

                self.cutin += 1

            if obstacel_in_path >= 20 and is_active == True:
                is_active = False

    data.to_excel('筛选记录表.xlsx', index=False, engine='openpyxl')
    return self.cutin


def CountAcceleratedTimes(self, bag_data, bag_path):
    '''
    加减速度过大场景数据筛选
    '''
    is_active = True
    data = pd.read_excel('筛选记录表.xlsx', encoding='utf-8')

    for topic, msg, t in bag_data.read_messages(
            topics='/planning/vehicle_monitor'):
        if topic == '/planning/vehicle_monitor':
            try:
                linear_acceleration = msg.ego_car_state.linear_acceleration
                is_dbw_enabled = msg.ego_car_state.is_dbw_enabled
                obstacel_in_path = msg.obstacle_state.obstacle_in_path.position.x
                linear_velocity = msg.ego_car_state.linear_velocity
                TTC = msg.obstacle_state.obstacle_in_path.ttc
            except:
                break

            if is_dbw_enabled == 0:
                is_active = False
                continue

            if linear_acceleration <= -2 and is_active == False:
                is_active = True
                data_time = time.strftime("%Y%m%d %H:%M:%S", time.localtime(t.to_sec()))
                num = data.shape[0]
                data.loc[num, 'NO'] = num + 1
                data.loc[num, 'Date'] = data_time.split(' ')[0]
                data.loc[num, 'Time'] = data_time.split(' ')[1]
                data.loc[num, 'BagPath'] = bag_path
                data.loc[num, 'type'] = '重刹、点刹'
                data.loc[num, 'Obstracel_X'] = obstacel_in_path
                data.loc[num, 'velocity'] = int(linear_velocity * 3.6)
                data.loc[num, 'TTC'] = round(TTC, 2)

                self.acceleration += 1

            if linear_acceleration >= 0 and is_active == True:
                is_active = False

    data.to_excel('筛选记录表.xlsx', index=False, engine='openpyxl')
    return self.acceleration
