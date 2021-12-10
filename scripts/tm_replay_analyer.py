# -*- coding: utf-8 -*-
import copy
from hashlib import md5
import json
import shutil
from datetime import datetime
import cv2
import tqdm

from config.cfg import Config
import utils
from jyftools import *


def get_replay_result(label_jsons, perce_jsons, func_list):
    file_name = utils.BASIC_NAME + "replay" + '.xlsx'
    # if not os.path.exists(file_name):
    #     df = pd.DataFrame(columns=['NO', 'Date', 'Time', 'Problem'], index=None)
    #     df.to_excel(file_name, index=False, engine='openpyxl')
    for func in func_list:
        eval(func)(label_jsons, perce_jsons, file_name)


@utils.register('环视-recall', 'KPI')
def get_recall_side(label_jsons, perce_jsons, file_name):
    '''召回率获取'''
    if not label_jsons or len(label_jsons) != 1 or not perce_jsons[0].endswith('.json'):
        print('无可用检测标注数据')
        return
    configs = Config.replay_configs()
    enum_obstacle_type = configs["enum_obstacle"]
    ''' result_recall_demo = [label_num,true_num,false_num]'''
    result_car = [0, 0, 0]
    result_truck = [0, 0, 0]
    result_bus = [0, 0, 0]
    result_pedestrian = [0, 0, 0]
    result_bicycle = [0, 0, 0]
    result_motorcycle = [0, 0, 0]
    result_tricycle = [0, 0, 0]
    result_rider = [0, 0, 0]
    result_other = [0, 0, 0]

    for label_result, perce_result in utils.get_match_img_one_json(label_jsons, perce_jsons):
        if not label_result or not perce_result:
            continue
        for label_data, perce_data in utils.get_match_obstacle_recall_side(label_result, perce_result):
            if not label_data:
                continue
            label_type = label_data['tags']["class"]
            perce_type = None if not perce_data else enum_obstacle_type[perce_data["obstacle_type"]]
            try:
                result = eval('result_' + label_type)
                result[0] += 1
            except NameError as E:
                result = result_other
                result[0] += 1
            if perce_type and perce_type == label_type:
                result[1] += 1
            elif perce_type:
                result[2] += 1

    is_duplicate = False
    print('-*-' * 50)
    for value in enum_obstacle_type.values():
        try:
            result = eval('result_' + value)
        except NameError as E:
            if is_duplicate:
                continue
            is_duplicate = True
            value = 'other'
            result = result_other
            continue
        obstacle_recall = 0 if result[0] == 0 else float(result[1] + result[2]) / result[0]
        utils.logger.info(
            '{}'.format(value).ljust(12, ' ') + 'recall: {}  {}'.format(round(obstacle_recall, 3), result))


@utils.register('环视-precision', 'KPI')
def get_precision_side(label_jsons, perce_jsons, file_name):
    '''精确率获取'''
    if not label_jsons or len(label_jsons) != 1 or not perce_jsons[0].endswith('.json'):
        print('无可用检测标注数据')
        return
    configs = Config.replay_configs()
    enum_obstacle_type = configs["enum_obstacle"]
    '''result_recall_demo = [label_num,TP,FP]'''
    result_car = [0, 0, 0]
    result_truck = [0, 0, 0]
    result_bus = [0, 0, 0]
    result_pedestrian = [0, 0, 0]
    result_bicycle = [0, 0, 0]
    result_motorcycle = [0, 0, 0]
    result_tricycle = [0, 0, 0]
    result_rider = [0, 0, 0]
    result_other = [0, 0, 0]

    for label_result, perce_result in utils.get_match_img_one_json(label_jsons, perce_jsons):
        if not perce_result:
            continue
        for label_data, perce_data in utils.get_match_obstacle_precision_side(label_result, perce_result):
            if not perce_data:
                continue
            perce_type = enum_obstacle_type[perce_data["obstacle_type"]]
            label_type = label_data['tags']["class"] if label_data else None
            try:
                result = eval('result_' + perce_type)
            except NameError as E:
                result = result_other

            if perce_type == label_type:
                result[1] += 1
            else:
                result[2] += 1

    is_duplicate = False
    print('-*-' * 50)
    for value in enum_obstacle_type.values():
        try:
            result = eval('result_' + value)
        except:
            if is_duplicate:
                continue
            value = 'other'
            result = result_other
            is_duplicate = True
            continue
        obstacle_precision = 0 if result[1] + result[2] == 0 else float(result[1]) / (result[2] + result[1])
        utils.logger.info(
            '{}'.format(value).ljust(12, ' ') + 'precision: {}  {}'.format(round(obstacle_precision, 3), result))


