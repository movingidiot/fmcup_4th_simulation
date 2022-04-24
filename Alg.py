import functools

import JudgeRunOver
from Parcel import parcel_comp_by_max_x


def alg(parcels, cur_speeds, config) -> list:
    """
    控制算法
    :param parcels: list，当前处于分离皮带上的包裹列表[parcel0,parcel1,parcel2, ... ]，parceln为Parcel类，包含的包裹状态信息参看Parcel类。
    :param cur_speeds: list，当前分离皮带的运行速度列表[s00, s01, s02,...]，顺序：先沿皮带前进方向从左到右，再沿垂直于皮带前进方向从上到下。
    :param config: SeparateConfig类，仿真软件的配置信息
    :return: speeds_cache: list，分离皮带预期速度列表[s00, s01, s02,...]，顺序：先沿皮带前进方向从左到右，再沿垂直于皮带前进方向从上到下。
    """
    row = config.motor_row
    col = config.motor_column
    max_speed = config.motor_max_speed
    default_speed = config.motor_default_speed
    speeds_cache = []
    # 将所有皮带速度调整为默认速度
    for i in range(0, len(cur_speeds)):
        speeds_cache.append(config.motor_default_speed)

    # 分离皮带结束坐标
    sep_end_line = config.motor_in_length + config.motor_width * col

    # 预测一个控制间隔后的包裹坐标
    for parcel in parcels:
        parcel.current_speed = config.motor_default_speed
        parcel.forward((config.sim_control_period + config.sim_get_info_period) * 2.5)

    # 对包裹集按照max_x进行降序排序
    parcels.sort(key=functools.cmp_to_key(parcel_comp_by_max_x))

    '''
    假定max_x最大的包裹为target包裹，将其与特定范围内的包裹进行碰撞检测，若该包裹前进会碰撞其他包裹，
    修改target包裹为max_x次大的包裹,并对新的待传送包裹进行碰撞检测，以此类推,
    确定待传送包裹后，target包裹所在皮带及其所在行的后续的皮带速度调整为最大值
    '''
    for i in range(len(parcels)):
        # target包裹已部分进入出料皮带，寻找下一个target包裹
        if parcels[i].rrect.get_max_x() > sep_end_line:
            continue

        # 包裹还未完全进入分离皮带，不能作为target
        if parcels[i].rrect.get_min_x() < config.motor_in_length:
            continue

        # 假定当前包裹为target，确定其碰撞检测边界
        up = parcels[i].rrect.get_min_y()
        down = parcels[i].rrect.get_max_y()
        left = parcels[i].rrect.get_min_x()
        right = config.motor_in_length + config.motor_width * col

        is_blocked = False  # 碰撞标记
        # 检测碰撞边界范围内的包裹是否会阻挡parcels[i]前进
        for j in range(len(parcels)):
            # parcels[j]不在parcels[i]的碰撞检测范围内，跳过
            if parcels[j].rrect.get_max_x() > right or parcels[j].rrect.get_max_x() < left or parcels[j].rrect.get_max_y() < up or parcels[j].rrect.get_min_y() > down:
                continue

            # parcels[j]会阻挡parcels[i]前进
            if parcels[j].id != parcels[i].id and JudgeRunOver.who_in_front(parcels[i], parcels[j]) == -1:
                is_blocked = True
                break

        # parcels[i]会被阻挡，选择下一个包裹为target包裹
        if is_blocked:
            continue
        # parcels[i]不会会被阻挡，确认parcels[i]为target包裹，调整其所在传送带及其所在行的后续的皮带速度调整为最大值
        else:
            max_x_coord = parcels[i].rrect.get_max_x_coord()
            c = int(
                (max_x_coord[0] - 1 - config.motor_in_length) // config.motor_width)
            r = int(max_x_coord[1] // config.motor_height)
            # 这里idx不需要加1，因为speeds不包含进料皮带和出料皮带的速度
            for idx in range(r * col + c, (r + 1) * col):
                speeds_cache[idx] = max_speed
            break

    return speeds_cache
