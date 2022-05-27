import copy
import functools
import json
import os
import threading
import time
import logging

import cv2
from flask import Flask

import JudgeOverlap
import JudgeRunOver
from Alg import alg
from InfoLock import *
from Info import Info
from Parcel import Parcel, parcel_comp_by_max_x, parcel_comp_by_min_x
from Singleton import singleton

import logging

# 控制算法控制事件
alg_event = threading.Event()
exit_signal = False
app = Flask(__name__)

config = None


class FlaskThread(threading.Thread):
    """
    Flask服务器线程
    """
    def __init__(self):
        threading.Thread.__init__(self)
        # 关闭flask的控制台log
        log = logging.getLogger('werkzeug')
        log.disabled = True
        app.logger.disabled = True

    def run(self) -> None:
        app.run()


# ----------------------------Flask config---------------------------------


@app.route('/get_config')
def get_config():
    """
    处理获取仿真软件配置信息的请求
    :return:
    """
    global config
    t = {'motor_row': config.motor_row,
         'motor_column': config.motor_column,
         'motor_width': config.motor_width,
         'motor_height': config.motor_height,
         'motor_in_length': config.motor_in_length,
         'sim_scale': config.sim_scale,
         'motor_out_length': config.motor_out_length,
         'motor_max_speed': config.motor_max_speed}
    return json.dumps(t, ensure_ascii=False)


@app.route('/get_snapshot')
def get_snapshot():
    """
    处理获取仿真软件工作状态快照的请求
    :return:
    """
    t = {}
    with InfoLock().lock:
        ps = []
        for parcel in Sim().info.parcels:
            ps.append(parcel.rrect.get_coord())
        speeds = copy.deepcopy(Sim().info.speeds)
        pph, run_time, parcels_cnt = Sim().info.get_trans_rate()

    t['data'] = [ps, speeds, pph, run_time, parcels_cnt]
    return json.dumps(t, ensure_ascii=False)


@app.route('/exit')
def exit_sim():
    global exit_signal
    exit_signal = True
    return 'Simulator exited.'


