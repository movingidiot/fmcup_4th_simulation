from threading import Lock

from Singleton import singleton


@singleton
class InfoLock(object):
    """
    Info类互斥锁
    """
    def __init__(self):
        self.lock = Lock()


@singleton
class SpeedCacheLock(object):
    """
    分离皮带速度缓存互斥锁
    """
    def __init__(self):
        self.lock = Lock()

