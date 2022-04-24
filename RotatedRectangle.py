import fcl
from math import *
import cv2
import numpy as np


class RotatedRect(object):
    def __init__(self, center_x, center_y, w, h, angle):
        self.center_x = center_x
        self.center_y = center_y
        self.w = w
        self.h = h
        self.angle = angle

        # 水平矩形顶点坐标
        _x0 = self.center_x - self.w / 2
        _y0 = self.center_y - self.h / 2
        _x1 = self.center_x - self.w / 2
        _y1 = self.center_y + self.h / 2
        _x2 = self.center_x + self.w / 2
        _y2 = self.center_y + self.h / 2
        _x3 = self.center_x + self.w / 2
        _y3 = self.center_y - self.h / 2

        # 旋转矩形顶点坐标
        self.x0 = float(floor((_x0 - self.center_x) * cos(self.angle) - (_y0 - self.center_y) * sin(self.angle) + self.center_x))
        self.y0 = float(floor((_x0 - self.center_x) * sin(self.angle) + (_y0 - self.center_y) * cos(self.angle) + self.center_y))
        self.x1 = float(floor((_x1 - self.center_x) * cos(self.angle) - (_y1 - self.center_y) * sin(self.angle) + self.center_x))
        self.y1 = float(floor((_x1 - self.center_x) * sin(self.angle) + (_y1 - self.center_y) * cos(self.angle) + self.center_y))
        self.x2 = float(floor((_x2 - self.center_x) * cos(self.angle) - (_y2 - self.center_y) * sin(self.angle) + self.center_x))
        self.y2 = float(floor((_x2 - self.center_x) * sin(self.angle) + (_y2 - self.center_y) * cos(self.angle) + self.center_y))
        self.x3 = float(floor((_x3 - self.center_x) * cos(self.angle) - (_y3 - self.center_y) * sin(self.angle) + self.center_x))
        self.y3 = float(floor((_x3 - self.center_x) * sin(self.angle) + (_y3 - self.center_y) * cos(self.angle) + self.center_y))

        # 创建3D碰撞检测对象，z轴高度默认都为1
        self.box = fcl.Box(self.w, self.h, 1.)
        self.R = np.array([[cos(-self.angle), sin(-self.angle), 0.],
                           [-sin(-self.angle), cos(-self.angle), 0.],
                           [0., 0., 1.]])
        self.T = np.array([self.center_x, self.center_y, 0.])
        self.obj = fcl.CollisionObject(self.box)
        self.obj.setRotation(self.R)
        self.obj.setTranslation(self.T)

    def get_fcl_collision_obj(self):
        """
        获取用于fcl碰撞检测库的碰撞检测对象
        :return: fcl的碰撞检测对象
        """
        return self.obj

    def get_vertices(self):
        """
        获取用于OpenCV函数绘图的旋转矩形顶点坐标
        :return: np.array([[x0, y0],
                           [x1, y1],
                           [x2, y2],
                           [x3, yd]])
        """
        return np.array([[self.x0, self.y0],
                         [self.x1, self.y1],
                         [self.x2, self.y2],
                         [self.x3, self.y3]], np.int32).reshape(-1, 1, 2)

    def get_x_coord(self):
        """
        获取旋转矩形顶点的x坐标
        :return: x轴坐标数组
        """
        return [self.x0, self.x1, self.x2, self.x3]

    def get_y_coord(self):
        """
        获取旋转矩形顶点的y坐标
        :return: y轴坐标数组
        """
        return [self.y0, self.y1, self.y2, self.y3]

    def get_min_x(self):
        """
        获取旋转矩形顶点的x坐标最小值
        :return: min_x，x轴坐标最小值
        """
        return min(self.get_x_coord())

    def get_max_x(self):
        """
        获取旋转矩形顶点的x坐标最大值
        :return: max_x，x轴坐标最大值
        """
        return max(self.get_x_coord())

    def get_min_y(self):
        """
        获取旋转矩形顶点的y坐标最小值
        :return: min_y，y轴坐标最小值
        """
        return min(self.get_y_coord())

    def get_max_y(self):
        """
        获取旋转矩形顶点的y坐标最大值
        :return: max_y，y轴坐标最大值
        """
        return max(self.get_y_coord())

    def get_max_x_coord(self):
        """
        获取旋转矩形x坐标最大的顶点的坐标
        :return: （x, y），x轴坐标最大的顶点的坐标
        """
        idx = self.get_x_coord().index(self.get_max_x())
        return self.get_coord()[idx]

    def forward(self, length):
        """
        沿x轴方向平移旋转矩形
        :param length: 平移距离，单位：mm
        :return:
        """
        # 更新顶点x坐标
        self.x0 += float(floor(length))
        self.x1 += float(floor(length))
        self.x2 += float(floor(length))
        self.x3 += float(floor(length))
        # 更新中心点x坐标
        self.center_x += length
        # 更新用于fcl碰撞检测对象的平移矩阵
        self.T = np.array([self.center_x, self.center_y, 0.])
        self.obj.setTranslation(self.T)

    def get_coord(self):
        """
        获取旋转矩形的顶点坐标
        :return: [[x0, y0], [x1, y1], [x2, y2], [x3, yd]]
        """
        return [[self.x0, self.y0],
                [self.x1, self.y1],
                [self.x2, self.y2],
                [self.x3, self.y3]]


if __name__ == '__main__':
    img = np.zeros((1000, 2000, 3), np.uint8)
    img.fill(255)

    rrect = RotatedRect(100, 400, 200, 50, radians(-45))
    pts = rrect.get_vertices()
    pts1 = np.array([[701.8749601780288, 600.9188325940389],
                     [856.4644458563041, 758.8526507512858],
                     [1040.1250398219713, 579.0811674059611],
                     [885.5355541436959, 421.14734924871425]], np.int).reshape(-1, 1, 2)
    pts2 = np.array([[1070.8447006870674, 659.656762811516],
                     [848.1253949192453, 815.7980796956108],
                     [1011.1552993129326, 1048.343237188484],
                     [1233.8746050807547, 892.2019203043892]], np.int).reshape(-1, 1, 2)
    cv2.polylines(img, [pts1], True, (0, 255, 255))
    cv2.polylines(img, [pts2], True, (0, 0, 255))
    cv2.imshow("a", img)
    cv2.waitKey(0)