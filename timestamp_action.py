import sys
from utils import log, log_disk, if_online
from global_variables import g

specific_timestamp = [i for i in range(0)]


def timestamp_action():
    read = sys.stdin.readline
    current_timestamp = int(read().split()[1])
    g.current_timestamp = current_timestamp
    print(f"TIMESTAMP {current_timestamp}")
    
    if g.current_timestamp % 100 == 0:
        for i in range(20):
            if g.time_count[i] > 0:
                log(f"Time count {i}: {g.time_count[i]}")

    if int(current_timestamp) == g.T + g.EXTRA_TIME:
        log_disk(g.disk, g.tag_dict)
    if not if_online and int(current_timestamp) in specific_timestamp:
        g.use_write_log = True
    else:
        g.use_write_log = False

    log("*" * 20 + f"TIMESTAMP {current_timestamp}" + "*" * 20, new_line=True)
    sys.stdout.flush()
