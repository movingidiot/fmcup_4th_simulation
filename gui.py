import signal

import requests
import cv2
import numpy as np
import sys


def disable_ctrl_c(a, b):
    pass


def parse_time(secs):
    """
    将秒钟数转换为时分秒
    :param secs: 秒数
    :return: hour, minute, sec
    """
    hour = secs // 3600
    minute = secs % 3600 // 60
    sec = secs % 60

    return hour, minute, sec


def main():
    # 禁用ctrl+c
    signal.signal(signal.SIGINT, disable_ctrl_c)
    if len(sys.argv) < 2:
        sys.exit()

    """
    GUI程序主逻辑
    """
    # 获取仿真软件配置信息
    connect_start = cv2.getTickCount()
    while (cv2.getTickCount() - connect_start) / cv2.getTickFrequency() < 5.:
        try:
            ret = requests.get("http://127.0.0.1:5000/get_config")
            break
        except:
            print("Get config error! Retrying......")
    if (cv2.getTickCount() - connect_start) / cv2.getTickFrequency() >= 5.:
        print('Error: connection timeout!')
        sys.exit()

    # 解析仿真软件配置信息
    config = ret.json()
    motor_row = config['motor_row']
    motor_column = config['motor_column']
    sim_scale = config['sim_scale']
    motor_in_length = int(config['motor_in_length'] / sim_scale)
    motor_out_length = int(config['motor_out_length'] / sim_scale)
    motor_width = int(config['motor_width'] / sim_scale)
    motor_height = int(config['motor_height'] / sim_scale)
    max_speed = config['motor_max_speed']

    # 初始化GUI界面
    img_h = motor_row * motor_height
    img_w = motor_column * motor_width + motor_in_length + motor_out_length
    img = np.zeros((img_h + 40, img_w, 3), dtype=np.uint8)  # 图像高度加40，用于显示包裹流量信息
    img.fill(255)

    # 绘制进料皮带、分离皮带以及出料皮带
    cv2.rectangle(img, (2, 2), (motor_in_length - 4, img_h - 3), (255, 0, 255), thickness=3)  # 进料皮带
    cv2.rectangle(img, (2, 2), (motor_in_length - int(600/sim_scale), img_h - 3), (255, 0, 255), thickness=3)  # 包裹生成缓冲区
    for i in range(motor_row):
        for j in range(motor_column):
            cv2.rectangle(img,
                          (motor_in_length + j * motor_width + 1, i * motor_height),
                          (motor_in_length + (j + 1) * motor_width - 1, (i + 1) * motor_height - 1),
                          (64, 255, 0),
                          thickness=3)
    cv2.rectangle(img,
                  (motor_in_length + motor_column * motor_width + 4, 2),
                  (motor_in_length + motor_column * motor_width + motor_out_length - 2, img_h - 3),
                  (255, 0, 255),
                  thickness=3)

    # 配置输出视频文件流
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    fps = 30
    video_writer = cv2.VideoWriter('sep.mp4', fourcc, fps, (img_w, img_h+40), True)

    # 循环获取仿真软件工作状态
    while True:
        im = img.copy()
        parcels = []
        speeds = []
        # 获取仿真软件工作状态快照
        try:
            ret = requests.get("http://127.0.0.1:5000/get_snapshot")
            info = ret.json()['data']
            parcels = info[0]
            speeds = info[1]
            pph = int(info[2])
            runtime = int(info[3])
            parcels_num = info[4]
        except:
            print("Get snapshot error! Retrying......")

        # 根据分离皮带速度渲染皮带颜色
        if len(speeds) > 0:
            for i in range(motor_row):
                for j in range(motor_column):
                    speed = speeds[i * motor_column + j + 1]
                    color = (150, 150, int(255 * (1 - speed / max_speed * 0.7)))
                    pts = np.array([[motor_in_length + j * motor_width + 2, i * motor_height + 2],
                                    [motor_in_length + j * motor_width + 2, (i + 1) * motor_height - 2],
                                    [motor_in_length + (j + 1) * motor_width - 2, (i + 1) * motor_height - 2],
                                    [motor_in_length + (j + 1) * motor_width - 2, i * motor_height + 2]])
                    cv2.fillConvexPoly(im, pts, color)

        # 绘制包裹
        for parcel in parcels:
            pts = (np.array(parcel) / sim_scale).astype(np.int32).reshape(-1, 1, 2)
            cv2.polylines(im, [pts], True, (128, 0, 0), thickness=2)

        # 绘制统计信息
        h, m, s = parse_time(runtime)
        cv2.putText(im, '{}:{}:{} Parcels:{} Parcels per hour:{}'.format(str(h).zfill(2), str(m).zfill(2), str(s).zfill(2), parcels_num, pph), (0, img_h + 30), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 0), 1)

        # 将图像写入视频输出流
        video_writer.write(im)
        # 显示图像
        cv2.imshow("GUI", im)
        # 按下q键保存视频并退出GUI和Simulator程序
        key = cv2.waitKey(33)
        if key & 0xff == ord('q'):
            # 释放视频输出流资源
            video_writer.release()
            ret = requests.get("http://127.0.0.1:5000/exit")
            print(ret.text)
            break


if __name__ == '__main__':
    main()
