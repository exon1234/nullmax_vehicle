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