@utils.register('环视-测距', 'KPI')
def get_distance_side(label_jsons, perce_jsons, file_name):
    '''测距效果获取'''
    # ranges = ('0 ~ 20m', '20 ~ 35m', '35 ~ 60m')
    result_car = ([[], [], [], []], [[], [], [], []])
    result_truck = ([[], [], [], []], [[], [], [], []])
    result_bus = ([[], [], [], []], [[], [], [], []])
    result_ped = ([[], [], [], []], [[], [], [], []])
    result_bicycle = ([[], [], [], []], [[], [], [], []])
    result_motocycle = ([[], [], [], []], [[], [], [], []])
    result_tricycle = ([[], [], [], []], [[], [], [], []])
    result_other = ([[], [], [], []], [[], [], [], []])
    configs = Config.replay_configs()
    enum_obstacle_type = configs["enum_obstacle"]
    if not label_jsons or len(label_jsons) <= 1 or not perce_jsons[0].endswith('.json'):
        print('无可用测距标注数据')
        return
    for label_result, perce_result in utils.get_match_img_more_json(label_jsons, perce_jsons):
        if not label_result or not perce_result:
            continue
        for label_data, perce_data in utils.get_match_obstacle_more(label_result, perce_result):
            if not perce_data or perce_data['obstacle_valid'] == 0:
                continue
            label_type = enum_obstacle_type[label_data['type']]
            label_position_x = label_data['box_3d']["dists"]['z']
            label_position_y = label_data['box_3d']["dists"]['x']
            perce_position_x = perce_data["position"]['obstacle_pos_x_filter']
            perce_position_y = perce_data["position"]['obstacle_pos_y_filter']
            distance_tolerance_x = abs(perce_position_x - label_position_x)
            distance_tolerance_y = abs(perce_position_y - label_position_y)
            try:
                result = eval('result_' + label_type)
            except:
                result = result_other
            if label_position_x <= 20:
                result[0][0].append(distance_tolerance_x)
            if label_position_x <= 35:
                result[0][1].append(distance_tolerance_x)
            if label_position_x <= 60:
                result[0][2].append(distance_tolerance_x)
            if label_position_x > 60:
                result[0][3].append(distance_tolerance_x)

            if label_position_y <= 20:
                result[1][0].append(distance_tolerance_y)
            if label_position_y <= 35:
                result[1][1].append(distance_tolerance_y)
            if label_position_y <= 60:
                result[1][2].append(distance_tolerance_y)
            if label_position_y > 60:
                result[0][3].append(distance_tolerance_y)
    utils.logger.info('type    0~20  20~35  35~60')
    for value in enum_obstacle_type.values():
        try:
            result = eval('result_' + value)
        except:
            value = 'other'
            result = result_other
        finally:
            result[0][0] = 0 if not result[0][0] else sum(result[0][0]) / len(result[0][0])
            result[0][1] = 0 if not result[0][1] else sum(result[0][1]) / len(result[0][1])
            result[0][2] = 0 if not result[0][2] else sum(result[0][2]) / len(result[0][2])
            result[1][0] = 0 if not result[1][0] else sum(result[1][0]) / len(result[1][0])
            result[1][1] = 0 if not result[1][1] else sum(result[1][1]) / len(result[1][1])
            result[1][2] = 0 if not result[1][2] else sum(result[1][2]) / len(result[1][2])
            utils.logger.info(
                '{}'.format(value).ljust(10, ' ') + '{}  {}  {}'.format(round(result[0][0], 2), round(result[0][1], 2),
                                                                        round(result[0][2], 2)))


@utils.register('环视-测速', 'KPI')
def get_velocity_side(label_jsons, perce_jsons, file_name):
    '''测距效果获取'''
    ranges = ('0 ~ 20m', '20 ~ 35m', '35 ~ 60m')
    result_car = ([[], [], [], []], [[], [], [], []])
    result_truck = ([[], [], [], []], [[], [], [], []])
    result_bus = ([[], [], [], []], [[], [], [], []])
    result_ped = ([[], [], [], []], [[], [], [], []])
    result_bicycle = ([[], [], [], []], [[], [], [], []])
    result_motocycle = ([[], [], [], []], [[], [], [], []])
    result_tricycle = ([[], [], [], []], [[], [], [], []])
    result_other = ([[], [], [], []], [[], [], [], []])
    configs = Config.replay_configs()
    enum_obstacle_type = configs["enum_obstacle"]
    if not label_jsons:
        return
    if len(label_jsons) == 1:
        print('无可用测距标注数据')
        return
    for label_result, perce_result in utils.get_match_img_more_json(label_jsons, perce_jsons):
        if not label_result or not perce_result:
            continue
        for label_data, perce_data in utils.get_match_obstacle_more(label_result, perce_result):

            if not perce_data:
                continue
            if perce_data['obstacle_valid'] == 0:
                continue
            label_type = enum_obstacle_type[label_data['type']]
            label_velocity_x = label_data['box_3d']["dists"]['z']
            label_velocity_y = label_data['box_3d']["dists"]['x']
            perce_velocity_x = perce_data["velocity"]['obstacle_rel_vel_x_filter']
            perce_velocity_y = perce_data["velocity"]['obstacle_rel_vel_y_filter']
            velocity_tolerance_x = perce_velocity_x - label_velocity_x
            velocity_tolerance_y = perce_velocity_y - label_velocity_y

            try:
                result = eval('result_' + label_type)
            except:
                result = result_other
            if label_velocity_x <= 20:
                result[0][0].append(velocity_tolerance_x)
            if label_velocity_x <= 35:
                result[0][1].append(velocity_tolerance_x)
            if label_velocity_x <= 60:
                result[0][2].append(velocity_tolerance_x)

            if label_velocity_y <= 20:
                result[1][0].append(velocity_tolerance_y)
            if label_velocity_y <= 35:
                result[1][1].append(velocity_tolerance_y)
            if label_velocity_y <= 60:
                result[1][2].append(velocity_tolerance_y)
    utils.logger.info('type    0~20  20~35  35~60')
    for value in enum_obstacle_type.values():
        try:
            result = eval('result_' + value)
        except:
            value = 'other'
            result = result_other
        finally:
            result[0][0] = 0 if not result[0][0] else sum(result[0][0]) / len(result[0][0])
            result[0][1] = 0 if not result[0][1] else sum(result[0][1]) / len(result[0][1])
            result[0][2] = 0 if not result[0][2] else sum(result[0][2]) / len(result[0][2])
            result[1][0] = 0 if not result[1][0] else sum(result[1][0]) / len(result[1][0])
            result[1][1] = 0 if not result[1][1] else sum(result[1][1]) / len(result[1][1])
            result[1][2] = 0 if not result[1][2] else sum(result[1][2]) / len(result[1][2])
            utils.logger.info(
                '{}'.format(value).ljust(10, ' ') + '{}  {}  {}'.format(result[0][0], result[0][1], result[0][2]))


