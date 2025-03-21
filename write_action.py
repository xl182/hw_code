from output import *
from get_in import *
from algorithm import *
from utils import *
from global_variables import g


def write_method_1(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use the same size space that belongs to the same tag
    ensure left_copy_num == 0

    Args:
        obj_id (int): id
        obj_size (int): size
        obj_tag (int): tag
        wo (WriteObjetc): wo
    """
    if not g.empty_spaces[obj_tag][obj_size]:
        return left_copy_num

    # copy: size, index, pointer
    if g.use_write_log:
        log(f"write method 1")
        log_empty_spaces(g.empty_spaces)
    copys = g.empty_spaces[obj_tag][obj_size].pop()

    for c in range(1, g.COPY_NUM + 1):
        wo.disk_serial[c] = copys[c - 1][3]
        wo.position[c] = copys[c - 1][2]

        left_copy_num -= 1
        if left_copy_num == 0:
            return left_copy_num

    return left_copy_num


def write_method_2(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use pre-allocated space, change the bound
    """
    if left_copy_num == 0:
        return left_copy_num
    
    use_method_2 = False
    for c in range(1, g.COPY_NUM+1):
        if g.write_bounds[obj_tag][c][0] + obj_size > g.write_bounds[obj_tag][c][1]:
            continue
        
        index = g.write_index[obj_tag][c]
        if index in wo.disk_serial:
            continue
        
        use_method_2 = True
        copy_serial = g.COPY_NUM - left_copy_num + 1
        position = g.write_bounds[obj_tag][c][0]

        g.write_bounds[obj_tag][c][0] += obj_size
        g.left_allocate_sizes[index] -= obj_size
        
        wo.disk_serial[copy_serial] = index
        wo.position[copy_serial] = position
        
        left_copy_num -= 1
        if left_copy_num == 0:
            if g.use_write_log and use_method_2:
                log(f"write method 2")
            return left_copy_num
        
    if g.use_write_log and use_method_2:
        log(f"write method 2")
    if g.use_write_log:
        log(f"2 left_copy_num: {left_copy_num}")
    return left_copy_num


def write_method_3(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use the empty space (released) that is larger than the object size
    ensure left_copy_num = 0
    Returns:
        exist_enough_space(bool): 
    """
    # use other empty space
    if left_copy_num != 3:
        return left_copy_num
    
    use_method_3 = False
    for i in range(len(g.empty_spaces[obj_tag]) - 1, obj_size, -1):
        if not g.empty_spaces[obj_tag][i]:
            continue
        use_method_3 = True
        copys = g.empty_spaces[obj_tag][i].pop()

        tmp_list = []
        for c in range(1, g.COPY_NUM + 1):
            wo.disk_serial[c] = copys[c - 1][3]
            wo.position[c] = copys[c - 1][2]

            copys[c - 1][1] -= obj_size  # space used, left size
            copys[c - 1][2] += obj_size  # position increased
            
            tmp_list.append(copys[c - 1])
            left_copy_num -= 1
            if left_copy_num == 0:
                return left_copy_num
            
        if copys[-1][1]:
            if g.use_write_log:
                log(f"current id: {obj_id}, current size: {obj_size}, current tag: {obj_tag}")
                log(f"add empty spaces: {tmp_list}")
            g.empty_spaces[obj_tag][copys[-1][1]].append(tmp_list)
        break
    
    if use_method_3 and g.use_write_log:
        log("write_method 3")
        log("out of bound use former empty space or other spaces")
        log_empty_spaces(g.empty_spaces)
    return left_copy_num


def write_method_4(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use pre public space of this tags

    Args:
        left_copy_num (_type_): _description_
        obj_id (_type_): _description_
        obj_size (_type_): _description_
        obj_tag (_type_): _description_
        wo (_type_): _description_

    Returns:
        _type_: _description_
    """
    if left_copy_num == 0:
        return left_copy_num
    
    if g.use_write_log:
        log(f"write method 4")
        log(f"left_copy_num: {left_copy_num}")
        log(f"obj_tag: {obj_tag}, obj id: {obj_id}, obj_size: {obj_size} left copy num: {left_copy_num}")
        
    for i in g.tag_assignments[obj_tag][1:]:
        if i in wo.disk_serial:
            continue
        assign_pos = g.disk_assignments[i].index(obj_tag)
        copy_serial = g.COPY_NUM - left_copy_num + 1
        if g.use_write_log:
            log(f"index: {i}, {g.public_bounds[i][assign_pos]}: {g.public_bounds[i][assign_pos-1]}, ")
        
        if g.public_bounds[i][assign_pos][0] + obj_size <= g.public_bounds[i][assign_pos][1]:
            postion = g.public_bounds[i][assign_pos][0]
            index = i
            g.public_bounds[i][assign_pos][0] += obj_size
            
        elif g.public_bounds[i][assign_pos-1][0] + obj_size <= g.public_bounds[i][assign_pos-1][1]:
            postion = g.public_bounds[i][assign_pos-1][1] - obj_size
            index = i
            g.public_bounds[i][assign_pos-1][1] -= obj_size
        else:
            continue
        
        wo.disk_serial[copy_serial] = index
        wo.position[copy_serial] = postion
        g.left_public_sizes[index] -= obj_size
        
        left_copy_num -= 1
        if left_copy_num == 0:
            if g.use_write_log:
                log(f"method 4: left_copy_num: {left_copy_num}")
            return left_copy_num
    if g.use_write_log:
        log(f"4 left_copy_num: {left_copy_num}")
    return left_copy_num


def write_method_5(left_copy_num, obj_id, obj_size, obj_tag, wo):
    # use the pre allocated space (other tag) that is related to this tag
    if left_copy_num == 0:
        return left_copy_num
    
    if g.use_write_log:
        log(f"write method 5")
        log(f"obj_tag: {obj_tag}, obj id: {obj_id}, obj_size: {obj_size} left copy num: {left_copy_num}")
        
    for i in range(1, g.N + 1):
        if not g.obj_relation[i][obj_tag]:
            continue
        
        if i in wo.disk_serial:
            continue
        
        copy_serial = g.COPY_NUM - left_copy_num + 1
        
        if g.use_write_log:
            left_tag, right_tag = g.obj_relation[i][obj_tag]
            log(f"left tag: {left_tag}, right tag: {right_tag}")
            log(f"left tag bounds: {g.write_bounds[left_tag]}")
            log(f"right tag bounds: {g.write_bounds[right_tag]}")

        left_tag, right_tag = g.obj_relation[i][obj_tag]
        left_copy_serial = g.tag_assignments[left_tag].index(i)
        right_copy_serial = g.tag_assignments[right_tag].index(i)

        index, position = -1, -1
        if (g.write_bounds[left_tag][left_copy_serial][0] + obj_size <= g.write_bounds[left_tag][left_copy_serial][1]):
            if g.tag_assignments[i][-1] == left_tag:
                continue
            index = i
            position = g.write_bounds[left_tag][left_copy_serial][1] - obj_size
            g.write_bounds[left_tag][left_copy_serial][1] -= obj_size
            
        elif (g.write_bounds[right_tag][right_copy_serial][0] + obj_size <= g.write_bounds[right_tag][right_copy_serial][1]):
            if g.tag_assignments[i][1] == right_tag:
                continue
            index = i
            position = g.write_bounds[right_tag][right_copy_serial][0]
            g.write_bounds[right_tag][right_copy_serial][0] += obj_size
        else:
            continue
        
        wo.disk_serial[copy_serial] = index
        wo.position[copy_serial] = position
        g.left_allocate_sizes[index] -= obj_size
        
        left_copy_num -= 1
        if left_copy_num == 0:
            if g.use_write_log: log(f"5 left_copy_num: {left_copy_num}")
            return left_copy_num
        
    if g.use_write_log: log(f"5 left_copy_num: {left_copy_num}")
    return left_copy_num


def write_method_6(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use pre allocated spaces of other tags that is not related to this tag

    Args:
        left_copy_num (_type_): _description_
        obj_id (_type_): _description_
        obj_size (_type_): _description_
        obj_tag (_type_): _description_
        wo (_type_): _description_

    Returns:
        _type_: _description_
    """
    if left_copy_num == 0:
        return left_copy_num
    
    if g.use_write_log:
        log(f"write method 6")
        log(f"obj_tag: {obj_tag}, obj id: {obj_id}, obj_size: {obj_size} left copy num: {left_copy_num}")
        log(f"left_copy_num: {left_copy_num}")
        

    if max(g.left_allocate_sizes) < obj_size:
        return left_copy_num

    top_indices = sorted(range(len(g.left_allocate_sizes)), key=lambda i: g.left_allocate_sizes[i], reverse=True)
    if g.use_write_log:
        log(f"obj_id: {obj_id}")
        log(f"free spaces: {g.left_allocate_sizes}")
        log(f"top indices: {top_indices}")
        
    for i in top_indices:
        # i : volume index
        if i in wo.disk_serial or i == 0:
            continue
        copy_serial = g.COPY_NUM - left_copy_num + 1

        diff_list = [0 for _ in range(len(g.disk_assignments[i]))]
        tag_list = g.disk_assignments[i]  # tag list in this volume
        
        for t, tag in enumerate(tag_list[1:]):
            tag_copy_serial = g.tag_assignments[tag].index(i)
            diff_list[t+1] = g.write_bounds[tag][tag_copy_serial][1] - g.write_bounds[tag][tag_copy_serial][0]
        
        if max(diff_list) < obj_size:
            return left_copy_num
        
        top_tag_index = diff_list.index(max(diff_list))  # the index of max_size
        tag = tag_list[top_tag_index]
        tag_copy_serial = g.tag_assignments[tag].index(i)
        
        if g.use_write_log:
            log(f"tag_list: {tag_list}")
            log(f"diff_list: {diff_list}")
            log(f"tag: {tag}, tag_copy_serial: {tag_copy_serial}")
            log(f"tag bounds: {g.write_bounds[tag]}")
        
        wo.disk_serial[copy_serial] = i
        wo.position[copy_serial] = g.write_bounds[tag][tag_copy_serial][0]
        g.write_bounds[tag][tag_copy_serial][0] += obj_size
        g.left_allocate_sizes[i] -= obj_size
        
        left_copy_num -= 1
        if left_copy_num == 0:
            return left_copy_num
        
    return left_copy_num
        
        
def write_method_7(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use public space of other tags that is not related to this tag

    Args:
        left_copy_num (_type_): _description_
        obj_id (_type_): _description_
        obj_size (_type_): _description_
        obj_tag (_type_): _description_
        wo (_type_): _description_

    Returns:
        _type_: _description_
    """
    if left_copy_num == 0:
        return left_copy_num
    
    if g.use_write_log:
        log(f"write method 7")
        log(f"obj_tag: {obj_tag}, obj id: {obj_id}, obj_size: {obj_size} left copy num: {left_copy_num}")
    
    public_bounds_sizes = [[0 for j in range(len(g.public_bounds[i]))] for i in range(g.N+1)]
    public_bounds_size_sum = [0 for i in range(g.N+1)]
    for i in range(1, g.N+1):
        for j in range(1, len(g.public_bounds[i])):
            public_bounds_sizes[i][j] += g.public_bounds[i][j][-1] - g.public_bounds[i][j][0]
        public_bounds_size_sum[i] = sum(public_bounds_sizes[i])
    top_indices = sorted(range(1, g.N+1), key=lambda i: public_bounds_size_sum[i], reverse=True)
    
    if g.use_write_log:
        log(f"public bounds sizes: {public_bounds_sizes}")
        log(f"public_bounds_size_sum: {public_bounds_size_sum}")
    
    for i in top_indices:
        if i in wo.disk_serial:
            continue
        
        if max(public_bounds_sizes[i]) < obj_size:
            continue
        
        copy_serial = g.COPY_NUM - left_copy_num + 1
        
        index = public_bounds_sizes[i].index(max(public_bounds_sizes[i]))
        position = g.public_bounds[i][index][0]
        
        wo.disk_serial[copy_serial] = i
        wo.position[copy_serial] = position
        g.public_bounds[i][index][0] += obj_size
        g.left_public_sizes[i] -= obj_size
        
        left_copy_num -= 1
        if left_copy_num == 0:
            if g.use_write_log:
                log(f"7 left_copy_num: {left_copy_num}")
            return left_copy_num
    if g.use_write_log:
        log(f"7 left_copy_num: {left_copy_num}")
    return left_copy_num


def write_method_8(left_copy_num, obj_id, obj_size, obj_tag, wo):
    """use empty spaces of other tags

    Args:
        left_copy_num (_type_): _description_
        obj_id (_type_): _description_
        obj_size (_type_): _description_
        obj_tag (_type_): _description_
        wo (_type_): _description_
    """
    if left_copy_num == 0:
        return left_copy_num
    
    if g.use_write_log:
        log(f"write method 8")
        log(f"obj_tag: {obj_tag}, obj id: {obj_id}, obj_size: {obj_size} left copy num: {left_copy_num}")
        
    if g.use_write_log:
        log("use empty spaces of other tags of same size")
    for t in range(1, 1+g.M):
        # t : tag
        if t == obj_tag:
            continue
        if not g.empty_spaces[t][obj_size]:
            continue
        
        copys = g.empty_spaces[t][obj_size].pop()
        for c in range(1, g.COPY_NUM + 1):
            copy_serial = g.COPY_NUM - left_copy_num + 1
            index, position = copys[c - 1][3], copys[c - 1][2]
            
            if index in wo.disk_serial or left_copy_num == 0:
                g.free_empty_spaces[index][obj_size].append(copys[c - 1])
                continue
            
            wo.disk_serial[copy_serial] = index
            wo.position[copy_serial] = position
            left_copy_num -= 1
            
        if left_copy_num == 0:
            if g.use_write_log:
                log(f"left_copy_num: {left_copy_num}")
            return left_copy_num
        
    if g.use_write_log:
        log("use larger empty spaces")
        log_empty_spaces(g.empty_spaces)
        
    for t in range(1, 1+g.M):
        # t : tag
        if t == obj_tag:
            continue

        copy_serial = g.COPY_NUM - left_copy_num + 1
        for s in range(g.MAX_OBJ_SIZE - 1, obj_size, -1):
            if not g.empty_spaces[t][s]:
                continue
            copys = g.empty_spaces[t][s].pop()

            for c in range(1, g.COPY_NUM + 1):
                index, position = copys[c - 1][3], copys[c - 1][2] # type: ignore
                
                if left_copy_num == 0 or index in wo.disk_serial:
                    free_empty_spaces[index][copys[c - 1][1]].append(copys[c - 1]) # type: ignore
                    continue
                
                wo.disk_serial[copy_serial] = index
                wo.position[copy_serial] = position

                copys[c - 1][1] -= obj_size  # type: ignore # space used, left size
                copys[c - 1][2] += obj_size  # type: ignore # position increased
                free_empty_spaces[index][copys[c - 1][1]].append(copys[c - 1]) # type: ignore
                
                left_copy_num -= 1
    if g.use_write_log:
        log(f"left_copy_num: {left_copy_num}")
    return left_copy_num


def do_write_object(obj_id, obj_size, obj_tag):
    wo = WriteOutput(obj_id, obj_size)
    left_copy_num = 3

    g.write_dict[obj_id] = []  # position, index
    # use released space first

    left_copy_num = write_method_1(left_copy_num, obj_id, obj_size, obj_tag, wo)
    left_copy_num = write_method_2(left_copy_num, obj_id, obj_size, obj_tag, wo)
    left_copy_num = write_method_3(left_copy_num, obj_id, obj_size, obj_tag, wo)
    left_copy_num = write_method_4(left_copy_num, obj_id, obj_size, obj_tag, wo)
    left_copy_num = write_method_6(left_copy_num, obj_id, obj_size, obj_tag, wo)
    left_copy_num = write_method_7(left_copy_num, obj_id, obj_size, obj_tag, wo)
    left_copy_num = write_method_8(left_copy_num, obj_id, obj_size, obj_tag, wo)
    
    for i in range(1, g.COPY_NUM + 1):
        index, position = wo.disk_serial[i], wo.position[i]
        g.write_dict[obj_id].append([obj_tag, obj_size, position, index])
    wo.print_info(g.disk)
    
    if left_copy_num:
        log_disk(g.disk, g.tag_dict)
        log(f"remaining copy num: {left_copy_num}")
        sys_break()
    
    if g.use_write_log:
        log(f"write id: {obj_id}, write size: {obj_size}, write tag: {obj_tag}, index: {wo.disk_serial}, position: {wo.position}")


def write_action():
    write_obj = write_input()
    for i in range(len(write_obj)):
        obj_id, obj_size, obj_tag = write_obj[i]
        g.tag_dict[obj_id] = obj_tag
        do_write_object(obj_id, obj_size, obj_tag)
