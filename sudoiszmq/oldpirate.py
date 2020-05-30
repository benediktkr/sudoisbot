#!/usr/bin/python3 -u

import os
from time import time # prarnoid pirate
from collections import OrderedDict # paranoid pirate
from copy import deepcopy # paranoid pirate

from loguru import logger
import zmq
# PPP = Paranoid Pirate Protocol
PPP_HEARTBEAT_LIVENESS = 5     # 3-5 is resanable
PPP_HEARTBEAT_INTERVAL = 1.0   # seconds
PPP_READY = b"\x01"
PPP_HEARTBEAT = b"\x02"

class Worker(object):
    def __init__(self, address):
        grace = PPP_HEARTBEAT_INTERVAL * PPP_HEARTBEAT_LIVENESS
        self.expiry = time() + grace
        self.address = address

    @classmethod
    def from_multipart(cls, multipart):
        address = multipart[0]
        return cls(address)

    def __str__(self):
        return self.address.decode()

class WorkerQueue(object):
    # this whole class can be made more pythonic but
    # following the guide for now
    def __init__(self):
        self.queue = OrderedDict()

    def __bool__(self):
        """True if there are workers"""
        return len(self.queue) > 0

    def __str__(self):
        return str([str(w) for w in self.queue])

    def ready(self, worker):
        # remove the worker if it exists
        # i think this logic can be done more pythonic
        self.queue.pop(worker.address, None)
        self.queue[worker.address] = worker

    def purge(self):
        t = time()
        expired = list()

        # this will also raise RuntimeError if we try to remove
        # items while we are iterating over it
        workers = deepcopy(self.queue)
        for address, worker in workers.items():
            if t > worker.expiry:
                logger.warning(f"Purging idle worker: '{worker}'")
                self.remove(address)

    def remove(self, address):
        removed = self.queue.pop(address, None)
        logger.debug(f"worker '{removed}' removed")

    def next(self):
        # last: FIFO if False, LIFO if True
        address, worker = self.queue.popitem(last=False)
        return address

def paranoidpirate(frontend_addr, backend_addr):
    context = zmq.Context()

    frontend = context.socket(zmq.ROUTER)
    frontend.bind(frontend_addr)

    backend = context.socket(zmq.ROUTER)
    # raises zmq.error.ZMQError when a message is sent to
    # an address thats not connected, otherwise drops
    # the message silently
    backend.setsockopt(zmq.ROUTER_MANDATORY, 1)
    backend.bind(backend_addr)

    poll_workers = zmq.Poller()
    poll_workers.register(backend, zmq.POLLIN)

    poll_both = zmq.Poller()
    poll_both.register(frontend, zmq.POLLIN)
    poll_both.register(backend, zmq.POLLIN)

    logger.info(
        f"paranoidpirate: {frontend_addr} [<-]--> {backend_addr}")

    workers = WorkerQueue()

    heartbeat_at = time() + PPP_HEARTBEAT_INTERVAL

    while True:
        if workers:
            poller = poll_both
        else:
            poller = poll_workers
        socks = dict(poller.poll(PPP_HEARTBEAT_INTERVAL*1000)) #ms

        # handle worker activity
        if socks.get(backend) == zmq.POLLIN:
            frames = backend.recv_multipart()
            if not frames:
                logger.error("empty multipart message on backend")
                break

            # maybes should be moved to the if statement below
            workers.ready(Worker.from_multipart(frames))

            msg = frames[1:]
            if len(msg) == 1:
                # validate control message
                if msg[0] not in (PPP_HEARTBEAT, PPP_READY):
                    logger.error(f"Invalid msg '{msg}' from {worker}")
            else:
                # returning reply to client
                # worker returns multipart frames with
                # client address
                logger.debug(f"from worker: {frames}")
                logger.debug(f"to client: {msg}")
                frontend.send_multipart(msg)

            # since the poller will release us here if the heartbeat
            # interval has passed, send heartbeat to idle workers
            # if its time
            # also move this to a function
            if time() >= heartbeat_at:
                # iterating over a dict, we get the key (address)

                # to avoid
                # RuntimeError: OrderedDict mutated during iteration
                # but we end up using 2x the memory for a short while
                idle_workers = deepcopy(workers.queue)

                for worker_addr in idle_workers:
                    msg = [worker_addr, PPP_HEARTBEAT]
                    try:
                        # nonblocking on ROUTER sockets. Will either
                        # raise error if ROUTER_MANDATORY is set
                        # or otherwise silently drop the message
                        backend.send_multipart(msg)
                    except zmq.error.ZMQError as e:
                        if str(e) == "Host unreachable":
                            # this would raise a RuntimeError
                            # if we were still orering over the
                            # same OrderedDict
                            # too far indendent...
                            logger.warning(
                                f"Unreachable: '{worker_addr}'")
                            workers.remove(worker_addr)
                        else:
                            raise
                heartbeat_at = time() + PPP_HEARTBEAT_INTERVAL

        if socks.get(frontend) == zmq.POLLIN:
            frames = frontend.recv_multipart()

            if not frames:
                logger.error("empty multipart message on frontend")
                break

            logger.debug(f"from client: {frames}")

            worker = workers.next()

            request2 = [worker, b""] + msg
            frames.insert(0, worker)


            #logger.debug(request2)
            logger.debug(f"to worker: {frames}")
            backend.send_multipart(frames)

        workers.purge()
