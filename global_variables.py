from re import L
from typing import Any, List
from demos.python.main import MAX_OBJECT_NUM
from utils import AutoSortedList, log


class GlobalVariables:
    # init
    COPY_NUM = 3
    MAX_OBJECT_NUM = 100000 + 1
    MAX_REQUEST_NUM = 30000000 + 1  # maximum number of requests
    EXTRA_TIME = 105

    SCORE_THRESHOLD = 0.1
    JUMP = 1
    PASS = 2
    READ = 3

    BASE_READ_COST = 64

    def __init__(self):
        self.use_write_log = False

        self.tag_assignments: Any  # [volume index] the assignments of each tag
        self.disk_assignments: Any  # [tag] the assignments of each disk

        self.disk: List

        self.delete_info: list
        self.write_info: list
        self.read_info: list

        self.write_bounds: List[List[List[int]]]  # [[left_bound, right_bound] * 3] * M
        self.write_index: List[List[int]]  # [volume_index * 3] * M

        self.write_dict: List[List[List[int]]]  # [obj_tag, obj_size, position, index]

        self.empty_spaces: List[List[List[int]]]  # [(size, disk, pointer)] * M
        self.obj_relation: List[List[List[int]]]  # [[[left tag, right tag] * tag] * N]
        # [[[size, [left pointer, right pointer], [left tag, right tag,] [left bound, right bound]] * tag] * N]
        self.free_empty_spaces: Any  # [(size, disk, pointer)] * M
        self.public_bounds: List[List[List[int]]]  # [left bound, right bound] * ? * ?
        self.public_sizes: List[List[int]]
        self.left_allocate_sizes: List[int]  # the free allocate space of each volume
        self.left_public_sizes: List[int]  # the free public space of each volume

        self.tag_max_obj_size = []
        self.volume_max_obj_size = []

        self.current_timestamp = -1
        self.T = -1  # timestamps
        self.M = -1  # tag numbers
        self.N = -1  # volume numbers
        self.V = -1  # volume
        self.G = -1  # tokens

        self.write_dict = [
            [] for i in range(self.MAX_OBJECT_NUM)
        ]  # [obj_tag, obj_size, position, index]

        self.tag_dict = {}
        self.current_neddle: List[int]
        self.request_data_list: List[AutoSortedList]  # [obj_id] * MAX_REQUEST_NUM id
        self.last_read_cost: List[int]
        self.if_last_read: List[bool]
        self.volume_locked: List[bool]
        self.waiting_reading_area: List[int]
        self.left_read_size: List[int]
        self.left_pass_size: List[int]
        self.current_read_obj: List[int]
        self.request_id_dict = [[] for j in range(MAX_OBJECT_NUM + 1)]
        self.new_id_dict = [[] for j in range(MAX_OBJECT_NUM + 1)]
        self.next_position: List[int]
        self.obj_size: List[int]

        self.read_obj_blocks: List[int] = [0 for _ in range(MAX_OBJECT_NUM + 1)]
        self.new_obj_blocks: List[int] = [0 for _ in range(MAX_OBJECT_NUM + 1)]
        self.read_disk_obj: List[List[int]]


def init_variables(T, M, N, V, G, gv: GlobalVariables):
    if gv.use_write_log:
        log(f"T, M, N, V, G: {T, M, N, V, G}")

    gv.tag_max_obj_size = [10 for _ in range(gv.M + 1)]
    gv.volume_max_obj_size = [10 for _ in range(gv.N + 1)]

    gv.disk = [[-1 for j in range(V + 1)] for i in range(N + 1)]  # init disk
    gv.empty_spaces = [
        [[] for i in range(gv.tag_max_obj_size[t])] for t in range(M + 1)
    ]  # [[[] * size] * M + 1]

    gv.write_index = [
        [0 for _ in range(gv.COPY_NUM + 1)] for i in range(M + 1)
    ]  # volume index of each tag
    gv.write_bounds = [[[-1, -1] for j in range(gv.COPY_NUM + 1)] for i in range(M + 1)]
    # the used space of each volume
    gv.obj_relation = [[[] for j in range(M + 1)] for i in range(N + 1)]

    gv.free_empty_spaces = [
        [[] for j in range(gv.volume_max_obj_size[i])] for i in range(N + 1)
    ]
    gv.left_allocate_sizes = [0 if i != 0 else 0 for i in range(N + 1)]
    gv.left_public_sizes = [0 if i != 0 else 0 for i in range(N + 1)]

    gv.current_neddle = [1 for _ in range(gv.N + 1)]  # [current postition] * N
    gv.request_data_list = [
        AutoSortedList() for _ in range(gv.N + 1)
    ]  # [postition] * N

    gv.last_read_cost = [gv.BASE_READ_COST for _ in range(gv.N + 1)]
    gv.if_last_read = [False for _ in range(gv.N + 1)]
    gv.volume_locked = [False for _ in range(gv.N + 1)]
    gv.left_read_size = [0 for _ in range(gv.N + 1)]
    gv.left_pass_size = [0 for _ in range(gv.N + 1)]
    gv.current_read_obj = [0 for _ in range(gv.N + 1)]
    gv.next_position = [0 for _ in range(gv.N + 1)]
    gv.read_disk_obj = [[0 for j in range(V + 1)] for i in range(N + 1)]
    gv.obj_size = [0 for _ in range(MAX_OBJECT_NUM + 1)]


g = GlobalVariables()
