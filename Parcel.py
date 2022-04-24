import copy
import uuid
from RotatedRectangle import RotatedRect


class Parcel(object):
    """
    包裹类
    """
    def __init__(self, x, y, w, h, angle):
        # 包裹id
        self.id = str(uuid.uuid1())
        # 包裹旋转矩形框
        self.rrect = RotatedRect(x, y, w, h, angle)
        # 和包裹重叠的皮带列表
        self.on_belts = []
        # 当前驱动包裹的皮带
        self.drive_belt = 0
        # 包裹当前的运行速度
        self.current_speed = 0
        # 可能阻挡包裹前进的包裹列表
        self.parcels_in_front = []
        # 包裹完全离开分离皮带标志位
        self.is_leave_sep_belt = False

    def forward(self, interval):
        """
        向前传送包裹
        :param interval:向前传送的时长，单位s
        :return:
        """
        length = int(self.current_speed * interval)  # mm
        self.rrect.forward(length)

    def copy(self):
        """
        深拷贝包裹对象
        :return: parcel_copy，返回当前包裹类的深拷贝对象
        """
        parcel_copy = Parcel(self.rrect.center_x, self.rrect.center_y, self.rrect.w, self.rrect.h, self.rrect.angle)
        parcel_copy.id = self.id
        parcel_copy.on_belts = copy.deepcopy(self.on_belts)
        parcel_copy.drive_belt = self.drive_belt
        parcel_copy.current_speed = self.current_speed
        parcel_copy.parcels_in_front = copy.deepcopy(self.parcels_in_front)
        parcel_copy.is_leave_sep_belt = self.is_leave_sep_belt
        return parcel_copy

    def to_string(self):
        """
        获取包裹状态信息字符串
        :return: 包裹状态信息字符串
        """
        return 'id:{};p_in_f:{};speed:{};drive:{};on:{};xywha:{}, {}, {}, {}, {};coords:{}'.format(self.id,
                                                                                                   self.parcels_in_front,
                                                                                                   self.current_speed,
                                                                                                   self.drive_belt,
                                                                                                   self.on_belts,
                                                                                                   self.rrect.center_x,
                                                                                                   self.rrect.center_y,
                                                                                                   self.rrect.w,
                                                                                                   self.rrect.h,
                                                                                                   self.rrect.angle,
                                                                                                   self.rrect.get_coord())


def parcel_comp_by_max_x(p1, p2):
    """
    比较器，比较两个包裹旋转矩形max_x的大小，用于对包裹列表按照各个包裹旋转矩形的max_x值进行降序排列
    :param p1: Parcel
    :param p2: Parcel
    :return: 0 or 正数 or 负数，0表示相等，正数表示p2的max_x大于p1，负数表示p2的max_x小于p1
    """
    return p2.rrect.get_max_x() - p1.rrect.get_max_x()


def parcel_comp_by_min_x(p1, p2):
    """
    比较两个包裹旋转矩形min_x的大小，用于对包裹列表按照各个包裹旋转矩形的min_x值进行降序排列
    :param p1: Parcel
    :param p2: Parcel
    :return: 0 or 正数 or 负数，0表示相等，正数表示p2的min_x大于p1，负数表示p2的min_x小于p1
    """
    return p2.rrect.get_min_x() - p1.rrect.get_min_x()


if __name__ == '__main__':
    pass

