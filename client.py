import threading
import math
import greenstalk
import time

leds=(0,{})

def set_leds(new_leds):
    global leds
    leds = new_leds

def get_leds():
    global leds
    return leds

def message_getter(lock):
    client = greenstalk.Client(("logo.lang.speechmarks.com", 11300), use="logo-status", watch="logo-status")
    iteration = 1
    while True:
        job = client.reserve()
        lock.acquire()
        set_leds((iteration, process_message(bstr_to_str(job.body))))
        lock.release()
        iteration = iteration + 1
        client.delete(job)

def bstr_to_str(msg):
    if type(msg) == bytes:
        return msg.decode("ascii")
    return msg

def process_message(msg):
    reta = []
    splits = str(msg).split("\n")
    for split in splits:
        d = {}
        for part in split.split(";"):
            kv = part.split("=")
            if len(kv) == 2:
                d[kv[0]] = kv[1]
        reta.append(d)
    ret = {}
    for ret_tmp in reta:
        if "LED" in ret_tmp:
            ret[ret_tmp["LED"]] = ret_tmp
            ret_tmp.pop("LED")
    print(str(ret))
    return ret


def light_lighter(lock):
    sleep_time = 1/60;
    # sleep_time = 1;

    ledconf = {
        'usr1': { 'color': "usr1-color", 'autonomous': "usr1-autonomous", 'brightness': "usr1-brightness" },
        'usr2': { 'color': "usr2-color", 'autonomous': "usr2-autonomous", 'brightness': "usr2-brightness" }
    }

    ledconf = {
        'usr1': { 'color': '/sys/class/leds/omnia-led:user1/color', 'autonomous': "/sys/class/leds/omnia-led:user1/autonomous", 'brightness': "/sys/class/leds/omnia-led:user1/brightness" },
        'usr2': { 'color': '/sys/class/leds/omnia-led:user2/color', 'autonomous': "/sys/class/leds/omnia-led:user2/autonomous", 'brightness': "/sys/class/leds/omnia-led:user2/brightness" }
    }

    with open(ledconf["usr1"]["autonomous"], "w") as usr1, open(ledconf["usr2"]["autonomous"], "w") as usr2:
        usr1.write("0")
        usr2.write("0")
        usr1.flush()
        usr2.flush()
    with open(ledconf["usr1"]["brightness"], "w") as usr1, open(ledconf["usr2"]["brightness"], "w") as usr2:
        usr1.write("255")
        usr2.write("255")
        usr1.flush()
        usr2.flush()
    with open(ledconf["usr1"]["color"], "w") as usr1, open(ledconf["usr2"]["color"], "w") as usr2:
        usr1.write("0 0 0")
        usr2.write("0 0 0")
        usr1.flush()
        usr2.flush()

    iteration = 0
    my_leds = (0, {})
    with open(ledconf["usr1"]["color"], "w") as usr1, open(ledconf["usr2"]["color"], "w") as usr2:
        files = { "usr1": usr1, "usr2": usr2 }
        frame = 0;
        while True:
            frame = frame + 1
            if frame > 100:
                frame = 0
            lock.acquire()
            my_leds = get_leds()
            lock.release()
            # my_leds = (msg[0], process_message(msg[1]))
            for k, v in my_leds[1].items():
                color = list(map(safe_str_to_int, v["COLOR"].split(" ")))
                if len(color) != 3:
                    continue
                status = safe_str_to_int(v["STATUS"])
                if status == 1:
                    color = list(map(str, color))
                if status == 0:
                    color = ["0", "0", "0"]
                if status != 0 and status != 1:
                    status = abs(status) - 1
                    sin_in = 6.283 * (frame / 100) * status
                    color = list(map(lambda c: str(int(math.sin(sin_in) * (c / 2) + (c / 2))), color))
                files[k].truncate(0)
                files[k].write(" ".join(color))
                files[k].flush()
            time.sleep(sleep_time)

def safe_str_to_int(s):
    try:
        return int(s)
    except:
        return 0

lock = threading.Lock()

# creating a thread for each function
trd1 = threading.Thread(target=message_getter, args=(lock,))
trd2 = threading.Thread(target=light_lighter, args=(lock,))

trd1.start() # starting the thread 1 
trd2.start() # starting the thread 2

trd1.join()
trd2.join()

print('End')


