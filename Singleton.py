def singleton(cls):
    """
    用于定义单例对象
    :param cls:
    :return:
    """
    _instance = {}

    def _singleton(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return _singleton
