from get_in import *
from action import *

EXTRA_TIME = 105


def main():
    try:
        log("starting...")
        T, M, N, V, G = pre_action()
        log(f"T: {T}, M: {M}, N: {N}, V: {V}, G: {G}")
        for _ in range(1, T + EXTRA_TIME + 1):
            timestamp_action()
            delete_action()
            write_action()
            read_action()
    except Exception as e:
        print_error(e)


if __name__ == "__main__":
    main()
