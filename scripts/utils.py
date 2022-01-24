# -*- coding: utf-8 -*-
import copy
import logging
import os
import json

from datetime import datetime
import cv2
import rosbag
import pandas as pd

from config.cfg import Config

FUNCTION_SET = {}
BASIC_NAME = os.path.dirname(os.path.dirname(__file__)) + '/data/' + datetime.now().strftime("%Y_%m_%d_")


def init_logger():
    '''
    配置日志记录
    '''
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler()
    log_filename = os.path.dirname(os.path.dirname(__file__)) + "/log/" + datetime.now().strftime(
        "%Y_%m_%d_%H_%M_%S") + ".log"
    fh = logging.FileHandler(log_filename, mode='w')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(stream_handler)
    return logger


def write_to_excel(df, file_name, sheet_name):
    print('-·-' * 30)
    print(df)
    writer = pd.ExcelWriter(file_name)
    if os.path.exists(file_name):
        raw_df = pd.read_excel(file_name, sheet_name=None, encoding='utf-8')
        for sheet, data in raw_df.items():
            if sheet == sheet_name:
                df = pd.concat([data, df], sort=False)
            else:
                data.to_excel(excel_writer=writer, sheet_name=sheet, index=False, engine='openpyxl')
    df.to_excel(excel_writer=writer, sheet_name=sheet_name, index=False, engine='openpyxl')
    writer.save()


def get_all_files(path, file_extension):
    """
    获取所有后缀为file_extension的文件
    """
    files = []
    list_dir = os.listdir(path)
    for each in list_dir:
        each_path = os.path.join(path, each)
        if os.path.isdir(each_path):
            files.extend(get_all_files(each_path, file_extension))
        if os.path.isfile(each_path) and each_path.endswith(file_extension):
            files.append(each_path)
    return files


def get_bag_msg(file_path, topic_list):
    bags = get_all_files(file_path, '.bag')
    bags.sort(reverse=False)
    bag_count = 0
    for bag_path in bags:
        logger.info('开始处理：{}'.format(os.path.basename(bag_path)))
        try:
            bag_data = rosbag.Bag(bag_path, skip_index=True)
            bag_count += 1
        except:
            continue
        for topic, msg, t in bag_data.read_messages(
                topics=topic_list):
            yield topic, msg, t, bag_path, bag_count
        bag_data.close()


def register(problem_type, mod):
    '''mod：函数所属功能,用于复选框添加到ui界面'''

    def add(fn):
        FUNCTION_SET[problem_type] = [fn.__name__, mod]

        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        return wrapper

    return add


def is_in_poly(p, poly):
    """
    判断点是否在任意多边形内部
    :param p: [x, y]
    :param poly: [[], [], [], [], ...]
    :return:
    """
    px, py = p
    poly = list(poly)
    is_in = False
    for i, corner in enumerate(poly):
        next_i = i + 1 if i + 1 < len(poly) else 0
        x1, y1 = corner
        x2, y2 = poly[next_i]
        if (x1 == px and y1 == py) or (x2 == px and y2 == py):  # if point is on vertex
            is_in = True
            break
        if min(y1, y2) < py <= max(y1, y2):  # find horizontal edges of polygon
            x = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if x == px:  # if point is on edge
                is_in = True
                break
            elif x > px:  # if point is on left-side of line
                is_in = not is_in
    return is_in


def dump_problem_data(file_name, label_data, raw_perce_result, mod):
    file_path = os.path.join(os.path.dirname(BASIC_NAME), mod, 'json-' + datetime.now().strftime("%d-%H%M"))
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    file_path = os.path.join(file_path, file_name).rsplit('.', 1)[0] + '.json'
    if os.path.exists(file_path):
        problems_json_data = get_json_data(file_path)
    else:
        problems_json_data = {"task_vehicle": [], "tracks": {}}
    problems_json_data["tracks"].update(raw_perce_result)
    problems_json_data['filename'] = file_name
    problems_json_data["task_vehicle"].append(label_data)
    with open(file_path, 'w') as f:
        json.dump(problems_json_data, f, indent=4)


