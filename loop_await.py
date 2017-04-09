import asyncio
import time
import random
import multiprocessing

async def async_loop(name, time_limit=10, time_step=.25):
    end_time = time.time() + time_limit
    count = 0
    while True:
        await asyncio.sleep(time_step)
        rd = random.random()
        count += 1
        print("name:", name, ", count:", count, ", random", rd)
        if time.time() > end_time:
            break
        if .8 < rd:
            return {"name": name, "result": True, "number": rd}
        return {"name": name, "result": False, "number": None}


def loop_decorator(name):
    print("in", name)
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(async_loop(name))
    loop.close()
    return res


def report_callback(result):
    print("name: {name}, result: {result}, number: {number}".format(**result))


def caller_loop(multiple):
    pool = multiprocessing.Pool(multiprocessing.cpu_count() * (multiple or 3))
    for i in range(0, 10):
        print("generating loops:", i)
        pool.apply_async(loop_decorator, ("looper_" + str(i), ), callback=report_callback)
    pool.close()
    pool.join()


if __name__ == "__main__":
    for i in range(1, 5):
        caller_loop(3)
