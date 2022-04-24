import numpy as np
import cv2

from Parcel import Parcel


def is_on_segment(pi, pj, pk):
    """
    判断点pk是否在线段(pi, pj)上
    :param pi: [xi, yi]，线段的端点1
    :param pj: [xj, yj]，线段的端点2
    :param pk: [xk, yk]
    :return: True：pk在(pi, pj)表示的线段上；False：pk不在(pi, pj)表示的线段上
    """
    min_x = min(pi[0], pj[0])
    max_x = max(pi[0], pj[0])
    min_y = min(pi[1], pj[1])
    max_y = max(pi[1], pj[1])

    return min_x <= pk[0] <= max_x and min_y <= pk[1] <= max_y


def cvx_dir(pi, pj, pk):
    """
    判断点pk与线段(pi, pj)的位置关系
    :param pi: [xi, yi]，线段的端点1
    :param pj: [xj, yj]，线段的端点2
    :param pk: [xk, yk]
    :return: True：pk在(pi, pj)表示的线段上；False：pk不在(pi, pj)表示的线段上
    """
    x1 = pk[0] - pi[0]
    y1 = pk[1] - pi[1]
    x2 = pj[0] - pi[0]
    y2 = pj[1] - pi[1]
    return x1 * y2 - x2 * y1


def cvx_is_intersect(p1, p2, p3, p4):
    """
    判断两个线段是否相交，并求出交点
    :param p1: [x1, y1]，线段1的端点1
    :param p2: [x2, y2]，线段1的端点2
    :param p3: [x3, y3]，线段2的端点1
    :param p4: [x4, y4]，线段2的端点2
    :return: True, [x, y]：两个线段存在交点以及它们的交点；False, []：两个线段不存在交点
    """
    res = []
    d1 = cvx_dir(p3, p4, p1)
    d2 = cvx_dir(p3, p4, p2)
    d3 = cvx_dir(p1, p2, p3)
    d4 = cvx_dir(p1, p2, p4)
    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        d = (p2[1] - p1[1]) * (p4[0] - p3[0]) - (p4[1] - p3[1]) * (p2[0] - p1[0])
        tx = (p2[0] - p1[0]) * (p4[0] - p3[0]) * (p3[1] - p1[1]) + \
            (p2[1] - p1[1]) * (p4[0] - p3[0]) * p1[0] - \
            (p4[1] - p3[1]) * (p2[0] - p1[0]) * p3[0]
        ty = (p2[1] - p1[1]) * (p4[1] - p3[1]) * (p3[0] - p1[0]) + \
            (p2[0] - p1[0]) * (p4[1] - p3[1]) * p1[1] - \
            (p4[0] - p3[0]) * (p2[1] - p1[1]) * p3[1]
        x = 1.0 * tx / d
        y = -1.0 * ty / d
        res.append(x)
        res.append(y)
        return True, res
    if d1 == 0 and is_on_segment(p3, p4, p1):
        res.append(p1[0])
        res.append(p1[1])
        return True, res
    if d2 == 0 and is_on_segment(p3, p4, p2):
        res.append(p2[0])
        res.append(p2[1])
        return True, res
    if d3 == 0 and is_on_segment(p1, p2, p3):
        res.append(p3[0])
        res.append(p3[1])
        return True, res
    if d4 == 0 and is_on_segment(p1, p2, p4):
        res.append(p4[0])
        res.append(p4[1])
        return True, res

    return False, res


def parcel_cross_line(parcel: Parcel, line):
    """
    判断包裹的任意一条边与直线是否有交点
    :param parcel: 包裹
    :param line: list [[x1, y1], [x2, y2]]两点确定直线
    :return: 如果直线与包裹的任意一条边有交点，返回True和交点坐标：True, [x, y]；不相交：False, []
    """
    coords = parcel.rrect.get_coord()
    for i in range(len(coords)):
        is_intersect, pts = cvx_is_intersect(coords[i], coords[(i + 1) % 4], line[0], line[1])
        if is_intersect:
            return is_intersect, pts

    return False, []


