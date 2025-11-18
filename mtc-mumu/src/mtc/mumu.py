import ctypes
import os
import time
from typing import List, Tuple

from mmumu.api import MuMuApi
from mmumu.base import get_mumu_path

from mtc.touch import Touch


class MuMuTouch(Touch):
    MUMU_API_DLL_PATH = r"\shell\sdk\external_renderer_ipc.dll"
    MUMU_12_5_API_DLL_PATH = r"\nx_device\12.0\shell\sdk\external_renderer_ipc.dll"

    def __init__(
        self,
        instance_index: int,
        emulator_install_path: str = None,
        dll_path: str = None,
        display_id: int = 0,
    ):
        """
        __init__ MumuApi 操作

        基于 /shell/sdk/external_renderer_ipc.dll 实现操作 mumu 模拟器

        Args:
            instance_index (int): 模拟器实例的编号
            emulator_install_path (str): 模拟器安装路径，一般会根据模拟器注册表路径获取. Defaults to None.
            dll_path (str, optional): dll 文件存放路径，一般会根据模拟器路径获取. Defaults to None.
            display_id (int, optional): 显示窗口 id，一般无需填写. Defaults to 0.
        """
        self.display_id = display_id
        self.instance_index = instance_index
        self.emulator_install_path = emulator_install_path or get_mumu_path()

        uninstall_path = os.path.join(self.emulator_install_path, "uninstall.exe")
        if not os.path.exists(uninstall_path):
            raise FileNotFoundError("模拟器安装目录下未找到卸载程序，当前安装路径不正确")

        self.dll_path = dll_path or self.emulator_install_path + self.MUMU_API_DLL_PATH
        if not os.path.exists(self.dll_path):
            self.dll_path = (
                self.emulator_install_path + self.MUMU_12_5_API_DLL_PATH
            )
        if not os.path.exists(self.dll_path):
            raise FileNotFoundError("external_renderer_ipc.dll not found!")

        self.width: int = 0
        self.height: int = 0

        self.nemu = MuMuApi(self.dll_path)
        # 连接模拟器
        self.handle = self.nemu.connect(
            self.emulator_install_path, self.instance_index
        )
        self.get_display_info()

    def get_display_info(self):
        width = ctypes.c_int(0)
        height = ctypes.c_int(0)
        result = self.nemu.capture_display(
            self.handle,
            self.display_id,
            0,
            ctypes.byref(width),
            ctypes.byref(height),
            None,
        )
        if result != 0:
            print("Failed to get the display size.")
            return None
        self.width, self.height = width.value, height.value

    def click(self, x: int, y: int, duration: int = 100):
        self.nemu.input_event_touch_down(self.handle, self.display_id, x, y)
        time.sleep(duration / 1000)
        self.nemu.input_event_touch_up(self.handle, self.display_id)

    def swipe(self, points: List[Tuple[int, int]], duration: int = 500):
        if not points:
            return
        for point in points:
            x, y = point
            self.nemu.input_event_touch_down(self.handle, self.display_id, x, y)
            time.sleep(duration / len(points) / 1000)
        self.nemu.input_event_touch_up(self.handle, self.display_id)

    def __del__(self):
        try:
            self.nemu.disconnect(self.handle)
        except Exception:
            # best-effort cleanup
            pass


if __name__ == "__main__":
    touch = MuMuTouch(0)
    touch.click(100, 100, 10000)
    # touch.swipe([(100, 100), (200, 200), (300, 300)])
