#!/usr/bin/python3 -u

from time import time
from collections import OrderedDict
from copy import deepcopy

from loguru import logger
import zmq


# PPP = Paranoid Pirate Protocol
PPP_HEARTBEAT_LIVENESS = 5     # 3-5 is resanable
PPP_HEARTBEAT_INTERVAL = 5.0   # seconds
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


class ParanoidPirate(object):
    def __init__(self, router_mandatory):

        self.context = zmq.Context()

        self.frontend = self.context.socket(zmq.ROUTER)
        self.backend = self.context.socket(zmq.ROUTER)
        # raises zmq.error.ZMQError when a message is sent to
        # an address thats not connected, otherwise drops
        # the message silently
        _rm = int(router_mandatory)
        self.backend.setsockopt(zmq.ROUTER_MANDATORY, _rm)

        self.poll_workers = zmq.Poller()
        self.poll_workers.register(self.backend, zmq.POLLIN)

        self.poll_both = zmq.Poller()
        self.poll_both.register(self.frontend, zmq.POLLIN)
        self.poll_both.register(self.backend, zmq.POLLIN)

        self.heartbeat_at = time() + PPP_HEARTBEAT_INTERVAL

        self.workers = WorkerQueue()


    def bind(self, frontend, backend):
        self.frontend.bind(frontend)
        self.backend.bind(backend)

        logger.info(f"paranoidpirate: {frontend} [<-]--> {backend}")

    def process_backend(self, frames):
        if not frames:
            logger.error("empty multipart message on backend")
            raise ValueError("empty multipart message on backend")
        # maybes should be moved to the if statement below
        self.workers.ready(Worker.from_multipart(frames))

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
            # return ?
            self.frontend.send_multipart(msg)

    def handle_frontend(self, frames):
        if not frames:
            logger.error("empty multipart message on frontend")
            raise ValueError("empty multipart message on frontend")

        logger.debug(f"from client: {frames}")

        worker = self.workers.next()
        request = [worker] + frames

        logger.debug(f"to worker: {request}")
        # return ?
        self.backend.send_multipart(request)


    def send_heartbeats(self):
        if time() >= self.heartbeat_at:
            # iterating over a dict, we get the key (address)
            # to avoid
            # RuntimeError: OrderedDict mutated during iteration
            # but we end up using 2x the memory for a short while
            # using a sperate dict like the guide did might be best..
            idle_workers = deepcopy(self.workers.queue)
            for worker_addr in idle_workers:
                msg = [worker_addr, PPP_HEARTBEAT]
                try:
                    # nonblocking on ROUTER sockets. Will either
                    # raise error if ROUTER_MANDATORY is set
                    # or otherwise silently drop the message
                    self.backend.send_multipart(msg)
                except zmq.error.ZMQError as e:
                    if str(e) == "Host unreachable":
                        # this would raise a RuntimeError
                        # if we were still orering over the
                        # same OrderedDict
                        # too far indendent...
                        logger.warning(f"Unreachable: '{worker_addr}'")
                        self.workers.remove(worker_addr)
                    else:
                        raise

            self.heartbeat_at = time() + PPP_HEARTBEAT_INTERVAL

    def destroy(self):
        while self.workers:
            for worker in self.workers:
                assert worker is not None
                # send a disconnect command to worker
                self.workers.remove(worker)

        self.context.destroy()

    def mediate(self):
        while True:
            if self.workers:
                poller = self.poll_both
            else:
                poller = self.poll_workers

            socks = dict(poller.poll(PPP_HEARTBEAT_INTERVAL*1000)) #ms

            # handle worker activity
            if socks.get(self.backend) == zmq.POLLIN:
                frames = self.backend.recv_multipart()
                self.process_backend(frames)

            # since the poller will release us here if the heartbeat
            # interval has passed, send heartbeat to idle workers
            # if its time
            self.send_heartbeats()

            if socks.get(self.frontend) == zmq.POLLIN:
                frames = self.frontend.recv_multipart()
                self.handle_frontend(frames)

            self.workers.purge()