# iou
def bb_intersection_over_union(boxA, boxB):
    '''
    iou计算
    :param boxA,boxB: {"obstacle_bbox.x":左上角x坐标,"obstacle_bbox.y":左上角y坐标,
                "obstacle_bbox.height":y轴方向大小，"obstacle_bbox.width":x轴方向大小}
    '''
    A11 = boxA["obstacle_bbox.x"]
    A12 = boxA["obstacle_bbox.x"] + boxA["obstacle_bbox.width"]
    A21 = boxA["obstacle_bbox.y"]
    A22 = boxA["obstacle_bbox.y"] + boxA["obstacle_bbox.height"]

    B11 = boxB["obstacle_bbox.x"]
    B12 = boxB["obstacle_bbox.x"] + boxB["obstacle_bbox.width"]
    B21 = boxB["obstacle_bbox.y"]
    B22 = boxB["obstacle_bbox.y"] + boxB["obstacle_bbox.height"]

    areaA = boxA["obstacle_bbox.height"] * boxA["obstacle_bbox.width"]
    areaB = boxB["obstacle_bbox.height"] * boxB["obstacle_bbox.width"]

    interW = max(0, min(A12, B12) - max(A11, B11))
    interH = max(0, min(A22, B22) - max(A21, B21))

    interArea = interH * interW
    iou = interArea / (areaA + areaB - interArea)
    return iou


def get_json_data(json_file):
    with open(json_file) as f:
        try:
            json_data = json.load(f)
        except:
            logger.info('json文件加载失败：{}'.format(json_file))
            return None
        return json_data


def get_match_img_one_json(label_jsons, perce_jsons):
    '''
    单一标注文件
    :label_jsons:[file]
    :perce_jsons:[file1,file2,file3...]
    yield label_result,prece_result
    '''
    label_data = get_json_data(label_jsons[0])
    label_jsons_name = [temp["filename"].rsplit('.')[0] for temp in label_data]
    perce_jsons = [file for file in perce_jsons if file.rsplit('/')[-1].split('.')[0] in label_jsons_name]
    perce_jsons.sort(key=lambda x: x.rsplit('/', 1)[-1].rsplit('.')[0].rsplit('_')[-1].zfill(6))
    perce_jsons.sort(key=lambda x: x.rsplit('/', 1)[0])
    if not label_jsons or not perce_jsons:
        logger.info('无可匹配标注图片数据')
        yield None, None
        return

    for perce_json in perce_jsons:
        for label_result in label_data:
            if perce_json.split('/')[-1].split('.')[0] == label_result["filename"].split('.')[0]:
                perce_result = get_json_data(perce_json)
                yield label_result, perce_result
                break


def get_match_img_more_json(label_jsons, perce_jsons):
    '''
    多标注文件
    :label_jsons:[file1,file2,file3...]
    :perce_jsons:[file1,file2,file3...]
    yield label_result,prece_result
    '''
    label_jsons_name = [name.rsplit('/')[-1].split('.')[0] for name in label_jsons]
    perce_jsons = [file for file in perce_jsons if file.split('/')[-1].split('.')[0] in label_jsons_name]
    perce_jsons.sort(key=lambda x: x.split('/')[-1].split('.')[0].split('_')[-1].zfill(6))
    label_jsons.sort(key=lambda x: x.split('/')[-1].split('.')[0].split('_')[-1].zfill(6))
    perce_jsons = sorted(perce_jsons, key=lambda x: x.rsplit('_', 1)[0])
    label_jsons = sorted(label_jsons, key=lambda x: x.rsplit('_', 1)[0])

    if not label_jsons or not label_jsons:
        logger.info('无可匹配标注图片数据')
        yield None, None
        return

    for perce_json in perce_jsons:
        for label_json in label_jsons:
            if perce_json.split('/')[-1].split('.')[0] == label_json.split('/')[-1].split('.')[0]:
                label_result = get_json_data(label_json)
                perce_result = get_json_data(perce_json)
                yield label_result, perce_result
                break