@utils.register('环视-测加速度', 'KPI')
def get_accel_side(label_jsons, perce_jsons, file_name):
    '''测距效果获取'''
    ranges = ('0 ~ 20m', '20 ~ 35m', '35 ~ 60m')
    result_car = ([[], [], [], []], [[], [], [], []])
    result_truck = ([[], [], [], []], [[], [], [], []])
    result_bus = ([[], [], [], []], [[], [], [], []])
    result_ped = ([[], [], [], []], [[], [], [], []])
    result_bicycle = ([[], [], [], []], [[], [], [], []])
    result_motocycle = ([[], [], [], []], [[], [], [], []])
    result_tricycle = ([[], [], [], []], [[], [], [], []])
    result_other = ([[], [], [], []], [[], [], [], []])
    configs = Config.replay_configs()
    enum_obstacle_type = configs["enum_obstacle"]
    if not label_jsons:
        return
    if len(label_jsons) == 1:
        print('无可用测距标注数据')
        return
    for label_result, perce_result in utils.get_match_img_more_json(label_jsons, perce_jsons):
        if not label_result or not perce_result:
            continue
        for label_data, perce_data in utils.get_match_obstacle_more(label_result, perce_result):

            if not perce_data:
                continue
            if perce_data['obstacle_valid'] == 0:
                continue
            label_type = enum_obstacle_type[label_data['type']]
            label_accel_x = label_data['box_3d']["dists"]['z']
            label_accel_y = label_data['box_3d']["dists"]['x']
            perce_accel_x = perce_data["accel"]['obstacle_rel_acc_x_filter']
            perce_accel_y = perce_data["accel"]['obstacle_rel_acc_y_filter']
            accel_tolerance_x = perce_accel_x - label_accel_x
            accel_tolerance_y = perce_accel_y - label_accel_y

            try:
                result = eval('result_' + label_type)
            except:
                result = result_other
            if label_accel_x <= 20:
                result[0][0].append(accel_tolerance_x)
            if label_accel_x <= 35:
                result[0][1].append(accel_tolerance_x)
            if label_accel_x <= 60:
                result[0][2].append(accel_tolerance_x)

            if label_accel_y <= 20:
                result[1][0].append(accel_tolerance_y)
            if label_accel_y <= 35:
                result[1][1].append(accel_tolerance_y)
            if label_accel_y <= 60:
                result[1][2].append(accel_tolerance_y)

    utils.logger.info('type    0~20  20~35  35~60')
    for value in enum_obstacle_type.values():
        try:
            result = eval('result_' + value)
        except:
            value = 'other'
            result = result_other
        finally:
            result[0][0] = 0 if not result[0][0] else sum(result[0][0]) / len(result[0][0])
            result[0][1] = 0 if not result[0][1] else sum(result[0][1]) / len(result[0][1])
            result[0][2] = 0 if not result[0][2] else sum(result[0][2]) / len(result[0][2])
            result[1][0] = 0 if not result[1][0] else sum(result[1][0]) / len(result[1][0])
            result[1][1] = 0 if not result[1][1] else sum(result[1][1]) / len(result[1][1])
            result[1][2] = 0 if not result[1][2] else sum(result[1][2]) / len(result[1][2])
            utils.logger.info(
                '{}'.format(value).ljust(10, ' ') + '{}  {}  {}'.format(result[0][0], result[0][1], result[0][2]))


@utils.register('问题绘图对比', 'KPI')
def draw_problem_img(problem_jsons, raw_imgs, file_name):
    for problem_json in problem_jsons:
        problem_json_data = utils.get_json_data(problem_json)
        file_name = problem_json_data["filename"]
        copy_path = os.path.dirname(problem_json).replace('json-', 'img-') + '_img'
        if not os.path.exists(copy_path):
            os.makedirs(copy_path)
        for raw_img in raw_imgs:
            if not os.path.basename(raw_img).rsplit('.', 1)[0] == file_name.rsplit('.', 1)[0]:
                continue
            shutil.copy(raw_img, copy_path)
            new_path = os.path.join(copy_path, os.path.basename(raw_img)).encode('utf-8')
            utils.draw_plot(new_path, problem_json_data)


