# -*- coding: utf-8 -*-
import os
import time

import pandas as pd

import utils


def get_perception_problem(bag_path, func_list):
    file_name = utils.BASIC_NAME + "perception" + '.xlsx'
    if not os.path.exists(file_name):
        df = pd.DataFrame(columns=['NO', 'Date', 'Time', 'Problem'], index=None)
        df.to_excel(file_name, index=False, engine='openpyxl')
    for func in func_list:
        eval(func)(bag_path, file_name)


@utils.register('类别错检', 'perception')
def cipv_front_error(file_path, file_name):
    '''
    目标类型跳变场景筛选
    '''
    topic_list = ['/planning/vehicle_monitor']
    old_obstacle_in_path_id = None
    old_obstacle_in_path_type = None
    last_time = 0
    for topic, msg, t, bag_path, bag_count in utils.get_bag_msg(file_path, topic_list):
        if topic == '/planning/vehicle_monitor':
            new_obstacle_in_path_id = msg.obstacle_state.obstacle_in_path.id
            new_obstacle_in_path_type = msg.obstacle_state.obstacle_in_path.type
            obstacel_in_path_x = msg.obstacle_state.obstacle_in_path.position.x
            if old_obstacle_in_path_id != new_obstacle_in_path_id and old_obstacle_in_path_type != new_obstacle_in_path_type:
                old_obstacle_in_path_id = new_obstacle_in_path_id
                old_obstacle_in_path_type = new_obstacle_in_path_type
            if old_obstacle_in_path_id == new_obstacle_in_path_id and old_obstacle_in_path_type != new_obstacle_in_path_type:
                if new_obstacle_in_path_type == 0:
                    continue
                old_obstacle_in_path_type = new_obstacle_in_path_type
                now_time = t.to_sec()
                if now_time - last_time < 1.5 or obstacel_in_path_x > 80:
                    continue
                last_time = now_time
                data = pd.read_excel(file_name)
                data_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t.to_sec()))
                num = data.shape[0]
                data.loc[num, 'NO'] = num + 1
                data.loc[num, 'Date'] = data_time.split(' ')[0]
                data.loc[num, 'Time'] = data_time.split(' ')[1]
                data.loc[num, 'BagPath'] = bag_path
                data.loc[num, 'Problem'] = '检测类别跳变'
                data.loc[num, 'Obstracel_X'] = obstacel_in_path_x
                data.to_excel(file_name, index=False, engine='openpyxl')


@utils.register('目标漏检', 'perception')
def cipv_front_lost(file_path, file_name):
    '''
    目标漏检场景筛选
    '''
    topic_list = ['/input/perception/obstacle_list', '/perception/obstacle_list']
    old_cipv_id = None
    last_cipv_id = None
    last_time = 0
    last_problem_time = 0
    for topic, msg, t, bag_path, bag_count in utils.get_bag_msg(file_path, topic_list):
        if topic == '/input/perception/obstacle_list' or topic == '/perception/obstacle_list':
            new_cipv_id = msg.cipv_id
            tracks = msg.tracks
            now_time = t.to_sec()
            if old_cipv_id != new_cipv_id:
                if (now_time - last_time) <= 1 and last_cipv_id == new_cipv_id and (
                        new_cipv_id not in old_id_list) and new_cipv_id != 0 and (now_time - last_problem_time) > 2:
                    for i in range(len(tracks)):
                        if tracks[i].id == new_cipv_id:
                            last_problem_time = now_time
                            cipv_x = tracks[i].position.x
                            data = pd.read_excel(file_name)
                            data_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t.to_sec()))
                            num = data.shape[0]
                            data.loc[num, 'NO'] = num + 1
                            data.loc[num, 'Date'] = data_time.split(' ')[0]
                            data.loc[num, 'BagPath'] = bag_path
                            data.loc[num, 'Time'] = data_time.split(' ')[1]
                            data.loc[num, 'Problem'] = '检测目标漏检'
                            data.loc[num, 'Obstracel_X'] = cipv_x
                            data.to_excel(file_name, index=False, engine='openpyxl')
                            break
                last_cipv_id = old_cipv_id
                old_cipv_id = new_cipv_id
                last_time = now_time
            tracks_id_list = []
            if len(tracks) > 0:
                [tracks_id_list.append(tracks[i].id) for i in range(len(tracks))]
            old_id_list = tracks_id_list


