import bisect
import sys
import time
import traceback
import logging


if_online = True
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

import bisect


class OrderedList:
    def __init__(self):
        self._list = []

    def insert(self, value):
        index = bisect.bisect_left(self._list, value)
        if index == len(self._list) or self._list[index] != value:
            bisect.insort_left(self._list, value)

    def delete(self, value):
        index = bisect.bisect_left(self._list, value)
        if index < len(self._list) and self._list[index] == value:
            del self._list[index]

    def find_next_position(self, value):
        index = bisect.bisect_right(self._list, value)
        if index == len(self._list):
            return self._list[0]
        return self._list[index]

    def __contains__(self, value):
        index = bisect.bisect_left(self._list, value)
        return index < len(self._list) and self._list[index] == value

    def __repr__(self):
        return str(self._list)

    def __len__(self):
        return len(self._list)


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
    log("[Traceback]", if_output=True)
    log(error_stack, if_output=True)

    exc_type, exc_value, exc_traceback = sys.exc_info()
    log("\n[sys.exc_info()]", if_output=True)
    if exc_type:
        log(f"{exc_type.__name__}", if_output=True)
    log(f"{exc_value}", if_output=True)
    log(f"Traceback: {traceback.format_tb(exc_traceback)[0]}", if_output=True)
    sys_break()


class RecordTimer:
    def __init__(self):
        self.end_time = 0
        self.start_time = [0.0 for _ in range(20)]
        self.time_list = [0.0 for _ in range(20)]
        self.annotations = {}
        self.time_index = 1

    def get_index(self, annotation=""):
        if annotation not in self.annotations.keys():
            self.time_index += 1
            self.annotations[annotation] = self.time_index
            index = self.time_index
        else:
            index = self.annotations[annotation]
        return index

    def init_timer(self):
        self.end_time = time.time()
        self.time_list = [0.0 for _ in range(20)]

    def set_start_time(self, annotation=""):
        index = self.get_index(annotation)
        self.start_time[index] = time.time()

    def record_time(self, annotation=""):
        index = self.get_index(annotation)
        self.end_time = time.time()
        self.time_list[index] += self.end_time - self.start_time[index]
        self.end_time = self.start_time

    def log_time(self):
        for annotation, time_index in self.annotations.items():
            if self.time_list[time_index] == 0:
                continue
            log(
                f"{annotation}, cost time: {self.time_list[time_index]}", if_output=True
            )
        log("\n", if_output=True)


rt: RecordTimer = RecordTimer()
