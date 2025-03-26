from pre_action import pre_action
from read_action import read_action
from delete_action import delete_action
from timestamp_action import timestamp_action
from utils import log, print_error, rt
from write_action import write_action

EXTRA_TIME = 105


def main():
    
    # try:
        log("starting...")
        T, M, N, V, G = pre_action()
        log(f"T: {T}, M: {M}, N: {N}, V: {V}, G: {G}")
        for _ in range(1, T + EXTRA_TIME + 1):
            # rt.set_start_time("timestamp action")
            timestamp_action()
            # rt.record_time("timestamp action")
            
            # rt.set_start_time("delete action")
            delete_action()
            # rt.record_time("delete action")
            
            # rt.set_start_time("write action")
            write_action()
            # rt.record_time("write action")
            
            # rt.set_start_time("read action")
            read_action()
            # rt.record_time("read action")

    # except Exception as e:
    #     print_error(e)


if __name__ == "__main__":
    main()