@utils.register('标注/感知数据绘图', 'KPI')
def draw_label_img(problem_jsons, raw_imgs, file_name):
    if len(problem_jsons) == 1:
        problem_json_datas = utils.get_json_data(problem_jsons[0])
        for problem_json_data in problem_json_datas:
            file_name = problem_json_data["filename"]
            copy_path = os.path.dirname(problem_jsons[0]).replace('json-', 'img-') + '_img'
            if not os.path.exists(copy_path):
                os.makedirs(copy_path)
            for raw_img in raw_imgs:
                if not os.path.basename(raw_img).rsplit('.', 1)[0] == file_name.rsplit('.', 1)[0]:
                    continue
                shutil.copy(raw_img, copy_path)
                new_path = os.path.join(copy_path, os.path.basename(raw_img)).encode('utf-8')
                utils.draw_plot(new_path, problem_json_data)

    elif len(problem_jsons) >= 1:
        for problem_json in problem_jsons:
            problem_json_data = utils.get_json_data(problem_json)
            file_name = os.path.basename(problem_json)
            copy_path = os.path.dirname(problem_json).replace('json-', 'img-') + '_img'
            if not os.path.exists(copy_path):
                os.makedirs(copy_path)
            for raw_img in raw_imgs:
                if not os.path.basename(raw_img).rsplit('.', 1)[0] == file_name.rsplit('.', 1)[0]:
                    continue
                shutil.copy(raw_img, copy_path)
                new_path = os.path.join(copy_path, os.path.basename(raw_img)).encode('utf-8')
                utils.draw_plot(new_path, problem_json_data)


@utils.register('S/M/L-recall', 'KPI')
def label_get_all_recall(label_jsons, perce_jsons, file_name):
    '''
    召回率获取
    '''
    if not label_jsons:
        return
    if len(label_jsons) > 1:
        print('召回率无可用标注数据')
        return
    configs = Config.replay_configs()
    enum_obstacle_type = configs["enum_obstacle"]
    ''' result_recall_demo = [label_num,true_num,false_num]'''
    result_small = [0, 0, 0]
    result_middle = [0, 0, 0]
    result_large = [0, 0, 0]
    result_other = [0, 0, 0]

    for label_result, perce_result in utils.get_match_img_one_json(label_jsons, perce_jsons):
        if not label_result or not perce_result:
            continue
        for label_data, perce_data in utils.get_match_obstacle_recall_side(label_result, perce_result):
            if not label_data:
                continue
            label_type = label_data['tags']["class"]
            if not perce_data:
                perce_type = None
            else:
                perce_type = enum_obstacle_type[perce_data["obstacle_type"]]
            area = label_data['tags']['height'] * label_data['tags']['width'] / 9
            if label_type == 'wheel':
                result = result_other
            elif area < 1024:
                result = result_small
            elif area < 9216:
                result = result_middle
            else:
                result = result_large
            result[0] += 1
            if perce_type and perce_type == label_type:
                result[1] += 1
            elif perce_type:
                result[2] += 1
    print('-*-' * 50)
    for key, value in {'small': result_small, 'middle': result_middle, 'large': result_large,
                       'wheel': result_other}.items():
        obstacle_recall = 0 if value[0] == 0 else float(value[1] + value[2]) / value[0]
        utils.logger.info('{}'.format(key).ljust(10, ' ') + '{}  recall: {}'.format(value, obstacle_recall))


@utils.register('S/M/L-precision', 'KPI')
def label_get_all_precision(label_jsons, perce_jsons, file_name):
    '''
    所有精确率获取
    环视、前视相机不同时修改enum_obstacle_type即可
    '''
    if not label_jsons:
        return
    if len(label_jsons) > 1:
        print('精确率无可用标注数据')
        return
    configs = Config.replay_configs()
    enum_obstacle_type = configs["enum_obstacle"]
    '''result_recall_demo = [label_num,TP,FP]'''
    result_small = [0, 0, 0]
    result_middle = [0, 0, 0]
    result_large = [0, 0, 0]

    for label_result, perce_result in utils.get_match_img_one_json(label_jsons, perce_jsons):
        if not perce_result:
            continue
        for label_data, perce_data in utils.get_match_obstacle_precision_side(label_result, perce_result):
            if not perce_data:
                continue
            else:
                perce_type = enum_obstacle_type[perce_data["obstacle_type"]]
            if label_data:
                label_type = label_data['tags']["class"]
            else:
                label_type = None
            area = perce_data["uv_bbox2d"]["obstacle_bbox.width"] * perce_data["uv_bbox2d"]["obstacle_bbox.height"]
            if area < 1024:
                result = result_small
            elif area < 9216:
                result = result_middle
            else:
                result = result_large
            if perce_type == label_type:
                result[1] += 1
            else:
                result[2] += 1
    print('-*-' * 50)
    for key, value in {'small': result_small, 'middle': result_middle, 'large': result_large}.items():
        obstacle_precision = 0 if value[1] + value[2] == 0 else float(value[1]) / (value[2] + value[1])
        utils.logger.info('{}'.format(key).ljust(10, ' ') + '{}  precision: {}'.format(value, obstacle_precision))


