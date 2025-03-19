import pickle
import sys
import time
import traceback

with open("log.log", "w") as f:
    pass


def sys_break():
    print("================================")
    print("System break")
    log("System break")
    exit(0)


def log(string):
    time_str = time.strftime("%H:%M:%S", time.localtime())
    with open("log.log", "a+") as f:
        f.write(f"{time_str}:  {string} \n")


def log_disk(disk, tag_dict):
    for i in range(1, len(disk)):
        for j in range(1, len(disk[i])):
            if disk[i][j] == -1:
                continue
            obj_tag = tag_dict[disk[i][j]]
            disk[i][j] = obj_tag

    pickle.dump(disk, open("disk.pkl", "wb"))


class Object:
    def __init__(self, id: int, size: int, tag: int):
        self.id = id
        self.size = size
        self.tag = tag


class WritePointer:
    def __init__(self):
        pass


def print_error(e):
    log("===== 捕获到异常 =====")

    log(f"错误类型: {type(e).__name__}")
    log(f"错误信息: {e}")

    log("\n===== traceback.print_exc() 输出 =====")
    traceback.print_exc()

    log("\n===== traceback.format_exc() 输出 =====")
    error_details = traceback.format_exc()
    log(error_details)
    sys_break()
