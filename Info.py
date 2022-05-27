import cv2

from RotatedRectangle import RotatedRect
import JudgeOverlap


class Info(object):
    """
    仿真软件工作状态信息类
    """
    def __init__(self, config):
        self.config = config
        # 包裹列表
        self.parcels = []
        # 皮带速度列表[进料皮带速度, ...分离皮带速度..., 出料皮带速度]
        self.speeds = []
        # 各个皮带所代表的旋转矩形
        self.belt_rects = []
        # 离开分离皮带的包裹数量
        self.out_count = 0
        # 最后一个包裹完全离开分离皮带的时刻
        self.last_out_time = cv2.getTickCount()
        # 最后一个完全离开分离皮带包裹的id
        self.last_out_parcel_id = None
        # 仿真软件开始工作的时刻
        self.sim_start_time = cv2.getTickCount()
        # 分离皮带速度缓存
        self.speeds_cache = []

        # 初始化各个皮带所代表的旋转矩形及初始速度
        self.belt_rects.append(RotatedRect(self.config.motor_in_length / 2,
                                           self.config.motor_row * self.config.motor_height / 2,
                                           self.config.motor_in_length,
                                           self.config.motor_row * self.config.motor_height,
                                           0))
        self.speeds.append(self.config.motor_default_speed)
        for r in range(self.config.motor_row):
            for c in range(self.config.motor_column):
                self.belt_rects.append(RotatedRect((c + 1 / 2) * self.config.motor_width + self.config.motor_in_length,
                                                   (r + 1 / 2) * self.config.motor_height,
                                                   self.config.motor_width,
                                                   self.config.motor_height,
                                                   0))
                self.speeds.append(self.config.motor_default_speed)
        self.belt_rects.append(RotatedRect(
            self.config.motor_out_length + self.config.motor_column * self.config.motor_width + self.config.motor_out_length / 2,
            self.config.motor_row * self.config.motor_height / 2,
            self.config.motor_out_length,
            self.config.motor_row * self.config.motor_height,
            0))
        if self.config.sim_mode == 'straight':
            self.speeds.append(self.config.motor_default_speed)
        elif self.config.sim_mode == 'separate':
            self.speeds.append(self.config.motor_max_speed)

        # 初始化分离皮带速度缓存
        self.speeds_cache = self.speeds[1:-1]

    def refresh_parcels_speed(self):
        """
        更新所有包裹的当前速度，包裹当前运行速度是根据包裹的旋转矩形与皮带的旋转矩形的重叠关系进行判断，包裹当前所占据的若干皮带中速度最大的
        那个皮带为驱动包裹前进的皮带，包裹当前运行速度等于当前驱动皮带的速度
        :return:
        """
        for parcel in self.parcels:
            parcel.on_belts = []

            # 进料皮带终点
            in_end = self.config.motor_in_length
            # 分离皮带终点/出料皮带起点
            out_begin = self.config.motor_in_length + self.config.motor_width * self.config.motor_column

            # 包裹完全处于进料皮带
            if parcel.rrect.get_max_x() < in_end:
                parcel.on_belts.append(0)
                parcel.drive_belt = 0
                parcel.current_speed = self.speeds[0]

            # 包裹部分进入分离皮带
            elif parcel.rrect.get_min_x() <= in_end <= parcel.rrect.get_max_x():
                parcel.on_belts.append(0)

                # 假设目前进料皮带速度比当前包裹压着的分离皮带速度都大
                if parcel.current_speed < self.speeds[0]:
                    parcel.current_speed = self.speeds[0]
                    parcel.drive_belt = 0

                # 计算当前包裹水平外接矩形所处的分离皮带范围
                belt_row_start = int(parcel.rrect.get_min_y() // self.config.motor_height)
                belt_row_end = int(parcel.rrect.get_max_y() // self.config.motor_height) + 1
                belt_col_start = 0
                belt_col_end = int((parcel.rrect.get_max_x() - in_end) //
                                   self.config.motor_width) + 1

                # 找到当前包裹所处皮带的最大速度，并记录皮带位置，速度最快的皮带即为当前包裹的驱动皮带
                for r in range(belt_row_start, belt_row_end):
                    for c in range(belt_col_start, belt_col_end):
                        idx = r * self.config.motor_column + c + 1
                        if JudgeOverlap.is_overlap(self.belt_rects[idx], parcel.rrect):
                            parcel.on_belts.append(idx)
                            if parcel.current_speed < self.speeds[idx]:
                                parcel.current_speed = self.speeds[idx]
                                parcel.drive_belt = idx

            # 包裹完全处于分离皮带范围
            elif parcel.rrect.get_min_x() > in_end and parcel.rrect.get_max_x() <= out_begin:
                # 计算当前包裹外接矩形所处的分离皮带范围
                belt_row_start = int(parcel.rrect.get_min_y() // self.config.motor_height)
                belt_row_end = int(parcel.rrect.get_max_y() // self.config.motor_height) + 1
                belt_col_start = int((parcel.rrect.get_min_x() - in_end) // self.config.motor_width)
                belt_col_end = int((parcel.rrect.get_max_x() - in_end) // self.config.motor_width) + 1

                # 假定当前最大速度是包裹中心点
                parcel.drive_belt = int((parcel.rrect.center_y - 1) // self.config.motor_height) * self.config.motor_column + \
                                    int((parcel.rrect.center_x - in_end) // self.config.motor_width) + 1
                parcel.current_speed = self.speeds[parcel.drive_belt]
                # 找到当前包裹所处皮带的最大速度，并记录皮带位置，速度最快的皮带即为当前包裹的驱动皮带
                for r in range(belt_row_start, belt_row_end):
                    for c in range(belt_col_start, belt_col_end):
                        idx = r * self.config.motor_column + c + 1
                        if JudgeOverlap.is_overlap(self.belt_rects[idx], parcel.rrect):
                            parcel.on_belts.append(idx)
                            if parcel.current_speed < self.speeds[idx]:
                                parcel.current_speed = self.speeds[idx]
                                parcel.drive_belt = idx
            # 包裹部分进入出料皮带，以最大速度运行
            elif parcel.rrect.get_max_x() > out_begin:
                parcel.on_belts.append(self.config.motor_row * self.config.motor_column + 1)
                parcel.current_speed = self.speeds[-1]
                parcel.drive_belt = self.config.motor_row * self.config.motor_column + 1

    def change_speeds_to_motor(self):
        """
        将皮带的速度更新为速度缓存中的速度，并更新所有包裹的当前运行速度
        :return:
        """
        self.speeds[1:-1] = self.speeds_cache
        self.refresh_parcels_speed()

    def copy_parcels(self):
        """
        深拷贝包裹列表
        :return: 包裹列表的深拷贝
        """
        parcels = []
        for parcel in self.parcels:
            parcels.append(parcel.copy())
        return parcels

    def get_trans_rate(self):
        """
        获取仿真软件传送包裹的效率
        :return: pph:Parcels Per Hour
        """
        # 仿真软件运行时长 s
        run_time = (cv2.getTickCount() - self.sim_start_time) / cv2.getTickFrequency()
        # 计算传送包裹效率 Parcels Per Hour
        pph = self.out_count / run_time * 3600
        return pph, run_time, self.out_count

    def print_info(self):
        """
        打印分离机工作状态信息
        :return:
        """
        # 打印分离皮带速度信息
        for r in range(self.config.motor_row):
            print(self.speeds[r * self.config.motor_column + 1: (r + 1) * self.config.motor_column + 1])
        # 打印包裹列表
        for p in self.parcels:
            print(p.to_string())

    def is_last_parcel_out_gen_area(self):
        """
        判断包裹列表是否都完全离开包裹生成区
        :return: True:所有包裹都离开包裹生成区；False：还有包裹未离开包裹生成区
        """
        if len(self.parcels) == 0:
            return True
        else:
            for parcel in self.parcels:
                if parcel.rrect.get_min_x() < self.config.motor_gen_length:
                    return False
            return True


if __name__ == '__main__':
    pass
