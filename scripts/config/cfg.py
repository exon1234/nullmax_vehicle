import numpy as np
from pprint import pprint


class Config:
    def __init__(self):
        self.evalcfgs = {
            'conf_thre': 0.001,
            'iou_thres': np.linspace(0.5, 0.95, 10, endpoint=True),
            'recall_thres': np.linspace(.0, 1.00, 101, endpoint=True),
            'max_dets': [1, 10, 100],
            'fn_ios_thre': 0.2,
            'fp_ios_thre': 0.5,
            'ign_ios_thre': 0.5,
            'cate_miscls_iou_thre': 0.5,
            'area_types': ['all', 'small', 'medium', 'large'],
            'area_ranges': [(0 ** 2, 1e5 ** 2), (0 ** 2, 32 ** 2), (32 ** 2, 96 ** 2), (96 ** 2, 1e5 ** 2)],
            'catenms': ['car', 'truck', 'bus', 'pedestrian', 'bicycle', 'motorcycle', 'tricycle', 'barrier',
                        'cone', 'sign', 'lock', 'None']
        }
        # print('\n==> (cfg.py) default evalcfgs: ')
        # pprint(self.evalcfgs)

    @classmethod
    def replay_configs(cls):
        configs = {
            "using_cfg": {"line_compensation": 0, "proportion": 1},
            "iou": 0.5,
            "enum_obstacle": {0: 'car', 1: 'truck', 2: 'bus', 3: 'pedestrian', 4: 'bicycle', 5: 'motorcycle',
                              6: 'tricycle', 7: 'rider', 8: 'cone', 9: 'barrier', 10: 'sign', 11: 'TRAFFIC_LIGHT'},
            # "analyze_obstacle": ['car', 'truck', 'bus', 'pedestrian', 'bicycle', 'motorcycle', 'tricycle', 'rider'],
            "analyze_obstacle": ['car', 'truck', 'bus', 'pedestrian', 'bicycle'],
            "SML_obstacle_cfg": {'small': (0, 1024), 'middle': (1024, 9216), 'large': (9216, 200000)},
            "ranging_obstacle_x": {'0~20': (0, 20), '20~35': (20, 35), '35~60': (35, 60)},
            "ranging_obstacle_y": {'first': (0, 4), 'second': (4, 8), 'third': (8, 12), 'ego_lane': (0, 1)},
        }
        return configs
