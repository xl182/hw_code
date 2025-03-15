import heapq
import utils

def allocate_files(files, num_folders=10, capacity=5192):
    folder_capacity = capacity * num_folders
    folders = [{'remaining': folder_capacity, 'index': i} for i in range(num_folders)]
    heap = [(-folder_capacity, i) for i in range(num_folders)]
    heapq.heapify(heap)
    
    allocations = {}
    file_details = []
    
    for idx, size in enumerate(sorted(files, reverse=True)):
        file_details.append((idx, size))
    
    for file_id, size in file_details:
        temp_heap = [(-f['remaining'], f['index']) for f in folders]
        heapq.heapify(temp_heap)
        selected = []
        used = set()
        
        while temp_heap and len(selected) < 3:
            rem_neg, idx = heapq.heappop(temp_heap)
            rem = -rem_neg
            if rem >= size and idx not in used:
                selected.append(idx)
                used.add(idx)
        
        if len(selected) >= 3:
            for idx in selected:
                folders[idx]['remaining'] -= size
            allocations[file_id] = {'split': False, 'locations': selected}
            continue
        
        s1 = size / 2
        s2 = size - s1
        if s1 > folder_capacity or s2 > folder_capacity:
            return None
        
        temp_heap_s1 = [(-f['remaining'], f['index']) for f in folders]
        heapq.heapify(temp_heap_s1)
        s1_selected = []
        used_s1 = set()
        
        while temp_heap_s1 and len(s1_selected) < 3:
            rem_neg, idx = heapq.heappop(temp_heap_s1)
            rem = -rem_neg
            if rem >= s1 and idx not in used_s1:
                s1_selected.append(idx)
                used_s1.add(idx)
        
        if len(s1_selected) < 3:
            return None
        
        for idx in s1_selected:
            folders[idx]['remaining'] -= s1
        
        temp_heap_s2 = [(-f['remaining'], f['index']) for f in folders]
        heapq.heapify(temp_heap_s2)
        s2_selected = []
        used_s2 = set()
        
        while temp_heap_s2 and len(s2_selected) < 3:
            rem_neg, idx = heapq.heappop(temp_heap_s2)
            rem = -rem_neg
            if rem >= s2 and idx not in used_s2:
                s2_selected.append(idx)
                used_s2.add(idx)
        
        if len(s2_selected) < 3:
            return None
        
        for idx in s2_selected:
            folders[idx]['remaining'] -= s2
        
        s1_locations = sorted(s1_selected)
        s2_locations = sorted(s2_selected)
        min_diff = float('inf')
        best_s2 = s2_locations
        
        for i in range(len(s2_locations) - 2):
            current = s2_locations[i:i+3]
            diff = sum(abs(current[j] - s1_locations[j]) for j in range(3))
            if diff < min_diff:
                min_diff = diff
                best_s2 = current
        
        allocations[file_id] = {
            'split': True,
            's1': {'size': s1, 'locations': s1_locations},
            's2': {'size': s2, 'locations': best_s2}
        }
    
    for f in folders:
        if f['remaining'] < 0:
            return None
    
    
    assignments = [[0, 0, 0] for i in range(len(files))]
    for file_id, details in allocations.items():
        if details['split']:
            utils.log(f"文件 {file_id} 被拆分为两个部分:")
            utils.log(f"  部分1大小 {details['s1']['size']}, 备份位置: {details['s1']['locations']}")
            utils.log(f"  部分2大小 {details['s2']['size']}, 备份位置: {details['s2']['locations']}")
        else:
            utils.log(f"文件 {file_id} 完整存储，备份位置: {details['locations']}")
            assignments[file_id] = details['locations']
            assignments[file_id] = [_+1 for _ in assignments[file_id]]
    return assignments


def calc_occupy(write_info, delete_info, M):
    max_cost_list = [0 for i in range(M+1)]
    finnal_cost_list = [0 for i in range(M+1)]

    for i in range(1, len(write_info)):
        finnal_cost_list[i] += sum(write_info[i]) - sum(delete_info[i])
        
    occpuy_list = finnal_cost_list
    return occpuy_list
