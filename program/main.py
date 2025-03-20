from get_in import *
from action import *
EXTRA_TIME = 105


def main():
    import time
    
    write_time = 0
    delete_time = 0
    read_time = 0
    
    try:
        log("starting...")
        T, M, N, V, G = pre_action()
        log(f"T: {T}, M: {M}, N: {N}, V: {V}, G: {G}")
        for _ in range(1, T + EXTRA_TIME + 1):
            timestamp_action()
            
            start_time = time.time()
            delete_action()
            delete_time += time.time() - start_time
            
            start_time = time.time()
            write_action()
            write_time += time.time() - start_time
            
            start_time = time.time()
            read_action()
            read_time += time.time() - start_time
    except Exception as e:
        print_error(e)

    log(f"write_time: {write_time}, delete_time: {delete_time}, read_time: {read_time}")


if __name__ == "__main__":
    main()
