import sys
from utils import *

COPY_NUM = 3


class WriteOutput(object):
    def __init__(self, obj_id, obj_size):
        self.write_id = obj_id
        self.write_disk_serial = [-1 for i in range(0, COPY_NUM + 1)]
        self.write_position = [-1 for i in range(0, COPY_NUM + 1)]
        self.write_size = obj_size

    def print_info(self, use_log=False):
        print(self.write_id)
        
        for i in range(1, COPY_NUM + 1):
            print(self.write_disk_serial[i], end="")
            for j in range(self.write_size):
                print(f" {self.write_position[i]+j}", end="")
            print()
        if use_log:
            log(f"write {self.write_id} (size: {self.write_size})to disk {self.write_disk_serial} at position {self.write_position}")


def print_abort(abort_requests):
    print(len(abort_requests))
    for i in range(len(abort_requests)):
        print(f"{abort_requests[i]}")
    sys.stdout.flush()
