import os
import socket
import subprocess
import time

from adbutils import adb, adb_path
from loguru import logger
from mtc.touch import Touch
from mtc.utils import CommandBuilder, str2byte

# MiniTouch
WORK_DIR = os.path.dirname(__file__)
DEFAULT_HOST = "127.0.0.1"
DEFAULT_BUFFER_SIZE = 0
MINITOUCH_PATH = "{}/bin/minitouch/libs".format(WORK_DIR)
MINITOUCH_REMOTE_PATH = "/data/local/tmp/minitouch"
MINITOUCH_REMOTE_ADDR = "localabstract:minitouch"
MINITOUCH_SERVER_START_DELAY = 1
ADB_EXECUTOR = adb_path()


class MiniTouchUnSupportError(Exception):
    pass


class ADBDeviceUnFound(Exception):
    pass


class MiniTouch(Touch):
    def __init__(self, serial: str) -> None:
        """
        __init__ minitouch点击方式

        Args:
            serial (str): 设备id
        """
        self.minitouch_process = None  # minitouch服务进程
        self.minitouch_port = None  # Socket端口记录
        self.pid = None  # minitouch服务pid记录
        if serial not in [device.serial for device in adb.device_list()]:
            raise ADBDeviceUnFound("设备不存在，请检查是否连接设备成功")
        self.__adb = adb.device(serial)  # adb设备

        self.__get_device_info()  # 获取设备信息
        self.__minitouch_install()  # 安装minitouch
        self.__kill_minitouch_server()  # 终止设备上正在运行的minitouch服务

        self.start()  # 启动minitouch

    def __start_minitouch_server(self):
        """启动安卓设备Minitouch Server"""
        command_list = [
            ADB_EXECUTOR,
            "-s",
            self.__adb.serial,
            "shell",
            "/data/local/tmp/minitouch",
        ]
        # 如果minitouch进程没有运行
        if self.minitouch_process is None:
            logger.info("start minitouch: {}".format(" ".join(command_list)))
            self.minitouch_process = subprocess.Popen(
                command_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        time.sleep(MINITOUCH_SERVER_START_DELAY)  # 等待Minitouch启动完成
        self.minitouch_port = self.__adb.forward_port(MINITOUCH_REMOTE_ADDR)  # 转发端口
        # TODO 检查minitouch是否可用

    def __connect_minitouch_by_socket(self):
        """使用TCP连接minitouch"""
        # build connection
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((DEFAULT_HOST, self.minitouch_port))  # 连接转发的端口
        self.client = client
        # get minitouch server info
        socket_out = client.makefile()
        # v <version>
        # protocol version, usually it is 1. needn't use this
        socket_out.readline()
        # ^ <max-contacts> <max-x> <max-y> <max-pressure>
        _, self.max_contacts, self.max_x, self.max_y, self.max_pressure, *_ = (
            socket_out.readline().replace("\n", "").replace("\r", "").split(" ")
        )

        # $ <pid>
        _, self.pid = (
            socket_out.readline().replace("\n", "").replace("\r", "").split(" ")
        )
        logger.info(
            "minitouch running on port: {}, pid: {}".format(
                self.minitouch_port, self.pid
            )
        )
        logger.info(
            "max_contact: {}; max_x: {}; max_y: {}; max_pressure: {}".format(
                self.max_contacts, self.max_x, self.max_y, self.max_pressure
            )
        )

    def __disconnect_minitouch_socket(self):
        """关闭Socket连接"""
        self.client and self.client.close()
        self.client = None
        logger.info("minitouch disconnected")

    def send(self, content):
        """send message to minitouch server"""
        byte_content = str2byte(content)
        self.client.sendall(byte_content)

    def __kill_minitouch_server(self):
        if self.minitouch_process and self.minitouch_process.poll() is None:
            self.minitouch_process.kill()
            self.minitouch_process = None
        if self.pid is None:
            self.pid = self.__adb.shell(["pidof", "minitouch"]).strip()
        if self.pid:
            self.__adb.shell(["kill", self.pid])
            self.pid = None

    def __get_device_info(self):
        """获取设备信息"""
        self.__abi = self.__adb.getprop("ro.product.cpu.abi")  # 获取设备架构
        self.__sdk = self.__adb.getprop("ro.build.version.sdk")  # 获取设备sdk
        self.__orientation = self.__adb.rotation()  # 屏幕方向获取
        self.__window_size = self.__adb.window_size()
        self.__width = self.__window_size.width
        self.__height = self.__window_size.height
        logger.debug(
            f"\n屏幕方向:{self.__orientation}\n屏幕宽度:{self.__width}\n屏幕高度:{self.__height}"
        )

    def __minitouch_install(self):
        self.__adb.sync.push(
            f"{MINITOUCH_PATH}/{self.__abi}/minitouch", MINITOUCH_REMOTE_PATH
        )
        self.__adb.shell(f"chmod +x {MINITOUCH_REMOTE_PATH}")

    def start(self):
        """启动minitouch服务"""
        # 启动minitouch Server
        self.__start_minitouch_server()
        # 构建tcp连接socket
        self.__connect_minitouch_by_socket()

    def stop(self):
        """停止minitouch服务"""
        # 关闭TCP连接
        self.__disconnect_minitouch_socket()
        # 终止minitouch服务
        self.__kill_minitouch_server()

    def __tap(self, points, pressure=100, duration=None, no_up=None):
        """
        tap on screen, with pressure/duration

        :param points: list, looks like [(x1, y1), (x2, y2)]
        :param pressure: default == 100
        :param duration:
        :param no_up: if true, do not append 'up' at the end
        :return:
        """
        if not points:
            return
        points = [self.__convert(point[0], point[1]) for point in points]
        points = [list(map(int, each_point)) for each_point in points]

        _builder = CommandBuilder()
        for point_id, each_point in enumerate(points):
            x, y = each_point
            _builder.down(point_id, x, y, pressure)
        _builder.commit()

        # apply duration
        if duration:
            _builder.wait(duration)
            _builder.commit()

        # need release?
        if not no_up:
            for each_id in range(len(points)):
                _builder.up(each_id)

        _builder.publish(self)

    def __swipe(self, points, pressure=100, duration=None, no_down=None, no_up=None):
        """
        swipe between points, one by one

        :param points: [(400, 500), (500, 500)]
        :param pressure: default == 100
        :param duration:
        :param no_down: will not 'down' at the beginning
        :param no_up: will not 'up' at the end
        :return:
        """
        if not points:
            return
        points = [self.__convert(point[0], point[1]) for point in points]
        points = [list(map(int, each_point)) for each_point in points]

        _builder = CommandBuilder()
        point_id = 0

        # tap the first point
        if not no_down:
            x, y = points.pop(0)
            _builder.down(point_id, x, y, pressure)
            _builder.publish(self)

        # start swiping
        for each_point in points:
            x, y = each_point
            _builder.move(point_id, x, y, pressure)

            # add delay between points
            if duration:
                _builder.wait(duration)
            _builder.commit()

        _builder.publish(self)

        # release
        if not no_up:
            _builder.up(point_id)
            _builder.publish(self)

    def __convert(self, x, y):
        if self.__orientation == 0:
            pass
        elif self.__orientation == 1:
            x, y = self.__height - y, x
        elif self.__orientation == 2:
            x, y = self.__width - x, self.__height - y
        elif self.__orientation == 3:
            x, y = y, self.__width - x
        return x, y

    def click(self, x: int, y: int, duration: int = 100) -> None:
        self.__tap([(x, y)], duration=duration)

    def swipe(self, points: list, duration: int = 300) -> None:
        if len(points) < 2:
            return
        self.__swipe(points, duration=duration / (len(points) - 1))

    def __del__(self):
        try:
            self.stop()
        except Exception:
            # best-effort cleanup
            pass