@utils.register('漏检问题筛选', 'KPI')
def get_problems_lost(label_jsons, perce_jsons, file_name):
    if not perce_jsons or not perce_jsons[0].endswith('.json'):
        return
    perce_jsons = sorted(perce_jsons, key=lambda x: x.rsplit('_', 1)[-1].split('.')[0].zfill(6))
    perce_jsons = sorted(perce_jsons, key=lambda x: x.rsplit('_', 1)[0])
    data, data_problem = [], {}
    for temp in tqdm.tqdm(perce_jsons):
        perce_data = utils.get_json_data(temp)
        if perce_data:
            tracks = perce_data['tracks']
            new = {'-image': temp}
            if tracks:
                for idx in tracks.keys():
                    new[str(idx)] = 1
            data.append(new)
    df = pd.DataFrame(data)

    for column in tqdm.tqdm(df.columns[1:]):
        df_column = df.iloc[:, df.columns.get_loc(column)]
        df_column = df_column[df_column.values == 1]
        last_idx = 0
        for idx in df_column.index:
            if last_idx != 0 and 10 >= (idx - last_idx) >= 2:
                image_name = df.iloc[idx, df.columns.get_loc('-image')]
                if data_problem.get(image_name):
                    data_problem[image_name].append(column)
                else:
                    data_problem[image_name] = [column]
            last_idx = idx

    for key, value in data_problem.items():
        img_data = utils.get_json_data(key)["tracks"]
        values = copy.deepcopy(value)
        for temp in values:
            pre_data = img_data[temp]
            if pre_data["uv_bbox2d"]["obstacle_bbox.height"] * pre_data["uv_bbox2d"]["obstacle_bbox.width"] < 9600:
                value.remove(temp)
    problem_json_data = [(x, y, '漏检问题') for x, y in data_problem.items() if y]
    problem_json_data.sort(key=lambda x: x[0].rsplit('/', 1)[-1].rsplit('.')[0].rsplit('_')[-1].zfill(6))
    problem_json_data.sort(key=lambda x: x[0].rsplit('/', 1)[0])
    df_problems = pd.DataFrame(problem_json_data, columns=['image', 'obstacle_id', 'Problem'])
    if os.path.exists(file_name):
        df_problems = pd.concat([pd.read_excel(file_name), df_problems])
    df_problems.to_excel(file_name, index=False, engine='openpyxl')
    print('数据处理完毕')


@utils.register('误检问题筛选', 'KPI')
def get_problems_err(label_jsons, perce_jsons, file_name):
    if not perce_jsons or not perce_jsons[0].endswith('.json'):
        return
    perce_jsons = sorted(perce_jsons, key=lambda x: x.rsplit('_', 1)[-1].split('.')[0].zfill(6))
    perce_jsons = sorted(perce_jsons, key=lambda x: x.rsplit('_', 1)[0])
    data, data_problem = [], {}
    for temp in tqdm.tqdm(perce_jsons):
        perce_data = utils.get_json_data(temp)
        if perce_data:
            tracks = perce_data['tracks']
            new = {'-image': temp}
            if tracks:
                for idx in tracks.keys():
                    new[str(idx)] = 1
            data.append(new)

    df = pd.DataFrame(data)

    for column in tqdm.tqdm(df.columns[1:]):
        df_column = df.iloc[:, df.columns.get_loc(column)]
        df_column = df_column[df_column.values != 1]
        last_idx = 0
        for idx in df_column.index:
            if last_idx != 0 and 10 >= (idx - last_idx) >= 2:
                image_name = df.iloc[idx - 1, df.columns.get_loc('-image')]
                if data_problem.get(image_name):
                    data_problem[image_name].append(column)
                else:
                    data_problem[image_name] = [column]
            last_idx = idx

    for key, value in data_problem.items():
        img_data = utils.get_json_data(key)["tracks"]
        values = copy.deepcopy(value)
        for temp in values:
            pre_data = img_data[temp]
            if pre_data["uv_bbox2d"]["obstacle_bbox.height"] * pre_data["uv_bbox2d"]["obstacle_bbox.width"] < 9600:
                value.remove(temp)
    problem_json_data = [(x, y, '误检问题') for x, y in data_problem.items() if y]
    problem_json_data.sort(key=lambda x: x[0].rsplit('/', 1)[-1].rsplit('.')[0].rsplit('_')[-1].zfill(6))
    problem_json_data.sort(key=lambda x: x[0].rsplit('/', 1)[0])
    df_problems = pd.DataFrame(problem_json_data, columns=['image', 'obstacle_id', 'Problem'])
    if os.path.exists(file_name):
        df_problems = pd.concat([pd.read_excel(file_name), df_problems])
    df_problems.to_excel(file_name, index=False, engine='openpyxl')
    print('数据处理完毕')


