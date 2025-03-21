import sys
from utils import log, log_disk, if_online
from global_variables import g

specific_timestamp = [86000]

def timestamp_action():
    read = sys.stdin.readline
    current_timestamp = int(read().split()[1])
    print(f"TIMESTAMP {current_timestamp}")
    
    if int(current_timestamp) == g.T+g.EXTRA_TIME:
        log_disk(g.disk, g.tag_dict)
    if not if_online and int(current_timestamp) in specific_timestamp:
        log_disk(g.disk, g.tag_dict)
        g.use_write_log = True
    else:
        g.use_write_log = False

    if g.use_write_log:
        log(f"TIMESTAMP {current_timestamp}")
    sys.stdout.flush()
    