def who_in_front(parcel1: Parcel, parcel2: Parcel):
    """
    包裹1,2是否会相互阻挡前进
    :param parcel1:
    :param parcel2:
    :return: 0：没有先后顺序，1：parcel1在前，-1：parcel2在前
    """
    p1_x = 0
    p2_x = 0

    # 判断parcel1和parcel2在y轴方向上所占的区间是否有重叠区域，没有则不会阻挡parcel1前进
    if parcel1.rrect.get_max_y() - parcel2.rrect.get_min_y() < 0 or parcel1.rrect.get_min_y() - parcel2.rrect.get_max_y() > 0:
        return 0
    # 如果有重叠区域，判断parcel1和parcel2的先后关系
    else:
        # 获取重叠区域的上下边界，取上下边界的中线
        up = max(parcel1.rrect.get_min_y(), parcel2.rrect.get_min_y())
        down = min(parcel1.rrect.get_max_y(), parcel2.rrect.get_max_y())
        mid = (up + down) / 2.
        line = [[0., mid], [100000., mid]]
        # 求parcel1任意一边与中线的交点
        is_intersect, pts = parcel_cross_line(parcel1, line)
        if not is_intersect:
            return 0
        if is_intersect:
            p1_x = pts[0]
        # 求parcel2任意一边与中线的交点
        is_intersect, pts = parcel_cross_line(parcel2, line)
        if is_intersect:
            p2_x = pts[0]
        # 判断parcel2是否在parcel1前面
        if p1_x > p2_x:
            return 1
        elif p1_x < p2_x:
            return -1


def is_run_over(parcel1: Parcel, parcel2: Parcel) -> bool:
    """
    判断两个包裹之间是否发生了穿越
    :param parcel1:
    :param parcel2:
    :return: True/False，True：两个包裹之间存在穿越情况，False：两个包裹之间不存在穿越情况
    """

    # 如果上一个状态两个包裹互相并不存在可能阻挡前进的情况，直接返回False
    if parcel1.id not in parcel2.parcels_in_front and parcel2.id not in parcel1.parcels_in_front:
        return False

    # 判断当前两个包裹哪个会阻挡另一个包裹前进
    ret = who_in_front(parcel1, parcel2)
    # 都不会发生阻挡
    if ret == 0:
        return False
    # parcel1阻挡在parcel2前，并且在上一状态parcel2阻挡在parcel1前面，发生穿越情况
    elif ret == 1 and parcel2.id in parcel1.parcels_in_front:
        return True
    # parcel2阻挡在parcel1前，并且在上一状态parcel1阻挡在parcel2前面，发生穿越情况
    elif ret == -1 and parcel1.id in parcel2.parcels_in_front:
        return True

    return False


def judge_run_over(parcels: list) -> bool:
    """
    判断包裹列表中是否存在任意两个包裹之间发生了穿越
    :param parcels:包裹列表
    :return: True/False，True：包裹列表中存在穿越情况，False：包裹列表中不存在穿越情况
    """
    for i in range(len(parcels)):
        for j in range(i + 1, len(parcels)):
            if is_run_over(parcels[i], parcels[j]):
                print(parcels[i].id, parcels[i].rrect.get_max_x(), parcels[i].rrect.center_x, parcels[i].rrect.center_y, parcels[i].rrect.w, parcels[i].rrect.h, parcels[i].rrect.angle)
                print(parcels[j].id, parcels[j].rrect.get_max_x(), parcels[j].rrect.center_x, parcels[j].rrect.center_y, parcels[j].rrect.w, parcels[j].rrect.h, parcels[j].rrect.angle)
                return True
    return False


def refresh_parcels_order(parcels: list):
    """
    更新包裹列表中各个包裹之间的阻挡关系
    :param parcels: 包裹列表
    :return:
    """
    parcels_size = len(parcels)
    for i in range(parcels_size):
        parcels[i].parcels_in_front = []
        for j in range(parcels_size):
            if parcels[i].id != parcels[j].id:
                # 计算两个包裹的阻挡关系
                order = who_in_front(parcels[i], parcels[j])
                if order == -1:
                    # 若parcels[j]会阻挡parcels[i]前进，将parcels[j]的id加入parcels[i]的阻挡包裹列表中
                    parcels[i].parcels_in_front.append(parcels[j].id)


if __name__ == '__main__':

    p1 = Parcel(6000.1138142478485, 823.9784258628027, 217.5299048646885, 283.3465038993628, 1.7428324329682836)
    p2 = Parcel(6220.228657488085, 550.3577501765337, 114.83172132209566, 338.2660026081668, 2.370782161711933)

    print(who_in_front(p1, p2))
    print(judge_run_over([p1, p2]))

    img = np.zeros((5000, 10000, 3), np.uint8)
    img.fill(255)

    cv2.polylines(img, [p1.rrect.get_vertices()], True, (255, 0, 0))
    cv2.polylines(img, [p2.rrect.get_vertices()], True, (0, 0, 255))

    cv2.imshow("a", img)
    cv2.waitKey(0)
    cv2.imwrite('a.jpg', img)