@utils.register('环视-mAP', 'KPI')
def mAP(label_jsons, perce_jsons, file_name):
    cfgs = Config()
    cfgs = cfgs.evalcfgs
    configs = Config.replay_configs()
    enum_obstacle_type = configs["enum_obstacle"]
    gts = []
    dets = []
    stats = dict()
    imgids = []
    if not label_jsons:
        return
    if len(label_jsons) > 1:
        print('无可用标注数据')
        return
    for label_result, perce_result in utils.get_match_img_one_json(label_jsons, perce_jsons):
        if not label_result or not perce_result:
            continue
        idx = 1
        mark = False
        label_name = label_result["filename"].split('.')[0]
        for label_data, perce_data in utils.get_match_obstacle_recall_side(label_result, perce_result):
            if label_data is not None:
                annid = md5((label_name + str(idx)).encode('utf-8')).hexdigest()
                gt = [label_name, label_data['tags']['class'],
                      label_data['tags']['x'] + label_data['tags']['width'] / 2,
                      label_data['tags']['y'] + label_data['tags']['height'] / 2., label_data['tags']['width'],
                      label_data['tags']['height'],
                      annid, idx]
                gts.append(gt)
                mark = True
            if perce_data is not None:
                annid = md5((label_name + str(idx)).encode('utf-8')).hexdigest()
                score = perce_data['obstacle_exist_prob'] * perce_data['obstacle_type_confidence']
                det = [label_name, enum_obstacle_type[perce_data['obstacle_type']],
                       perce_data['uv_bbox2d']['obstacle_bbox.x'] + perce_data['uv_bbox2d']['obstacle_bbox.width'] / 2.,
                       perce_data['uv_bbox2d']['obstacle_bbox.y'] + perce_data['uv_bbox2d'][
                           'obstacle_bbox.height'] / 2.,
                       perce_data['uv_bbox2d']['obstacle_bbox.width'], perce_data['uv_bbox2d']['obstacle_bbox.height'],
                       score, perce_data['obstacle_id'], annid, idx]
                dets.append(det)
                mark = True
            idx += 1
        if mark:
            imgids.append(label_name)
    # del label_jsons, perce_jsons
    columns_gts = ['imgname', 'catenm', 'cx', 'cy', 'w', 'h', 'annid', 'id']
    columns_dets = ['imgname', 'catenm', 'cx', 'cy', 'w', 'h', 'score', 'track_id', 'annid', 'id']
    gts = pd.DataFrame(gts, columns=columns_gts)
    dets = pd.DataFrame(dets, columns=columns_dets)
    # modify gt_labels
    gts['cx'] = gts['cx'] / 3.
    gts['cy'] = gts['cy'] / 3. + 12
    gts['w'] = gts['w'] / 3.
    gts['h'] = gts['h'] / 3.
    gts['area'] = gts['w'] * gts['h']
    dets['area'] = dets['w'] * dets['h']
    dets_gts = pd.merge(dets[['imgname', 'catenm', 'cx', 'cy', 'w', 'h', 'score', 'track_id', 'annid', 'id', 'area']],
                        gts[['imgname', 'catenm', 'cx', 'cy', 'w', 'h', 'annid', 'id', 'area']], on=['imgname'],
                        how='outer', suffixes=['_det', '_gt'])
    dets_gts['ios_gt'], dets_gts['ios_det'], dets_gts['iou'] = compute_IoU_IoS(dets_gts)
    # False detection
    false_det = dets_gts.groupby('annid_det')['ios_det'].max()
    false_det = false_det[false_det < cfgs['fn_ios_thre']].index
    false_det = dets[dets['annid'].isin(false_det)]
    stats['false_det'] = false_det.groupby('catenm')['annid'].count()
    # Missed gt
    missed_gt = dets_gts.groupby('annid_gt')['ios_gt'].max()
    missed_gt = missed_gt[missed_gt < cfgs['fp_ios_thre']].index
    missed_gt = gts[gts['annid'].isin(missed_gt)]
    stats['missed_gt'] = missed_gt.groupby('catenm')['annid'].count()
    # set cate_miscls flag
    cate_miscls = dets_gts[dets_gts['catenm_gt'] != dets_gts['catenm_det']].groupby('annid_gt', as_index=False)[
        'iou'].max()
    cate_miscls = cate_miscls[cate_miscls['iou'] > cfgs['cate_miscls_iou_thre']]
    cate_miscls = pd.merge(cate_miscls, dets_gts, on=['annid_gt', 'iou'], how='left')
    stats['cate_miscls'] = cate_miscls.groupby('catenm_gt')['annid_gt'].count()
    # evaluate
    ious = dets_gts.loc[
        dets_gts['catenm_gt'] == dets_gts['catenm_det'], ['imgname', 'catenm_gt', 'annid_det', 'annid_gt', 'id_det',
                                                          'id_gt', 'iou', 'area_gt', 'score']]
    del dets_gts

    c_gts = defaultdict(list)
    for name, gts_group in gts.groupby(['imgname', 'catenm']):
        anns = []
        for ind, gt in gts_group.iterrows():
            ann = {}
            ann['annid'] = gt.annid
            ann['id'] = gt.id
            ann['bbox'] = [gt.cx, gt.cy, gt.w, gt.h]
            ann['area'] = gt.area
            ann['ignore'] = 0
            anns.append(ann)
        c_gts[name] = anns

    c_dets = defaultdict(list)
    for name, dets_group in dets.groupby(['imgname', 'catenm']):
        anns = []
        for ind, det in dets_group.iterrows():
            ann = {}
            ann['annid'] = det.annid
            ann['id'] = det.id
            ann['bbox'] = [det.cx, det.cy, det.w, det.h]
            ann['area'] = det.area
            ann['score'] = det.score
            anns.append(ann)
        c_dets[name] = anns
    c_ious = defaultdict(list)
    ious[['id_gt', 'id_det']] = ious[['id_gt', 'id_det']].astype(int)
    for name, ious_group in ious.groupby(['imgname', 'catenm_gt']):
        ious_group.set_index(['id_det', 'id_gt'], inplace=True)
        c_ious[name] = ious_group['iou'].to_dict()
    # evaluate per image
    max_det = cfgs['max_dets'][-1]
    eval_imgs_res = [evaluate_img(c_gts, c_dets, c_ious, cfgs, imgid, catenm, area_range, max_det)
                     for catenm in cfgs['catenms']
                     for area_range in cfgs['area_ranges']
                     for imgid in imgids
                     ]

    c_eval = accumulate(cfgs, imgids, eval_imgs_res)
    eval_stats = summarize(cfgs, c_eval)
    to_excel(gts, stats, imgids, cfgs, eval_stats)


