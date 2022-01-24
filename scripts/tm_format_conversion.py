# -*- coding: utf-8 -*-
import json
import os, cv2
from PIL import Image
import traceback
import utils


def img_to_video(file_path, file_extension, save_file_path=None, raw_path=None):
    """
    获取所有后缀为file_extension的文件
    """
    if not raw_path:
        raw_path = file_path
    if not save_file_path:
        save_file_path = file_path + '_video'
    files = []
    list_dir = os.listdir(file_path)
    for each in list_dir:
        each_path = os.path.join(file_path, each)
        if os.path.isdir(each_path):
            img_to_video(each_path, file_extension, save_file_path, raw_path)
        if os.path.isfile(each_path) and each_path.endswith(file_extension):
            files.append(each_path)
    img_to_video_helper(files, raw_path, save_file_path, )


def img_to_video_helper(imgs, file_path, save_file_path):
    if not imgs:
        return
    imgs.sort(key=lambda x: x.split('_')[-1].split('.')[0].zfill(6))
    imgs.sort(key=lambda x: x.rsplit('/', 1)[0])

    im = Image.open(imgs[0])
    video_dir = os.path.dirname(imgs[0]).replace(file_path, save_file_path) + '.avi'
    if not os.path.exists(os.path.dirname(video_dir)):
        os.makedirs(os.path.dirname(video_dir))
    fourc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    fps = 14
    img_size = (im.size[0], im.size[1])
    videoWriter = cv2.VideoWriter(video_dir, fourc, fps, img_size)
    for im_name in imgs:
        try:
            frame = cv2.imread(im_name)
            videoWriter.write(frame)
        except:
            utils.logger.error(traceback.format_exc())
            continue
    videoWriter.release()


def png_to_bmp(file_path, save_file_path=None):
    if not save_file_path:
        save_file_path = file_path + '_bmp'
    imgs = utils.get_all_files(file_path, '.png')
    for img in imgs:
        save_path = img.replace(file_path, save_file_path).replace('.png', '.bmp')
        if not os.path.exists(os.path.dirname(save_path)):
            os.makedirs(os.path.dirname(save_path))
        img = cv2.imread(img)
        img = img[90:-38, :, :]
        img = cv2.resize(img, (640, 384))
        cv2.imwrite(save_path, img)


def png_to_yuv(file_path, save_file_path=None):
    if not save_file_path:
        save_file_path = file_path + '_yuv'
    imgs = utils.get_all_files(file_path, '.png')
    for img in imgs:
        save_path = img.replace(file_path, save_file_path).replace('.png', '.yuv')
        if not os.path.exists(os.path.dirname(save_path)):
            os.makedirs(os.path.dirname(save_path))
        command = "ffmpeg -s 1920x1080 -pix_fmt nv12 -i {} {}".format(img, save_path)
        os.system(command)


def transform_3d(file_path, save_file_path=None):
    file_path = '/home/user/Desktop/fov/gt'

    track_file_path = utils.add_track_id(file_path, save_file_path)
    label_json_files = utils.get_all_files(track_file_path, '.json')
    label_json_files.sort(key=lambda x: x.rsplit('/', 1)[-1].rsplit('.')[0].rsplit('_')[-1].zfill(6))

    que = []
    for label_json_file in label_json_files:
        json_data = utils.get_json_data(label_json_file)
        que.insert(0, json_data)
        if len(que) <= 3:
            for temp in json_data:
                temp["box_3d"]["velocity"] = {"x": -1000, "Y": -1000, "z": -1000}
        else:
            last_data = que.pop()
            last_data_id = [x["id"] for x in last_data]
            for temp in json_data:
                if temp["id"] in last_data_id:
                    last_temp = [x for x in last_data if x["id"] == temp["id"]][0]
                    temp["box_3d"]["velocity"] = {
                        "x": round((temp["box_3d"]["dists"]['x'] - last_temp["box_3d"]["dists"]["x"]) / 0.3, 3),
                        "y": round((temp["box_3d"]["dists"]['y'] - last_temp["box_3d"]["dists"]["y"]) / 0.3, 3),
                        "z": round((temp["box_3d"]["dists"]['z'] - last_temp["box_3d"]["dists"]["z"]) / 0.3, 3)
                    }
                else:
                    temp["box_3d"]["velocity"] = {"x": -1000, "Y": -1000, "z": -1000}
        with open(label_json_file, 'w') as f:
            json.dump(json_data, f, indent=4)

    # for json_file in label_jsons:
    #     save_path = json_file.replace(file_path, save_file_path)
    #     if not os.path.exists(os.path.dirname(save_path)):
    #         os.makedirs(os.path.dirname(save_path))
    #
    #     command = "ffmpeg -s 1920x1080 -pix_fmt nv12 -i {} {}".format(img, save_path)
    #     os.system(command)


'''
# id生成
原始jsons排序 +遍历
第一帧id赋予    + 数据存储 + id最大1000
第二帧id继承 + id赋予  + 数据存储 + id最大1000
第三帧~最后一帧  复用的第二帧逻辑

# 3d数据生成
新jsons排序 + 遍历
前十帧率缓存 
第十一帧根据id 3d数据生成 + 无效数据标记 + 第一帧id更新 + 第十一帧数据更新 
第十二帧 ~ 最后一帧 复用第十一帧逻辑
最终结果
'''