# 同一图片标注与检出障碍物匹配
def get_match_obstacle_recall_side(label_result, perce_result):
    '''召回率单一标注文件目标障碍物匹配'''
    raw_perce_result = copy.deepcopy(perce_result)
    perce_result = perce_result["tracks"]
    configs = Config.replay_configs()
    line_compensation = configs["using_cfg"]["line_compensation"]
    proportion = configs["using_cfg"]["proportion"]
    iou_benchmark = configs['iou']
    for label_data in label_result["task_vehicle"]:
        boxA = {}
        boxA["obstacle_bbox.height"] = label_data['tags']['height'] / proportion
        boxA["obstacle_bbox.width"] = label_data['tags']['width'] / proportion
        boxA["obstacle_bbox.x"] = label_data['tags']['x'] / proportion
        boxA["obstacle_bbox.y"] = (label_data['tags']['y'] + line_compensation) / proportion

        is_in = False
        px = boxA["obstacle_bbox.x"] * proportion + boxA["obstacle_bbox.width"] * proportion / 2
        py = boxA["obstacle_bbox.y"] * proportion - line_compensation + boxA["obstacle_bbox.height"] * proportion / 2
        point = [px, py]  # 目标所在位置点

        occluded = label_data['tags']['occluded']
        attention_areas = label_result["task_attention_area"]
        if int(occluded) != 0:
            continue
        for attention_area in attention_areas:
            xn = [float(x) for x in attention_area["tags"]["xn"].replace('"', '').split(';')]
            yn = [float(y) for y in attention_area["tags"]["yn"].replace('"', '').split(';')]
            polygon = zip(xn, yn)
            if is_in_poly(point, polygon):
                is_in = True
                break
        if not is_in:
            continue
        if not perce_result:
            yield label_data, None
            continue

        iou_result = {}
        for id, perce_data in perce_result.items():
            boxB = perce_data["uv_bbox2d"]
            iou = bb_intersection_over_union(boxA, boxB)
            iou_result[id] = iou
        iou_max_item = max(iou_result.items(), key=lambda x: x[1])
        iou_max_value = iou_max_item[1]
        iou_max_id = iou_max_item[0]
        if iou_max_value >= iou_benchmark:
            yield label_data, perce_result[iou_max_id]
            del perce_result[iou_max_id]
        else:
            if label_data['tags']["class"] != 'wheel':
                label_data['tags']["problem"] = 'FN'
                dump_problem_data(label_result['filename'], label_data, raw_perce_result["tracks"], 'recall')
            yield label_data, None


def get_match_obstacle_precision_side(label_result, perce_result):
    '''准确率单一标注文件目标障碍物匹配'''
    perce_result = perce_result["tracks"]
    attention_areas = label_result["task_attention_area"]
    configs = Config.replay_configs()
    line_compensation = configs["using_cfg"]["line_compensation"]
    proportion = configs["using_cfg"]["proportion"]
    iou_benchmark = configs['iou']
    for label_data in label_result["task_vehicle"]:
        boxA = {}
        boxA["obstacle_bbox.height"] = label_data['tags']['height'] / proportion
        boxA["obstacle_bbox.width"] = label_data['tags']['width'] / proportion
        boxA["obstacle_bbox.x"] = label_data['tags']['x'] / proportion
        boxA["obstacle_bbox.y"] = (label_data['tags']['y'] + line_compensation) / proportion

        is_in = False
        px = boxA["obstacle_bbox.x"] * proportion + boxA["obstacle_bbox.width"] * proportion / 2
        py = boxA["obstacle_bbox.y"] * proportion - line_compensation + boxA["obstacle_bbox.height"] * proportion / 2
        point = [px, py]  # 目标所在位置点
        occluded = label_data['tags']['occluded']
        for attention_area in attention_areas:
            xn = [float(x) for x in attention_area["tags"]["xn"].replace('"', '').split(';')]
            yn = [float(y) for y in attention_area["tags"]["yn"].replace('"', '').split(';')]
            polygon = zip(xn, yn)
            if is_in_poly(point, polygon):
                is_in = True
                break
        if not perce_result:
            yield None, None
            return
        iou_result = {}
        for id, perce_data in perce_result.items():
            boxB = perce_data["uv_bbox2d"]
            iou = bb_intersection_over_union(boxA, boxB)
            iou_result[id] = iou
        iou_max_item = max(iou_result.items(), key=lambda x: x[1])
        iou_max_value = iou_max_item[1]
        iou_max_id = iou_max_item[0]
        if iou_max_value >= iou_benchmark:
            if int(occluded) == 0 and is_in:
                yield label_data, perce_result[iou_max_id]
            del perce_result[iou_max_id]
            continue

    if perce_result:
        for key, perce_data in perce_result.items():
            # if perce_data["uv_bbox2d"]["obstacle_bbox.width"] * perce_data["uv_bbox2d"]["obstacle_bbox.height"] < 100:
            #     continue
            if abs(perce_data["bbox3d"]["obstacle_pos_y"]) > 60:
                continue
            px = perce_data["uv_bbox2d"]["obstacle_bbox.x"] * proportion + perce_data["uv_bbox2d"][
                "obstacle_bbox.width"] * proportion / 2
            py = perce_data["uv_bbox2d"]["obstacle_bbox.y"] * proportion - line_compensation + perce_data["uv_bbox2d"][
                "obstacle_bbox.height"] * proportion / 2
            point = [px, py]
            for attention_area in attention_areas:
                xn = [float(x) for x in attention_area["tags"]["xn"].replace('"', '').split(';')]
                yn = [float(y) for y in attention_area["tags"]["yn"].replace('"', '').split(';')]
                polygon = zip(xn, yn)
                if is_in_poly(point, polygon):
                    for label_data in label_result["task_vehicle"]:
                        perce_data['problem'] = 'FP'
                        perce_problem = {key: perce_data}
                        dump_problem_data(label_result['filename'], label_data, perce_problem, 'precision')
                    yield None, perce_data


