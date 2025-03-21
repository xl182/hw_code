import sys
from get_in import read_input
from global_variables import g



def read_action():
    n_read, read_req = read_input()

    for req_id, obj_id in read_req[:n_read]:
        g.read_requests[obj_id].append(req_id)
    for i in range(0, g.N):
        print("#")
    print("0")
    sys.stdout.flush()