@utils.register('测距误差统计', 'perception')
def cipv_distance_front(file_path, file_name):
    CIPV_DISTANCE_TOLERANCE = {'result': {20: [], 40: [], 60: [], 80: [], 100: [], 120: [], 200: []}}
    topic_list = ['/fusion/radar_process/processed_radar_tracks',
                  '/fusion/tracked_obstacles', '/input/perception/obstacle_list', '/perception/obstacle_list']
    cipv_id = 0
    radar_distance = None
    for topic, msg, t, bag_path, bag_count in utils.get_bag_msg(file_path, topic_list):
        if topic == '/input/perception/obstacle_list' or topic == '/perception/obstacle_list':
            cipv_id = msg.cipv_id
            perception_tracks = msg.tracks
            for i in range(len(perception_tracks)):
                if perception_tracks[i].id == cipv_id:
                    perception_distance = perception_tracks[i].position.x
        if topic == '/fusion/radar_process/processed_radar_tracks':
            radar_tracks = msg.tracks
            if radar_tracks:
                radar_distance = {}
                for i in range(len(radar_tracks)):
                    radar_distance[radar_tracks[i].id] = radar_tracks[i].position.x
        if topic == '/fusion/tracked_obstacles':
            fusion_tracks = msg.tracks
            if fusion_tracks and cipv_id != 0 and radar_distance:
                for i in range(len(fusion_tracks)):
                    if cipv_id == fusion_tracks[i].associate_infos[0].id:
                        try:
                            cipv_radar_distance = radar_distance[
                                fusion_tracks[i].associate_infos[1].id]
                            gaper = (cipv_radar_distance - perception_distance - 2.07) / (
                                    cipv_radar_distance - 2.07)
                            print(gaper, cipv_radar_distance - 2.07, perception_distance)
                            if cipv_radar_distance - 2.07 < 20:
                                CIPV_DISTANCE_TOLERANCE['result'][20].append(abs(gaper))
                            elif cipv_radar_distance - 2.07 < 40:
                                CIPV_DISTANCE_TOLERANCE['result'][40].append(abs(gaper))
                            elif cipv_radar_distance - 2.07 < 60:
                                CIPV_DISTANCE_TOLERANCE['result'][60].append(abs(gaper))
                            elif cipv_radar_distance - 2.07 < 80:
                                CIPV_DISTANCE_TOLERANCE['result'][80].append(abs(gaper))
                            elif cipv_radar_distance - 2.07 < 100:
                                CIPV_DISTANCE_TOLERANCE['result'][100].append(abs(gaper))
                            elif cipv_radar_distance - 2.07 < 120:
                                CIPV_DISTANCE_TOLERANCE['result'][120].append(abs(gaper))
                            else:
                                CIPV_DISTANCE_TOLERANCE['result'][200].append(abs(gaper))
                        except:
                            continue
    try:
        print('20:{}'.format(sum(CIPV_DISTANCE_TOLERANCE['result'][20]) / len(CIPV_DISTANCE_TOLERANCE['result'][20])))
        print('40:{}'.format(sum(CIPV_DISTANCE_TOLERANCE['result'][40]) / len(CIPV_DISTANCE_TOLERANCE['result'][40])))
        print('60:{}'.format(sum(CIPV_DISTANCE_TOLERANCE['result'][60]) / len(CIPV_DISTANCE_TOLERANCE['result'][60])))
        print('80:{}'.format(sum(CIPV_DISTANCE_TOLERANCE['result'][80]) / len(CIPV_DISTANCE_TOLERANCE['result'][80])))
        print(
            '100:{}'.format(sum(CIPV_DISTANCE_TOLERANCE['result'][100]) / len(CIPV_DISTANCE_TOLERANCE['result'][100])))
        print(
            '120:{}'.format(sum(CIPV_DISTANCE_TOLERANCE['result'][120]) / len(CIPV_DISTANCE_TOLERANCE['result'][120])))
        print(
            '200:{}'.format(sum(CIPV_DISTANCE_TOLERANCE['result'][200]) / len(CIPV_DISTANCE_TOLERANCE['result'][200])))
    except:
        pass