def get_match_obstacle_3d(label_result, perce_result):
    '''多文件目标障碍物匹配'''
    perce_result = perce_result["tracks"]
    configs = Config.replay_configs()
    line_compensation = configs["using_cfg"]["line_compensation"]
    proportion = configs["using_cfg"]["proportion"]
    iou_benchmark = configs['iou']
    for label_data in label_result:
        if not perce_result:
            continue
        boxA = {}
        boxA["obstacle_bbox.height"] = label_data["box_2d"]['h'] / proportion
        boxA["obstacle_bbox.width"] = label_data["box_2d"]['w'] / proportion
        boxA["obstacle_bbox.x"] = label_data["box_2d"]['x'] / proportion - boxA["obstacle_bbox.width"] / 2
        boxA["obstacle_bbox.y"] = (label_data["box_2d"]['y'] + line_compensation) / proportion - boxA[
            "obstacle_bbox.height"] / 2
        iou_result = {}
        for id, perce_data in perce_result.items():
            boxB = perce_data["uv_bbox2d"]
            iou = bb_intersection_over_union(boxA, boxB)
            iou_result[id] = iou
        iou_max_item = max(iou_result.items(), key=lambda x: x[1])
        iou_max_value = iou_max_item[1]
        iou_max_id = iou_max_item[0]
        if iou_max_value >= iou_benchmark:
            yield label_data, perce_result[iou_max_id]
            del perce_result[iou_max_id]

    # perce_result = perce_result["tracks"]
    # configs = Config.replay_configs()
    # line_compensation = configs["using_cfg"]["line_compensation"]
    # proportion = configs["using_cfg"]["proportion"]
    # for label_data in label_result["task_vehicle"]:
    #     boxA = {}
    #     boxA["obstacle_bbox.height"] = label_data['tags']['height'] / proportion
    #     boxA["obstacle_bbox.width"] = label_data['tags']['width'] / proportion
    #     boxA["obstacle_bbox.x"] = label_data['tags']['x'] / proportion
    #     boxA["obstacle_bbox.y"] = (label_data['tags']['y'] + line_compensation) / proportion
    #
    #     is_in = False
    #     px = boxA["obstacle_bbox.x"] * proportion + boxA["obstacle_bbox.width"] * proportion / 2
    #     py = boxA["obstacle_bbox.y"] * proportion - line_compensation + boxA["obstacle_bbox.height"] * proportion / 2
    #     point = [px, py]  # 目标所在位置点
    #
    #     occluded = label_data['tags']['occluded']
    #     attention_areas = label_result["task_attention_area"]
    #     if int(occluded) == 1:
    #         continue
    #     for attention_area in attention_areas:
    #         xn = [float(x) for x in attention_area["tags"]["xn"].replace('"', '').split(';')]
    #         yn = [float(y) for y in attention_area["tags"]["yn"].replace('"', '').split(';')]
    #         polygon = zip(xn, yn)
    #         if is_in_poly(point, polygon):
    #             is_in = True
    #             break
    #     if not is_in:
    #         continue
    #
    #     if not perce_result:
    #         continue
    #     iou_result = {}
    #     for id, perce_data in perce_result.items():
    #         boxB = perce_data["uv_bbox2d"]
    #         iou = bb_intersection_over_union(boxA, boxB)
    #         iou_result[id] = iou
    #     iou_max_item = max(iou_result.items(), key=lambda x: x[1])
    #     iou_max_value = iou_max_item[1]
    #     iou_max_id = iou_max_item[0]
    #     if iou_max_value >= 0.5:
    #         yield label_data, perce_result[iou_max_id]
    #         del perce_result[iou_max_id]