class TransThread(threading.Thread):
    """
    包裹传输线程，用于控制包裹的前进，包裹前进过程中会进行碰撞检测，出双检测，穿越检测以及输出间距检测
    """
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.config = config
        # 分离皮带起点坐标
        self.sep_start_line = self.config.motor_in_length
        # 分离皮带终点坐标
        self.sep_end_line = self.config.motor_in_length + \
                            self.config.motor_column * self.config.motor_width
        # 出料皮带终点坐标
        self.belt_end_line = self.config.motor_in_length + \
                             self.config.motor_column * self.config.motor_width + \
                             self.config.motor_out_length

    def run(self) -> None:
        # 初始化传送时间间隔
        forward_start = cv2.getTickCount()
        forward_one_round_time = 0.
        while True:
            with InfoLock().lock:
                # 更新包裹碰撞关系
                JudgeRunOver.refresh_parcels_order(Sim().info.parcels)

                # 更新包裹当前速度
                Sim().info.refresh_parcels_speed()

                # 传送包裹
                now = cv2.getTickCount()
                # 预估传送时间
                interval = (now - forward_start) / cv2.getTickFrequency() + forward_one_round_time
                forward_start = now
                for parcel in Sim().info.parcels:
                    parcel.forward(interval)
                forward_done = cv2.getTickCount()
                forward_one_round_time = (forward_done - forward_start) / cv2.getTickFrequency()
                forward_start = forward_done

                # 再次更新包裹当前速度
                Sim().info.refresh_parcels_speed()

                # 检测是否发生出双
                if self.config.sim_mode == 'separate':
                    on_sep_end_line_num = 0
                    for parcel in Sim().info.parcels:
                        if parcel.rrect.get_min_x() < self.sep_end_line < parcel.rrect.get_max_x():
                            on_sep_end_line_num += 1
                            if on_sep_end_line_num > 1:
                                Sim().logger.error('Parcels double out!')
                                Sim().info.print_info()
                                raise Exception("包裹发生出双")

                # 检测是否发生碰撞
                if JudgeOverlap.judge_overlap(Sim().info.parcels):
                    Sim().logger.error('Parcels collision!')
                    Sim().info.print_info()
                    raise Exception("包裹发生碰撞")

                # 检测是否发生穿越
                if JudgeRunOver.judge_run_over(Sim().info.parcels):
                    Sim().logger.error('Parcels collision(run over)!')
                    Sim().info.print_info()
                    raise Exception("包裹发生碰撞(穿越)")

                # 检测送出包裹的时间间隔，并删除已送出包裹
                del_idx = -1
                # 将包裹按照min_x进行降序排列
                Sim().info.parcels.sort(key=functools.cmp_to_key(parcel_comp_by_min_x))
                parcels_size = len(Sim().info.parcels)
                for i in range(parcels_size):
                    if Sim().info.parcels[i].rrect.get_min_x() > self.belt_end_line:
                        del_idx = i
                    # 如果包裹已经被标记过，则跳过
                    if Sim().info.parcels[i].is_leave_sep_belt:
                        continue
                    # 如果包裹前端已经离开分离皮带
                    if Sim().info.parcels[i].rrect.get_max_x() > self.sep_end_line:
                        # 如果已经有包裹完全离开分离皮带，并且当前包裹不是上一个完全离开分离皮带的包裹，计算它们之间的时间间隔
                        if Sim().info.last_out_parcel_id is not None and Sim().info.parcels[i].id != Sim().info.last_out_parcel_id:
                            # 计算当前包裹开始离开分离皮带的时刻
                            now = forward_done / cv2.getTickFrequency()
                            leave_time = (Sim().info.parcels[i].rrect.get_max_x() - self.sep_end_line) / self.config.motor_max_speed
                            start_leave_time = now - leave_time
                            # 如果当前包裹开始离开分离皮带的时刻与上一包裹完全离开分离皮带时刻的间隔过小，则报错
                            if start_leave_time - Sim().info.last_out_time < self.config.sim_min_parcel_out_interval and self.config.sim_mode == 'separate':
                                print('leave_time: ', leave_time, 'start_leave_time:', start_leave_time, 'last_out_time:', Sim().info.last_out_time)
                                raise Exception('包裹输出间隔过小')

                        # 如果包裹已经完全离开分离皮带，并且未被记录为last_out_parcel
                        if Sim().info.parcels[i].rrect.get_min_x() > self.sep_end_line:
                            Sim().info.parcels[i].is_leave_sep_belt = True
                            Sim().info.out_count += 1
                            # 计算当前包裹完全离开分离皮带的时间
                            now = forward_done / cv2.getTickFrequency()
                            finish_leave_time = now - (Sim().info.parcels[i].rrect.get_min_x() - self.sep_end_line) / self.config.motor_max_speed
                            # 是否为第一个离开分离皮带的包裹
                            if Sim().info.last_out_parcel_id is None:
                                Sim().info.last_out_time = finish_leave_time
                                Sim().info.last_out_parcel_id = Sim().info.parcels[i].id
                            else:
                                if finish_leave_time > Sim().info.last_out_time:
                                    Sim().info.last_out_time = finish_leave_time
                                    Sim().info.last_out_parcel_id = Sim().info.parcels[i].id
                    # 包裹前端还未离开分离皮带
                    else:
                        break
                # 删除已经完全离开分离皮带的包裹
                if del_idx != -1:
                    Sim().info.parcels = Sim().info.parcels[del_idx+1:]

            time.sleep(0.0001)


class WorkThread(threading.Thread):
    """
    仿真软件工作线程
    """
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.config = config

    def run(self) -> None:
        while True:
            time.sleep(self.config.sim_get_info_period)
            # 通过事件启动控制算法
            alg_event.set()
            time.sleep(self.config.sim_control_period)
            # 将分离皮带速度更新为分离皮带缓存速度
            with InfoLock().lock:
                with SpeedCacheLock().lock:
                    Sim().info.change_speeds_to_motor()
                # 更新包裹当前速度
                Sim().info.refresh_parcels_speed()


