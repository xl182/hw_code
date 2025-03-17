import heapq
import utils
import time
from collections import deque

def allocate_files(file_sizes, N, V, timeout=1):
    file_sizes.remove(0)
    start_time = time.time()
    folders = [{"capacity": V, "files": []} for _ in range(N)]
    file_queue = deque(sorted(enumerate(file_sizes), key=lambda x: -x[1]))
    split_files = set()
    original_to_parts = {}

    while file_queue and time.time() - start_time < timeout:
        file_id, size = file_queue.popleft()
        
        # 尝试分配原文件
        candidates = sorted([(i, f["capacity"]) for i, f in enumerate(folders)], 
                          key=lambda x: -x[1])
        available = [i for i, cap in candidates if cap >= size]
        
        if len(available) >= 3:
            selected = []
            used = set()
            for fidx in available:
                if len(selected) < 3 and fidx not in used:
                    selected.append(fidx)
                    used.add(fidx)
            if len(selected) == 3:
                for fidx in selected:
                    folders[fidx]["capacity"] -= size
                    folders[fidx]["files"].append(file_id)
                continue
        
        file_sizes.insert(0, 0)
        return None, None
        # 拆分文件
        split_size1 = size // 2
        split_size2 = size - split_size1
        split_files.add(file_id)
        
        # 生成拆分后的部分并加入队列
        part1 = (f"{file_id}_p1", split_size1)
        part2 = (f"{file_id}_p2", split_size2)
        file_queue.appendleft(part2) # type: ignore
        file_queue.appendleft(part1) # type: ignore
        original_to_parts[file_id] = [part1[0], part2[0]]

    # 处理最终分配结果
    allocation = []
    for folder in folders:
        valid_files = []
        for f in folder["files"]:
            if isinstance(f, int) and f not in split_files:
                valid_files.append(f)
            elif str(f).endswith(("_p1", "_p2")):
                original_id = int(f.split("_")[0]) # type: ignore
                if original_id in split_files:
                    valid_files.append(f)
        allocation.append(valid_files)
        
    for i in range(len(allocation)):
        for j in range(len(allocation[i])):
            allocation[i][j] += 1
        allocation[i] = sorted(allocation[i])
        allocation[i].insert(0, None)
    allocation.insert(0, None)
    file_sizes.insert(0, 0)
    return allocation, list(split_files)


def calc_occupy(write_info, delete_info, M):
    max_cost_list = [0 for i in range(M+1)]
    finnal_cost_list = [0 for i in range(M+1)]

    for i in range(1, len(write_info)):
        finnal_cost_list[i] += sum(write_info[i]) - sum(delete_info[i])
        
    cost_tmp = [0 for _ in range(M+1)]
    for i in range(1, len(write_info)):
        for j in range(len(write_info[-1])):
            cost_tmp[i] += write_info[i][j] - delete_info[i][j]
            max_cost_list[i] = max(max_cost_list[i], cost_tmp[i])
    return finnal_cost_list, max_cost_list
