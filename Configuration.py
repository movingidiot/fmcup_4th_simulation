import yaml


class SeparateConfig(object):
    """
    仿真软件配置类
    """
    def __init__(self, yml_path):

        with open(yml_path, 'r', encoding="UTF-8") as file:
            self.config = yaml.load(file, Loader=yaml.FullLoader)

            # mm，包裹最小尺寸
            self.parcels_min_size = self.config['parcels']['min_size']
            # mm，包裹最大尺寸
            self.parcels_max_size = self.config['parcels']['max_size']

            # 皮带行数，平行于包裹前进方向为行
            self.motor_row = self.config['motor']['row']
            # 皮带列数，垂直于包裹前进方向为列
            self.motor_column = self.config['motor']['column']
            # mm，单个分离皮带高度，垂直于包裹前进方向
            self.motor_height = self.config['motor']['height']
            # mm，单个分离皮带宽度，平行于包裹前进方向
            self.motor_width = self.config['motor']['width']
            # mm/s，进料皮带运行速度，分离皮带默认运行速度，直通模式下出料皮带的运行速度
            self.motor_default_speed = self.config['motor']['default_speed']
            # mm/s，分离皮带最大运行速度，分离'separate'模式下出料皮带的运行速度
            self.motor_max_speed = self.config['motor']['max_speed']
            # mm，进料皮带长度，平行于包裹前进方向
            self.motor_in_length = self.config['motor']['in_length']
            # mm，包裹生成缓冲区长度，平行于包裹前进方向，包裹生成算法中包裹旋转矩形中心点在x方向上的边界，应小于进料皮带长度in_length
            self.motor_gen_length = self.config['motor']['gen_length']
            # mm，出料皮带长度
            self.motor_out_length = self.config['motor']['out_length']

            # s，调用控制算法后到改变分离皮带速度的控制延时
            self.sim_control_period = self.config['sim']['control_period']
            # s，改变分离皮带速度后到下一次调用控制算法的延时
            self.sim_get_info_period = self.config['sim']['get_info_period']
            # parcels/s，包裹生成速度
            self.sim_generate_rate = self.config['sim']['generate_rate']
            # s，包裹输出最小时间间隔
            self.sim_min_parcel_out_interval = self.config['sim']['min_parcel_out_interval']
            # straight or separate，直通或者分离模式
            self.sim_mode = self.config['sim']['mode']
            # mm/pixel，实际长度与GUI像素比例
            self.sim_scale = self.config['sim']['scale']

    def dump_config(self, dump_path="config_dump.yml"):
        with open(dump_path, 'w+', encoding="UTF-8") as file:
            yaml.dump(self.config, file, Dumper=yaml.Dumper)


if __name__ == '__main__':
    config = SeparateConfig()
    print(config)