class GenThread(threading.Thread):
    """
    包裹生成线程
    """
    def __init__(self, name, generator, config):
        threading.Thread.__init__(self)
        self.name = name
        self.generator = generator
        self.config = config

    def run(self) -> None:
        # 更新仿真软件开始工作的时间
        Sim().info.sim_start_time = cv2.getTickCount()
        # 计算包裹生成算法的超时
        timeout = 1. * self.config.motor_gen_length / self.config.motor_default_speed

        start_time = cv2.getTickCount()
        # 以timeout为周期循环在包裹生成缓冲区生成包裹
        while True:
            # 调用包裹生成算法
            parcels = self.generator.generate(timeout)

            # 判断已有的包裹是否都离开包裹生成区
            while not Sim().info.is_last_parcel_out_gen_area():
                time.sleep(0.05)

            # 保证固定时间周期更新包裹
            use_time = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
            if use_time < timeout:
                time.sleep(timeout - use_time)
            start_time = cv2.getTickCount()

            # 将生成的包裹更新到包裹生成缓冲区中
            with InfoLock().lock:
                for parcel in parcels:
                    Sim().info.parcels.append(parcel.copy())


class AlgThread(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.config = config

    def run(self) -> None:
        while True:
            alg_event.wait()
            # 获取分离皮带速度信息和处于分离皮带范围内的包裹信息，用于控制算法的计算
            with InfoLock().lock:
                speeds = Sim().info.speeds[1:-1]
                parcels = []
                for parcel in Sim().info.parcels:
                    if parcel.rrect.get_max_x() > self.config.motor_in_length and \
                            parcel.rrect.get_min_x() < self.config.motor_in_length + \
                            self.config.motor_column * self.config.motor_width:
                        parcels.append(parcel.copy())

# --------------------------------------------------控制算法开始----------------------------------------------------------

            speeds_cache = alg(parcels, speeds, config)

# -------------------------------------------------控制算法结束-----------------------------------------------------------

            # 将控制算法生成的分离皮带预期速度写入分离皮带速度缓存中，仿真软件会在特定的时间段将缓存的速度更新到分离皮带
            with SpeedCacheLock().lock:
                Sim().info.speeds_cache = copy.deepcopy(speeds_cache)
            alg_event.clear()


@singleton
class Sim(object):
    """
    仿真软件类
    """
    def __init__(self, generator, sim_config):
        global config
        config = sim_config
        # 配置日志
        self.logger = logging.getLogger('sim')
        self.logger.setLevel(logging.INFO)

        logfile = './log.txt'
        fh = logging.FileHandler(logfile, mode='a')
        fh.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        # 完成配置日志

        self.threads = []
        self.info = Info(config=config)

        # 载入配置
        self.logger.info('Loading config...')

        self.logger.info('Load config done.')

        self.logger.info('Add transport parcels thread.')
        # 添加传送包裹传线程
        self.threads.append(TransThread(config=config))

        self.logger.info('Add parcels generator thread.')
        # 配置包裹生成器
        self.parcels_generator = generator

        # 添加包裹生成线程
        if self.parcels_generator is not None:
            self.threads.append(GenThread(name="GenThread", generator=self.parcels_generator, config=config))
        else:
            self.logger.error('Please input correct parcels generator!')
            raise Exception('请输入正确的包裹生成器参数')

        # 如果工作在分离模式，添加控制算法相关线程
        if config.sim_mode == 'separate':
            print(config.sim_mode)
            self.logger.info('Add control thread.')
            self.threads.append(WorkThread(config=config))
            self.threads.append(AlgThread(config=config))

        # 添加Flask服务器线程
        self.threads.append(FlaskThread())

    def run(self):
        """
        启动所有线程
        :return:
        """
        for t in self.threads:
            t.start()

        global exit_signal
        while not exit_signal:
            time.sleep(0.01)
            pass
        os._exit(0)


if __name__ == '__main__':
    pass
