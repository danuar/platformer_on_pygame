import time

# Const
PHYSICAL_FRAME = 60


def physical_process(time_delay, *args):
    while True:
        for i in args:
            i()
        time.sleep(time_delay)

