import bisect
import sys
import time
import traceback
import logging


if_online = False
use_write_log = False
use_read_log = False


if not if_online:
    logger = logging.basicConfig(
        filename="generated_files/log.log",
        level=logging.DEBUG,
        format="%(asctime)s(%(levelname)s): %(message)s",
        datefmt="%d %H:%M:%S",
        filemode="w",
    )


class AutoSortedList:
    def __init__(self):
        self.obj_id_list = []  # (pos, size, time_stamp, tag) * N
        self.pos_list = []  # pos * N

    def insert(self, pos, obj_id):
        # Insert into data_list based on pos (value[0])
        if pos in self.pos_list:
            return

        # Find the insertion index for data_list
        index = bisect.bisect_left(self.pos_list, pos)
        # Insert into pos_list
        self.pos_list.insert(index, pos)
        # Insert into id_list
        self.obj_id_list.insert(index, obj_id)

    def remove(self, index):
        """reomve value by data_list

        Args:
            value (_type_): _description_

        Raises:
            ValueError: _description_
        """
        # Find the index of the value in pos_list
        # Ensure the value exists at the found index
        del self.pos_list[index]
        del self.obj_id_list[index]


def sys_break():
    if if_online:
        return
    print("================================")
    print("System break")
    exit(0)


CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20


def log(string, if_output=False, mode=logging.INFO, new_line=False, c_frame=None):
    if if_online or (not use_read_log) and (not if_output):
        return
    if new_line:
        logging.log(INFO, "\n")

    if c_frame:
        logging.log(mode, f"line({c_frame.f_lineno}): {string}")
    else:
        logging.log(mode, string)


def log_disk(disk, tag_dict):
    for i in range(1, len(disk)):
        for j in range(1, len(disk[i])):
            if disk[i][j] == -1:
                continue
            obj_tag = tag_dict[disk[i][j]]
            disk[i][j] = obj_tag
    if if_online:
        return

    import pickle

    pickle.dump(disk, open("generated_files/disk.pkl", "wb"))


def print_error(e):
    if if_online:
        return
    error_stack = traceback.format_exc()
    log("[Traceback 输出]")
    log(error_stack)

    exc_type, exc_value, exc_traceback = sys.exc_info()
    log("\n[sys.exc_info() 输出]")
    if exc_type:
        log(f"异常类型: {exc_type.__name__}")
    log(f"错误信息: {exc_value}")
    log(f"Traceback 对象: {traceback.format_tb(exc_traceback)[0]}")
    sys_break()


class RecordTimer:
    def __init__(self):
        self.end_time = 0
        self.start_time = 0
        self.time_list = [0.0 for _ in range(20)]
        self.annotations = {}
        self.time_index = 1

    def init_timer(self):
        self.end_time = time.time()
        self.time_list = [0.0 for _ in range(20)]

    def set_start_time(self):
        self.start_time = time.time()

    def record_time(self, annotation=""):
        if annotation not in self.annotations.keys():
            self.time_index += 1
            self.annotations[annotation] = self.time_index
            index = self.time_index
        else:
            index = self.annotations[annotation]
        self.end_time = time.time()
        self.time_list[index] += self.end_time - self.start_time
        self.end_time = self.start_time

    def log_time(self):
        for annotation, time_index in self.annotations.items():
            if self.time_list[time_index] == 0:
                continue
            log(f"{annotation}, cost time: {self.time_list[time_index]}", if_output=True)
        log("\n", if_output=True)


rt: RecordTimer = RecordTimer()