@utils.register('框-稳定性', 'KPI')
def stability(label_jsons, perce_jsons, file_name):
    def get_frame_id(x):
        name = os.path.basename(x)
        return int(name.split('.')[0].split('_')[-1])

    def analyse_info(x):

        w = x['w'].values
        h = x['h'].values
        length = len(w)
        smooth_w = SampEn(w)
        smooth_h = SampEn(h)
        track_id = x.iloc[0, 1]
        columns = ['track_id', 'smooth_w', 'smooth_h', 'length']
        res = [[track_id, smooth_w, smooth_h, length]]
        return pd.DataFrame(res, columns=columns)

    dets = []
    perce_jsons = sorted([perce_json for perce_json in perce_jsons], key=get_frame_id)
    for i in range(len(perce_jsons)):
        perce_json1 = perce_jsons[i]
        with open(perce_json1, 'r') as f:
            jsdicts1 = json.load(f)
        jsdicts1 = jsdicts1['tracks']
        if type(jsdicts1) == type(None):
            continue
        for _, v in jsdicts1.items():
            score = v['obstacle_exist_prob'] * v['obstacle_type_confidence']
            obj = [i, v['obstacle_id'], v['uv_bbox2d']['obstacle_bbox.x'], v['uv_bbox2d']['obstacle_bbox.y'],
                   v['uv_bbox2d']['obstacle_bbox.width'], v['uv_bbox2d']['obstacle_bbox.height'], score,
                   v['obstacle_type']]

            dets.append(obj)

    columns = ['idx', 'track_id', 'cx', 'cy', 'w', 'h', 'score', 'type']
    dets = pd.DataFrame(dets, columns=columns)
    dets['area'] = dets['w'] * dets['h']
    print('analysis....')
    res = dets.groupby('track_id', as_index=False).apply(analyse_info)
    print('saving results to ./test_result/jiao/stability/stability.xlsx')
    res.to_excel('./test_result/jiao/stability/stability.xlsx')


@utils.register('Range-稳定性', 'KPI')
def stabilit_range(label_jsons, perce_jsons, file_name):
    def get_frame_id(x):
        name = os.path.basename(x)
        return int(name.split('.')[0].split('_')[-1])

    def analyse_info(x):

        w = x['dx'].values
        h = x['dy'].values
        length = len(w)
        smooth_w = SampEn(w)
        smooth_h = SampEn(h)
        track_id = x.iloc[0, 1]
        columns = ['track_id', 'smooth_dx', 'smooth_dy', 'length']
        res = [[track_id, smooth_w, smooth_h, length]]
        return pd.DataFrame(res, columns=columns)

    dets = []
    perce_jsons = sorted([perce_json for perce_json in perce_jsons], key=get_frame_id)
    for i in range(len(perce_jsons)):
        perce_json1 = perce_jsons[i]
        with open(perce_json1, 'r') as f:
            jsdicts1 = json.load(f)
        jsdicts1 = jsdicts1['tracks']
        if type(jsdicts1) == type(None):
            continue
        for k, v in jsdicts1.items():
            score = v['obstacle_exist_prob'] * v['obstacle_type_confidence']
            obj = [i, k, v["position"]["obstacle_pos_x_filter"], v["position"]["obstacle_pos_z_filter"], score]
            dets.append(obj)

    columns = ['idx', 'track_id', 'dx', 'dy', 'score']
    dets = pd.DataFrame(dets, columns=columns)
    print('analysis....')
    res = dets.groupby('track_id', as_index=False).apply(analyse_info)
    print('saving results to ./test_result/jiao/stability/stability_range.xlsx')
    res.to_excel('./test_result/jiao/stability/stability_range.xlsx')