def draw_plot(new_path, problem_json_data):
    configs = Config.replay_configs()
    line_compensation = configs["using_cfg"]["line_compensation"]
    proportion = configs["using_cfg"]["proportion"]
    img_data = cv2.imread(new_path)
    if problem_json_data.get("task_vehicle"):
        for temp in problem_json_data["task_vehicle"]:
            A11 = temp["tags"]["x"]
            A21 = temp["tags"]["y"]
            A12 = temp["tags"]["width"] + A11
            A22 = temp["tags"]["height"] + A21
            problem = temp["tags"].get("problem")
            if problem:
                labelSize = cv2.getTextSize(problem, cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)
                x_text = int(A11) + labelSize[0][0]
                y_text = int(A21) - int(labelSize[0][1])
                cv2.rectangle(img_data, (int(A11), int(A21)), (x_text, y_text), (255, 0, 0), cv2.FILLED)
                cv2.putText(img_data, problem, (int(A11), int(A21)), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 0), 1)
            cv2.rectangle(img_data, (int(A11), int(A21)), (int(A12), int(A22)), (255, 0, 0), 2)
    if problem_json_data.get("tracks"):
        for key, perce in problem_json_data["tracks"].items():
            A11 = perce["uv_bbox2d"]["obstacle_bbox.x"] * proportion
            A21 = perce["uv_bbox2d"]["obstacle_bbox.y"] * proportion - line_compensation
            A12 = perce["uv_bbox2d"]["obstacle_bbox.width"] * proportion + A11
            A22 = perce["uv_bbox2d"]["obstacle_bbox.height"] * proportion + A21
            cv2.rectangle(img_data, (int(A11), int(A21)), (int(A12), int(A22)), (0, 255, 0), 2)
            problem = perce.get('problem')
            if problem:
                labelSize = cv2.getTextSize(problem, cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)
                x_text = int(A11) + labelSize[0][0]
                y_text = int(A21) - int(labelSize[0][1])
                cv2.rectangle(img_data, (int(A11), int(A21)), (x_text, y_text), (0, 255, 0), cv2.FILLED)
                cv2.putText(img_data, str(key) + problem, (int(A11), int(A21)), cv2.FONT_HERSHEY_COMPLEX, 0.5,
                            (0, 0, 0), 1)
    cv2.imwrite(new_path.replace('.yuv', '.png'), img_data)


def add_track_id_helper(last_json_data, json_data, idx):
    '增加track id'
    for tempA in json_data:
        boxA = {}
        boxA["obstacle_bbox.height"] = tempA["box_2d"]["h"]
        boxA["obstacle_bbox.width"] = tempA["box_2d"]["w"]
        boxA["obstacle_bbox.x"] = tempA["box_2d"]['x']
        boxA["obstacle_bbox.y"] = tempA["box_2d"]['y']

        iou_result = {}
        for num, tempB in enumerate(last_json_data):
            boxB = {}
            boxB["obstacle_bbox.height"] = tempB["box_2d"]["h"]
            boxB["obstacle_bbox.width"] = tempB["box_2d"]["w"]
            boxB["obstacle_bbox.x"] = tempB["box_2d"]['x']
            boxB["obstacle_bbox.y"] = tempB["box_2d"]['y']

            iou = bb_intersection_over_union(boxA, boxB)
            iou_result[num] = iou

        iou_max_item = max(iou_result.items(), key=lambda x: x[1])
        iou_max_value, iou_max_id = iou_max_item[1], iou_max_item[0]
        if iou_max_value >= 0.70:
            tempA['id'] = last_json_data[iou_max_id]["id"]
        else:
            tempA['id'] = idx
            idx += 1
    return json_data, idx
    # if iou_max_value >= iou_benchmark:
    #     yield label_data, perce_result[iou_max_id]
    #     del perce_result[iou_max_id]
    # else:
    #     if label_data['tags']["class"] != 'wheel':
    #         label_data['tags']["problem"] = 'FN'
    #         dump_problem_data(label_result['filename'], label_data, raw_perce_result["tracks"], 'recall')
    #     yield label_data, None


def add_track_id(file_path, save_file_path):
    if not save_file_path:
        save_file_path = file_path + '_3d'

    label_json_files = get_all_files(file_path, '.json')
    label_json_files.sort(key=lambda x: x.rsplit('/', 1)[-1].rsplit('.')[0].rsplit('_')[-1].zfill(6))

    idx = 0
    last_json_data = None

    for label_json_file in label_json_files:
        json_data = get_json_data(label_json_file)
        if idx >= 980:
            idx = 0
        if not last_json_data:
            for temp in json_data:
                temp['id'] = idx
                idx += 1
        else:
            json_data, idx = add_track_id_helper(last_json_data, json_data, idx)

        last_json_data = json_data
        save_path = label_json_file.replace(file_path, save_file_path)
        if not os.path.exists(os.path.dirname(save_path)):
            os.makedirs(os.path.dirname(save_path))
        with open(save_path, 'w') as f:
            json.dump(json_data, f, indent=4)
    # id_list = [x['id'] for x in last_json_data]
    # print(id_list)
    return save_file_path


logger = init_logger()
