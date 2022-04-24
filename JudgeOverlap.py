import fcl
from RotatedRectangle import RotatedRect


def is_overlap(rrect1: RotatedRect, rrect2: RotatedRect):
    """
    调用fcl库判断两个旋转矩形之间是否会发生碰撞
    :param rrect1: 旋转矩形1
    :param rrect2: 旋转矩形2
    :return: True：会发生碰撞；False：不会发生碰撞
    """
    obj1 = rrect1.get_fcl_collision_obj()
    obj2 = rrect2.get_fcl_collision_obj()
    req = fcl.CollisionRequest()
    res = fcl.CollisionResult()
    fcl.collide(obj1, obj2, req, res)
    if res.is_collision:
        return True
    else:
        return False


def judge_overlap(parcels: list):
    """
    判断包裹列表中是否存在任意两个包裹的旋转矩形发生了碰撞
    :param parcels: 包裹列表
    :return: True：包裹列表中的包裹存在碰撞关系；False：包裹列表中的包裹不存在碰撞关系
    """
    for i in range(len(parcels)):
        for j in range(i + 1, len(parcels)):
            is_overlap(parcels[i].rrect, parcels[j].rrect)
            if is_overlap(parcels[i].rrect, parcels[j].rrect):
                return True
    return False


if __name__ == '__main__':
    pass