@utils.register('Range-统计', 'KPI')
def statistic_range(label_jsons, perce_jsons, file_name):
    cfgs = Config()
    cfgs = cfgs.evalcfgs
    ranges = ['0~10m', '10~20m', '20~30m', '30~40m', '40~50m', '50~60m',
              '60~70m', '70~80m', '80~90m', '90~100m', '100~110m', '110~120m']
    catename = cfgs['catename'][:-1] + ['all']
    det = []
    for i in range(len(perce_jsons)):
        perce_json = perce_jsons[i]
        with open(perce_json, 'r') as f:
            jsdicts = json.load(f)
        jsdicts = jsdicts['tracks']
        for k, v in jsdicts.items():
            cate = v['obstacle_type']
            dx = v["position"]["obstacle_pos_x_filter"]
            mark = int(dx / 10)
            if mark >= 12:
                continue
            det.append[i, ranges[mark], cate, dx]
    columns = ['idx', 'range', 'cate', 'dx']
    det = pd.DataFrame(det, columns=columns)
    new_data = det.groupby(['cate', 'range'], as_index=False).agg(['mean', 'std', 'count'])
    print(new_data)
    new_data.to_excel('./test_result/jiao/statistic_range.xlsx')


@utils.register('tracking', 'KPI')
def get_problem_track(label_jsons, perce_jsons, file_name):
    pass
    if not perce_jsons:
        return
    perce_jsons = sorted(perce_jsons, key=lambda x: x.rsplit('_', 1)[-1].split('.')[0].zfill(6))
    perce_jsons = sorted(perce_jsons, key=lambda x: x.rsplit('_', 1)[0])
    df = pd.DataFrame(columns=['image'], index=None)
    problem_list = []
    problem_result_list = []
    num = df.shape[0]
    for temp in perce_jsons:
        num += 1
        perce_data = utils.get_json_data(temp)
        tracks = perce_data['tracks']
        df.loc[num, 'image'] = temp
        if not tracks:
            continue
        for id in tracks.keys():
            df.loc[num, id] = 1
    # for column in df.columns[1:]:
    #     result = df.loc[:, column]
    #     last_state = -1
    #     start_num = 1
    #     for i, j in enumerate(result):
    #         if str(j) != str(last_state):
    #             problem_img = df.loc[i + 1, 'image']
    #             # if (i + 1) - start_num < 10 and i != 0 and i > 10 and problem_img not in problem_list:
    #             if (i + 1) - start_num < 10 and i != 0 and i > 10 and problem_img not in problem_list and j != 1:
    #                 problem_list.append(problem_img)
    #                 problem_result_list.append((problem_img, column))
    #             last_state = j
    #             start_num = i + 1
    # problem_result_list.sort(key=lambda x: x[0].split('_')[-1].zfill(12))
    # problem_filter_result = []
    # for temp in problem_result_list:
    #     img_data = utils.get_json_data(temp[0])["tracks"][temp[1]]
    #     if img_data["uv_bbox2d"]["obstacle_bbox.height"] * img_data["uv_bbox2d"]["obstacle_bbox.width"] > 960:
    #         problem_filter_result.append(temp)
    # filename = os.path.dirname(os.path.dirname(__file__)) + '/data/' + datetime.now().strftime(
    #     "%Y_%m_%d_") + 'perce_problem' + '.json'
    # if os.path.exists(filename):
    #     os.remove(filename)
    # with open(filename, 'a') as f:
    #     json.dump(problem_filter_result, f, indent=4)


# @utils.register('前视-CIPV', 'KPI')
# def get_cipv_front(label_jsons, perce_jsons, file_name):
#     '''
#       CIPV目标漏检场景筛选
#       '''
# old_cipv_id = None
# last_cipv_id = None
# last_time = 0
# for perce_data ,t in for datum in data:
#     new_cipv_id = perce_data.cipv_id
#     tracks = perce_data.tracks
#     now_time = t.to_sec()
#     if old_cipv_id != new_cipv_id:
#         if (now_time - last_time) <= 1 and last_cipv_id == new_cipv_id and (
#                 new_cipv_id not in old_id_list) and new_cipv_id != 0:
#             for i in range(len(tracks)):
#                 if tracks[i].id == new_cipv_id:
#                     cipv_x = tracks[i].position.x
#                     data = pd.read_excel(file_name)
#                     data_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t.to_sec()))
#                     num = data.shape[0]
#                     data.loc[num, 'NO'] = num + 1
#                     data.loc[num, 'Date'] = data_time.split(' ')[0]
#                     data.loc[num, 'BagPath'] = bag_path
#                     data.loc[num, 'Time'] = data_time.split(' ')[1]
#                     data.loc[num, 'Problem'] = '检测目标漏检'
#                     data.loc[num, 'Obstracel_X'] = cipv_x
#                     data.to_excel(file_name, index=False, engine='openpyxl')
#                     break
#         last_cipv_id = old_cipv_id
#         old_cipv_id = new_cipv_id
#         last_time = now_time
#     tracks_id_list = []
#     if len(tracks) > 0:
#         [tracks_id_list.append(tracks[i].id) for i in range(len(tracks))]
#     old_id_list = tracks_id_list