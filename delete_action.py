from get_in import delete_input
from output import print_abort
from utils import *
from global_variables import g


def do_delete_object(delete_objs_id):
    for obj_id in delete_objs_id:
        copys = g.write_dict[obj_id]
        for copy in copys:
            tag, size, pos, index = copy
            for s in range(size):
                g.disk[index][pos + s] = -1
            
        tag, size, pos, index = copys[0]
        g.empty_spaces[tag][size].append(copys)
        g.write_dict[obj_id] = []
        if g.use_write_log:
            log(f"delete current id: {obj_id}")
            log(f"add empty spaces: {copys}")
            log(f"delete finished (id: {obj_id})(tag: {g.tag_dict[obj_id]}): {g.write_dict[obj_id]}")
        log_empty_spaces(g.empty_spaces)


def delete_action():
    n_delete, delete_obj_id = delete_input()

    # abort read request id
    abort_request_id = []
    for obj_id in delete_obj_id:
        abort_request_id.extend(g.read_requests[obj_id])

    # delete objects
    if n_delete != 0:
        do_delete_object(delete_obj_id)

    print_abort(abort_request_id)
