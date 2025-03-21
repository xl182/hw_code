from typing import Any, List


class GlobalVariables:
    # init
    COPY_NUM = 3
    MAX_OBJECT_NUM = 100000 + 1
    MAX_REQUEST_NUM = 30000000 + 1  # maximum number of requests
    EXTRA_TIME = 105
    MAX_OBJ_SIZE = 100
    
    def __init__(self):
        self.use_write_log = False
        
        self.tag_assignments: Any  # [volume index] the assignments of each tag
        self.disk_assignments: Any  # [tag] the assignments of each disk

        self.delete_info: list
        self.write_info: list
        self.read_info: list

        self.write_bounds: List[List[List[int]]]  # [[left_bound, right_bound] * 3] * M
        self.write_index: List[List[int]]  # [volume_index * 3] * M

        self.write_dict: List[List[int]]  # [obj_tag, obj_size, position, index]

        self.empty_spaces: List[List[List[int]]]  # [(size, disk, pointer)] * M
        self.obj_relation: List[List[List[int]]]  # [[[left tag, right tag] * tag] * N]
        # [[[size, [left pointer, right pointer], [left tag, right tag,] [left bound, right bound]] * tag] * N]
        self.free_empty_spaces: Any  # [(size, disk, pointer)] * M
        self.public_bounds: List[List[List[int]]]  # [left bound, right bound] * ? * ?
        self.public_sizes: List[List[int]]
        self.left_allocate_sizes: List[int]  # the free allocate space of each volume
        self.left_public_sizes: List[int]  # the free public space of each volume
  
        self.read_requests: List[List[int]]  # [obj_id] * MAX_REQUEST_NUM id
        self.current_needle: List[int]  # [position] * (N + 1)

        self.disk: List

        self.current_timestamp = -1
        self.T = -1  # timestamps
        self.M = -1  # tag numbers
        self.N = -1  # volume numbers
        self.V = -1  # volume
        self.G = -1  # tokens

        self.write_dict = [[] for i in range(self.MAX_OBJECT_NUM)]  # [obj_tag, obj_size, position, index]
        self.read_requests = [[] for _ in range(self.MAX_REQUEST_NUM)]
        self.tag_dict = {}


g = GlobalVariables()
