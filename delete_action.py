from get_in import delete_input
from output import print_abort
from utils import log
from global_variables import g


def do_delete_object(delete_objs_id):
    for obj_id in delete_objs_id:
        copys = g.write_dict[obj_id]
        for copy in copys:
            tag, size, pos, index = copy
            for s in range(size):
                g.disk[index][pos + s] = -1
            if obj_id in g.request_data_list[index].obj_id_list:
                obj_index = g.request_data_list[index].obj_id_list.index(obj_id)
                g.request_data_list[index].remove(obj_index)
            if obj_id in g.current_read_obj:
                for i in range(len(g.current_read_obj)):
                    g.current_read_obj[i] = 0
                    g.left_read_size[i] = 0
                    g.left_pass_size[i] = 0

        # enlarge size list of empty spaces
        tag, size, pos, index = copys[0]
        if size > g.tag_max_obj_size[tag]:
            g.tag_max_obj_size[tag] = size
            for _ in range(size, g.tag_max_obj_size[tag]):
                g.empty_spaces[tag].append([])
        if size > g.volume_max_obj_size[index]:
            g.volume_max_obj_size[index] = size
            for _ in range(size, g.volume_max_obj_size[index]):
                g.free_empty_spaces[index].append([])

        g.empty_spaces[tag][size].append(copys)
        g.write_dict[obj_id] = []
        if g.use_write_log:
            log(f"delete current id: {obj_id}")
            log(f"add empty spaces: {copys}")
            log(
                f"delete finished (id: {obj_id})(tag: {g.tag_dict[obj_id]}): {g.write_dict[obj_id]}"
            )


def delete_action():
    n_delete, delete_obj_id = delete_input()

    # abort read request id
    abort_request_id = []
    for obj_id in delete_obj_id:
        abort_request_id.extend(g.request_id_dict[obj_id])
        abort_request_id.extend(g.new_id_dict[obj_id])

    # delete objects
    if n_delete != 0:
        do_delete_object(delete_obj_id)

    print_abort(abort_request_id)
