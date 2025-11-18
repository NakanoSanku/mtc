from abc import ABC, abstractmethod
from typing import List, Tuple


class Touch(ABC):
    @abstractmethod
    def click(self, x: int, y: int, duration: int = 100):
        """
        点击某个坐标
        :param x: x
        :param y: y
        :param duration: 持续时间. Defaults to 100ms
        :return:
        """

    @abstractmethod
    def swipe(self, points: List[Tuple[int, int]], duration: int = 500):
        """
        模拟手势(滑动)
        :param points: list[Point(x,y)] 坐标点列表
        :param duration: 持续时间. Defaults to 500ms
        :return:
        """
