import sys
from global_variables import g
from utils import log


class WriteOutput(object):
    def __init__(self, obj_id, obj_size):
        self.write_id = obj_id
        self.disk_serial = [-1 for i in range(0, g.COPY_NUM + 1)]
        self.position = [-1 for i in range(0, g.COPY_NUM + 1)]
        self.size = obj_size

    def record_disk(self, disk, obj_id, obj_size, index, position):
        for s in range(obj_size):
            disk[index][position + s] = obj_id

    def print_info(self, disk, use_log=False):
        print(self.write_id)

        for i in range(1, g.COPY_NUM + 1):
            print(self.disk_serial[i], end="")
            for j in range(self.size):
                print(f" {self.position[i]+j}", end="")
            print()
            self.record_disk(
                disk, self.write_id, self.size, self.disk_serial[i], self.position[i]
            )
        sys.stdout.flush()
        if use_log:
            log(
                f"write {self.write_id} (size: {self.size})to disk {self.disk_serial} at position {self.position}"
            )


class ReadOutput:
    JUMP = "J"
    PASS = "P"
    READ = "R"

    def __init__(self, length):
        self.action_list = [[] for _ in range(length + 1)]
        self.finished_request = []

    def add_jump(self, index, pos):
        self.action_list[index] = [self.JUMP, pos]

    def add_read(self, index):
        self.action_list[index].append(self.READ)

    def add_pass(self, index, pos):
        self.action_list[index].extend([self.PASS, pos])

    def add_finished_request(self, request_id):
        self.finished_request.extend(request_id)

    def print_info(self):
        output = []  # Cache output to reduce I/O overhead

        for actions in self.action_list[1:]:  # Skip the first empty list
            jump_found = False
            for i, action in enumerate(actions):
                if action == self.JUMP:
                    output.append(f"j  {actions[i + 1]}\n")
                    jump_found = True
                    break
                elif action == self.PASS:
                    output.append("p" * actions[i + 1])
                elif action == self.READ:
                    output.append("r")
            if not jump_found:  # No JUMP action found in the current actions
                output.append("#\n")

        output.append(f"{len(self.finished_request)}\n")
        for request_id in self.finished_request:
            output.append(f"{request_id}\n")

        sys.stdout.write("".join(output))
        sys.stdout.flush()


def print_abort(abort_request_id):
    print("\n".join([str(len(abort_request_id))] + list(map(str, abort_request_id))))
    sys.stdout.flush()
