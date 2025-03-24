import bisect
import sys
import traceback
import logging

if_online = False
use_write_log = True
use_read_log = True


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
        self.data_list = []  # (pos, size, time_stamp, tag) * N
        self.pos_list = []  # pos * N
        self.id_list = []  # id * N

    def insert(self, value):
        # Insert into data_list based on pos (value[0])
        pos, obj_id = value[0], value[2]
        # Find the insertion index for data_list
        index = bisect.bisect_left([x[0] for x in self.data_list], pos)
        self.data_list.insert(index, value)
        # Insert into pos_list
        self.pos_list.insert(index, pos)
        # Insert into id_list
        self.id_list.insert(index, obj_id)

    def remove(self, index):
        """reomve value by data_list

        Args:
            value (_type_): _description_

        Raises:
            ValueError: _description_
        """
        # Find the index of the value in pos_list
        # Ensure the value exists at the found index
        del self.data_list[index]
        del self.pos_list[index]
        del self.id_list[index]


def sys_break():
    if if_online:
        return
    print("================================")
    print("System break")
    log("System break")
    exit(0)


CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20


def log(string, mode=logging.INFO, new_line=False, c_frame=None):
    if if_online or (not use_read_log):
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
