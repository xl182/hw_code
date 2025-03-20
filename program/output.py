import sys
from utils import *

COPY_NUM = 3


class WriteOutput(object):
    def __init__(self, obj_id, obj_size):
        self.write_id = obj_id
        self.disk_serial = [-1 for i in range(0, COPY_NUM + 1)]
        self.position = [-1 for i in range(0, COPY_NUM + 1)]
        self.size = obj_size
    
    def record_disk(self, disk, obj_id, obj_size, index, position):
        for s in range(obj_size):
            disk[index][position + s] = obj_id

    def print_info(self, disk, use_log=False):
        print(self.write_id)
        
        for i in range(1, COPY_NUM + 1):
            print(self.disk_serial[i], end="")
            for j in range(self.size):
                print(f" {self.position[i]+j}", end="")
            print()
            self.record_disk(disk, self.write_id, self.size, self.disk_serial[i], self.position[i])
            
        if use_log:
            log(f"write {self.write_id} (size: {self.size})to disk {self.disk_serial} at position {self.position}")


def print_abort(abort_request_id):
    print('\n'.join([str(len(abort_request_id))] + list(map(str, abort_request_id))))
    sys.stdout.flush()