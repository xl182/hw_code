import sys
from utils import log, log_disk, if_online, rt
from global_variables import g

specific_timestamp = [i for i in range(0)]


def timestamp_action():
    read = sys.stdin.readline
    current_timestamp = int(read().split()[1])
    g.current_timestamp = current_timestamp
    print(f"TIMESTAMP {current_timestamp}")
    
    if g.current_timestamp % 2000 == 0:
        pass
        # rt.log_time()

    # if int(current_timestamp) == g.T + g.EXTRA_TIME:
    #     log_disk(g.disk, g.tag_dict)

    # log("*" * 20 + f"TIMESTAMP {current_timestamp}" + "*" * 20, new_line=True)
    sys.stdout.flush()
