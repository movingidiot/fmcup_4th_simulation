import math
import random
import time

import cv2
import numpy as np

import JudgeOverlap
from Parcel import Parcel
from RotatedRectangle import RotatedRect


class RandomParcelsGenerator(object):
    """
    随机包裹生成类，用于在包裹生成缓冲区随机生成包裹
    """
    def __init__(self, config):
        self.config = config
        # 包裹旋转矩形中心点的左边界
        self.x_start = self.config.parcels_min_size / 2
        # 包裹旋转矩形中心点的上边界
        self.y_start = self.config.parcels_min_size / 2
        # 包裹旋转矩形中心点的右边界
        self.x_bound = self.config.motor_gen_length - self.config.parcels_min_size / 2
        # 包裹旋转矩形中心点的下边界
        self.y_bound = self.config.motor_row * self.config.motor_height - self.config.parcels_min_size / 2
        # mm，包裹最小尺寸
        self.parcel_min_size = self.config.parcels_min_size
        # mm，包裹最大尺寸
        self.parcel_max_size = self.config.parcels_max_size

    def generate(self, timeout):
        """
        随机包裹生成算法
        :param timeout: 包裹生成超时
        :return: parcels list，
        """
        parcels = []
        start = cv2.getTickCount()
        # 计算需要一次生成的包裹数量
        n = math.ceil(self.config.sim_generate_rate * timeout)
        # 当生成的包裹数量未满足要求，并且还未超时，循环生成包裹
        while len(parcels) < n and (cv2.getTickCount() - start) / cv2.getTickFrequency() < timeout:
            # 在进料皮带随机生成旋转矩形框
            x = random.uniform(self.x_start, self.x_bound)
            y = random.uniform(self.y_start, self.y_bound)
            w = random.uniform(self.parcel_min_size, self.parcel_max_size)
            h = random.uniform(self.parcel_min_size, self.parcel_max_size)
            angle = random.uniform(0, math.pi)
            rrect = RotatedRect(x, y, w, h, angle)

            # 重叠标记
            is_overlap = False
            # 判断旋转矩形框是否越界, 如果没有越界
            if rrect.get_min_x() >= 0 and rrect.get_max_x() < self.config.motor_gen_length - self.config.parcels_max_size and rrect.get_min_y() >= 0 and rrect.get_max_y() < self.config.motor_row * self.config.motor_height - 1:
                # 判断旋转矩形是否与已生成的包裹旋转矩形框重叠
                for parcel in parcels:
                    is_overlap = JudgeOverlap.is_overlap(parcel.rrect, rrect)
                    # 如果存在其他任意包裹与当前生成的包裹发生重叠，直接进行下一轮包裹生成步骤
                    if is_overlap:
                        break
                # 如果当前随机生成的包裹与已存在的包裹都没有重叠，则更新包裹状态，并加入输出列表
                if not is_overlap:
                    p = Parcel(x, y, w, h, angle)
                    p.current_speed = self.config.motor_default_speed
                    p.on_belts.append(0)
                    p.drive_belt = 0
                    parcels.append(p)

        # 生成此次包裹的耗时小于timeout，线程暂停至timeout再返回生成的包裹列表
        use_time = (cv2.getTickCount() - start) / cv2.getTickFrequency()
        if use_time < timeout:
            time.sleep(timeout - use_time)
        return parcels


if __name__ == '__main__':
    gen = RandomParcelsGenerator()
    parcels = gen.generate(1)

    im = np.zeros((800, 1000, 3), np.uint8)
    im.fill(255)

    for parcel in parcels:
        color = (0, 0, 255)
        cv2.polylines(im, [parcel.rrect.get_vertices()], True, color)
    cv2.imshow("a", im)
    cv2.waitKey(0)