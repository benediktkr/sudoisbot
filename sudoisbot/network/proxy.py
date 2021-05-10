#!/usr/bin/python3 -u

from collections import deque, defaultdict
import os
import json
import time
import base64

from loguru import logger
import zmq

from sudoisbot.config import read_config

def dealer(dealer_addr, router_addr):
    print("dealer")
    context = zmq.Context()

    # facing requesters
    dealer = context.socket(zmq.DEALER)
    dealer.bind(dealer_addr)

    # facing repliers
    router = context.socket(zmq.ROUTER)
    router.bind(router_addr)

    logger.info(f"zmq dealer: {dealer_addr} [<-]--> {router_addr}")
    zmq.proxy(dealer, router)

    dealer.close()
    router.close()
    context.close()



def proxy_buffering(frontend_addr, backend_addr, capture_addr=None):
    context = zmq.Context()

    disk_interval = 3
    disk_at = int(time.time()) + disk_interval

    def save_cache_to_disk(target_dir="/tmp/proxy_cache/"):
        for topic in cache.keys():

            filename = topic.decode() + ".cache"

            with open(os.path.join(target_dir, filename), 'wb') as f:

                for multipart_msg in list(cache[topic]):
                    parts64 = [base64.b64encode(a) for a in multipart_msg]

                    #print(parts64)
                    f.write(b"|".join(parts64))
                    f.write(b"\n")

    def load_cache_from_disk(target_dir="/tmp/proxy_cache"):
        files = os.listdir(target_dir)
        for filename in files:
            fullpath = os.path.join(target_dir, filename)
            with open(fullpath, 'rb') as f:
                for line in f.readlines():
                    parts64 = line.split(b"|")
                    yield [base64.b64decode(a) for a in parts64]
            #os.remove(fullpath)

    def delete_cache_on_disk(topic, target_dir="/tmp/proxy_cache"):
        filename = topic.decode() + ".cache"
        fullpath = os.path.join(target_dir, filename)
        try:
            os.remove(fullpath)
        except FileNotFoundError:
            logger.warning(f"could not delete disk cache because {fullpath} does not exist")


    # facing publishers
    frontend = context.socket(zmq.SUB)
    frontend.setsockopt(zmq.SUBSCRIBE, b'')
    frontend.bind(frontend_addr)

    # facing services (sinks/subsribers)
    backend = context.socket(zmq.XPUB)
    backend.bind(backend_addr)
    # infrom publishers of a new sink
    #backend.setsockopt(ZMQ_XPUB_VERBOSE, 1)

    logger.info(f"zmq pubsub proxy: {frontend_addr} -> {backend_addr}")
    if capture_addr:
        capture = context.socket(zmq.PUB)
        capture.bind(capture_addr)
        logger.info(f"zmq capture: {capture_addr}")


    else:
        capture = None


    poller = zmq.Poller()
    poller.register(frontend, zmq.POLLIN)
    poller.register(backend, zmq.POLLIN)
    if capture:
        poller.register(backend, zmq.POLLIN)


    # send \x01 to all publishers when they connect

    lvc = dict()
    cache = defaultdict(deque)
    cache_topics = set()

    for item in load_cache_from_disk():
        cache[item[0]].append(item)

    for topic in cache.keys():
        csize  = len(cache[topic])
        if csize > 0:
            logger.warning(f"{topic} - {csize} cached items loaded")

    while True:
        try:
            events = dict(poller.poll(1000))
        except KeyboardInterrupt:
            logger.info("im leaving")
            save_cache_to_disk()
            logger.info("saved cache")
            break


        now = int(time.time())
        if now > disk_at:
            save_cache_to_disk()
            disk_at = now + disk_interval

        if capture:
            stats = {
                'cache_size': {
                    k.decode(): len(v) for (k, v) in cache.items()
                },
                'topics': [a.decode() for a in lvc.keys()],
                'cache_topics': [a.decode() for a in  cache_topics],
                'disk_at': disk_at
            }
            capture.send_multipart([b"meta:stats", json.dumps(stats).encode()])

        if frontend in events:
            msg = frontend.recv_multipart()
            topic = msg[0]

            #frontend.send_multipart([b"\x00rain"])

            if topic not in lvc:
                logger.info(f"caching topic {topic} that hasnt seen a listener yet")
                cache_topics.add(topic)
            lvc[topic] = msg

            if topic in cache_topics:
                #logger.debug(f"[o] cached {msg}")
                cache[topic].append(msg)
            else:
                backend.send_multipart(msg)

            if capture:
                capture.send_multipart(msg)


        if backend in events:

            msg = backend.recv_multipart()
            #logger.warning(f"[x] backend: {msg}")
            if msg[0][0] == 0:
                topic = msg[0][1:]
                cache_topics.add(topic)
                logger.info(f"[o] now caching {topic}")

            if msg[0][0] == 1: #'\x01'
                topic = msg[0][1:]
                if topic not in lvc:
                    # the keys of the topic dir are also a list of "known topics"
                    logger.success(f"registered {topic}")
                    lvc[topic] = None

                if topic in cache_topics:
                    csize = len(cache[topic])
                    if csize > 0:
                        logger.info(f"draning {csize} messages for {topic}")

                        while len(cache[topic]) > 0:
                            buffered = cache[topic].popleft()
                            backend.send_multipart(buffered)

                        save_cache_to_disk()


                    logger.success(f"stopped caching {topic}")
                    cache_topics.discard(topic)


                elif topic in lvc and lvc[topic] is not None:
                    cached = lvc[topic]
                    backend.send_multipart(cached + [b"cached"])
                    logger.success(f"[>] lvc sent for {topic}")


                #frontend.send(msg)
                #logger.success(f"[>] backend: {msg}")


        if capture in events:
            logger.warning(f"capture: {capture.recv_mutlipart(msg)}")


    #zmq.proxy(frontend, backend, capture)
    #while True:



    # we never used to get here
    frontend.close()
    backend.close()
    context.close()

