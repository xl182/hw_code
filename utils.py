import time
import traceback
from global_variables import g

if_online = False


if not if_online:
    with open("generated_files/log.log", "w") as f:
        pass

def sys_break():
    if if_online:
        return
    print("================================")
    print("System break")
    log("System break")
    exit(0)
    

def log(string):
    if if_online:
        return
    time_str = time.strftime("%H:%M:%S", time.localtime())
    with open("generated_files/log.log", "a+") as f:
        f.write(f"{time_str}:  {string} \n")


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
    
    
def log_empty_spaces(empty_spaces):
    # print exist empty spaces in a list in line
    if g.use_write_log:
        log(f"empty spaces:")

    for i in range(1, len(empty_spaces)):  # tag
        for j in range(1, len(empty_spaces[i])):  # size_list
            if empty_spaces[i][j]:
                if g.use_write_log:
                    log(f"tag: {i}, size: {j}, empty spaces: {empty_spaces[i][j]}")


def print_error(e):
    if if_online:
        return
    log("===== 捕获到异常 =====")

    log(f"错误类型: {type(e).__name__}")
    log(f"错误信息: {e}")

    log("\n===== traceback.print_exc() 输出 =====")
    traceback.print_exc()

    log("\n===== traceback.format_exc() 输出 =====")
    error_details = traceback.format_exc()
    log(error_details)
    sys_break()