@utils.register('测速误差统计', 'perception')
def cipv_velocity(file_path, file_name):
    CIPV_VELOCITY_TOLERANCE = {'result': {20: [], 40: [], 60: [], 80: [], 100: [], 120: [], 200: []}}
    topic_list = ['/fusion/radar_process/processed_radar_tracks',
                  '/fusion/tracked_obstacles', '/input/perception/obstacle_list', '/perception/obstacle_list']
    radar_velocity = None
    cipv_id = 0
    for topic, msg, t, bag_path, bag_count in utils.get_bag_msg(file_path, topic_list):
        if topic == '/input/perception/obstacle_list' or topic == '/perception/obstacle_list':
            cipv_id = msg.cipv_id
            perception_tracks = msg.tracks
            for i in range(len(perception_tracks)):
                if perception_tracks[i].id == cipv_id:
                    perce_velocity = perception_tracks[i].velocity.x
        if topic == '/fusion/radar_process/processed_radar_tracks':
            radar_tracks = msg.tracks
            if radar_tracks:
                radar_velocity = {}
                radar_distance = {}
                for i in range(len(radar_tracks)):
                    radar_velocity[radar_tracks[i].id] = radar_tracks[i].velocity.x
                    radar_distance[radar_tracks[i].id] = radar_tracks[i].position.x
        if topic == '/fusion/tracked_obstacles':
            fusion_tracks = msg.tracks
            if fusion_tracks and cipv_id != 0 and radar_velocity:
                for i in range(len(fusion_tracks)):
                    if cipv_id == fusion_tracks[i].associate_infos[0].id:

                        try:
                            cipv_radar_velocity = radar_velocity[
                                fusion_tracks[i].associate_infos[1].id]
                            cipv_radar_distance = radar_distance[
                                fusion_tracks[i].associate_infos[1].id]
                            gaper = (cipv_radar_velocity - perce_velocity)
                            if cipv_radar_distance - 2.07 < 20:
                                CIPV_VELOCITY_TOLERANCE['result'][20].append(abs(gaper))
                            elif cipv_radar_distance - 2.07 < 40:
                                CIPV_VELOCITY_TOLERANCE['result'][40].append(abs(gaper))
                            elif cipv_radar_distance - 2.07 < 60:
                                CIPV_VELOCITY_TOLERANCE['result'][60].append(abs(gaper))
                            elif cipv_radar_distance - 2.07 < 80:
                                CIPV_VELOCITY_TOLERANCE['result'][80].append(abs(gaper))
                            elif cipv_radar_distance - 2.07 < 100:
                                CIPV_VELOCITY_TOLERANCE['result'][100].append(abs(gaper))
                            elif cipv_radar_distance - 2.07 < 120:
                                CIPV_VELOCITY_TOLERANCE['result'][120].append(abs(gaper))
                            else:
                                CIPV_VELOCITY_TOLERANCE['result'][200].append(abs(gaper))
                        except:
                            continue
    try:
        print('20:{}'.format(sum(CIPV_VELOCITY_TOLERANCE['result'][20]) / len(CIPV_VELOCITY_TOLERANCE['result'][20])))
        print('40:{}'.format(sum(CIPV_VELOCITY_TOLERANCE['result'][40]) / len(CIPV_VELOCITY_TOLERANCE['result'][40])))
        print('60:{}'.format(sum(CIPV_VELOCITY_TOLERANCE['result'][60]) / len(CIPV_VELOCITY_TOLERANCE['result'][60])))
        print('80:{}'.format(sum(CIPV_VELOCITY_TOLERANCE['result'][80]) / len(CIPV_VELOCITY_TOLERANCE['result'][80])))
        print(
            '100:{}'.format(sum(CIPV_VELOCITY_TOLERANCE['result'][100]) / len(CIPV_VELOCITY_TOLERANCE['result'][100])))
        print(
            '120:{}'.format(sum(CIPV_VELOCITY_TOLERANCE['result'][120]) / len(CIPV_VELOCITY_TOLERANCE['result'][120])))
        print(
            '200:{}'.format(sum(CIPV_VELOCITY_TOLERANCE['result'][200]) / len(CIPV_VELOCITY_TOLERANCE['result'][200])))
    except:
        pass


@utils.register('tracking问题', 'perception')
def get_tracking_problems(file_path, file_name):
    last_tracks = []
    topic_list = ['/input/perception/obstacle_list', '/perception/obstacle_list']
    for topic, msg, t, bag_path, bag_count in utils.get_bag_msg(file_path, topic_list):
        if topic == '/input/perception/obstacle_list' or topic == '/perception/obstacle_list':
            tracks = msg.tracks
            now_time = t.to_sec()
            if len(tracks) == len(last_tracks):
                tracks_id = [x.id for x in tracks]
                for temp in last_tracks:
                    if temp.id not in tracks_id:
                        area = temp.uv_bbox2d.size.x * temp.uv_bbox2d.size.y
                        distance_x = temp.position_std.x
                        distance_y = temp.position_std.y
                        if area > 9216 and distance_x < 80 and abs(distance_y) < 10:
                            data = pd.read_excel(file_name)
                            data_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t.to_sec()))
                            num = data.shape[0]
                            data.loc[num, 'NO'] = num + 1
                            data.loc[num, 'Date'] = data_time.split(' ')[0]
                            data.loc[num, 'BagPath'] = bag_path
                            data.loc[num, 'Time'] = data_time.split(' ')[1]
                            data.loc[num, 'Problem'] = 'tracking有误'
                            data.loc[num, 'ID'] = temp.id
                            data.loc[num, 'Obstracel_X'] = distance_x
                            data.to_excel(file_name, index=False, engine='openpyxl')
            last_tracks = tracks