def proxy_forwarder(frontend_addr, backend_addr, capture_addr):
    context = zmq.Context()

    # facing publishers
    #frontend = context.socket(zmq.XSUB)

    frontend = context.socket(zmq.SUB)
    frontend.setsockopt(zmq.SUBSCRIBE, b'')
    frontend.connect(frontend_addr)

    # facing services (sinks/subsribers)
    backend = context.socket(zmq.XPUB)
    backend.bind(backend_addr)
    # infrom publishers of a new sink
    #backend.setsockopt(ZMQ_XPUB_VERBOSE, 1)

    logger.info(f"zmq pubsub proxy: {frontend_addr} -> {backend_addr}")


    if capture_addr:
        capture = context.socket(zmq.PUB)
        capture.bind(capture_addr)
        logger.info(f"zmq capture: {capture_addr}")

        zmq.proxy(frontend, backend, capture)

    else:
        zmq.proxy(frontend, backend)

    # we never get here
    frontend.close()
    backend.close()
    if capture:
        capture.close()
    context.close()

def capture(capture_addr):
    capture_port = capture_addr.split(":")[-1]
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b'')
    addr = f"tcp://127.0.0.1:{capture_port}"
    socket.connect(addr)
    logger.info("connecting to " + addr)

    import pprint
    import sys
    while True:

        r = socket.recv_multipart()
        #pprint.pprint(r[1].decode())
        #print(r)
        jdata = json.loads(r[1].decode())

        if "cache_size" in jdata:
            print(r[1].decode(), end="\n")
        sys.stdout.flush()
        #print("")



def main_forwarder(config):

    # zmq_in_connect = config['zmq_in_connect']
    # zmq_frontend = config['zmq_frontend']
    # zmq_capture = config['zmq_capture']

    zmq_in_connect = "tcp://192.168.1.2:5560"
    zmq_backend = "tcp://*:5560"
    zmq_capture = "tcp://127.0.0.1:5561"


    return forwarder(
        config['frontend_addr'], config['backend_addr'], config['capture_addr'])


def main_buffering(args, config):
    capture_addr = config.get('capture_addr')
    if args.capture:
        return capture(capture_addr)

    return proxy_buffering(
        config['frontend_addr'], config['backend_addr'], capture_addr)
