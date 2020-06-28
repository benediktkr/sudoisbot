#!/usr/bin/python3 -u

from time import time
from collections import OrderedDict
from copy import deepcopy
from binascii import hexlify

from loguru import logger
import zmq


# PPP = Paranoid Pirate Protocol
PPP_HEARTBEAT_LIVENESS = 5     # 3-5 is resanable
PPP_HEARTBEAT_INTERVAL = 5.0   # seconds
PPP_READY = b"\x01"
PPP_HEARTBEAT = b"\x02"

class Worker(object):
    def __init__(self, address, service):
        grace = PPP_HEARTBEAT_INTERVAL * PPP_HEARTBEAT_LIVENESS
        self.expiry = time() + grace
        self.address = address
        if service is None:
            self.service = "default"
        else:
            self.service = service

    @classmethod
    def from_multipart(cls, multipart):
        address = multipart[0]
        service = multipart[2]
        return cls(address, service)

    def __str__(self):
        try:
            return hexlify(self.address).decode('utf-8')
        except UnicodeDecodeError:
            return super().__str__()

    def __repr__(self):
        return f"<Worker {self} {self.service}>"

class NoWorkerError(KeyError): pass

class WorkerQueue(dict):
    # this whole class can be made more pythonic but
    # following the guide for now

    def __bool__(self):
        """True if there are workers"""
        # since we dont have to actually know how many there are
        # just that there are some, this is sufficient and margianally
        # faster. returns a list of lists of workers in each service
        #   [ ['worker-0', 'worker-1'], ['foo-1', 'foo-2'], [] ]
        return [v for (k,v) in self.items()]


    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str({k: [str(a) for a in w.values()] for (k, w) in self.items()})

    def ready(self, worker):
        # remove the worker if it exists
        # i think this logic can be done more pythonic
        logger.trace(f"adding worker {worker} to service '{worker.service}'")
        if worker.service == b'':
            raise EnvironmentError
        self.setdefault(worker.service, OrderedDict())
        self[worker.service].pop(worker.address, None)
        self[worker.service][worker.address] = worker

    def all_workers(self):
        for workers in self.values():
            for worker in workers.values():
                yield worker

    def purge(self):
        t = time()

        # this will also raise RuntimeError if we try to remove
        # items while we are iterating over it

        for service, workers in self.items():
            expired = list()
            for address, worker in workers.items():
                if t > worker.expiry:
                    expired.append(worker)
            for address in expired:
                logger.warning(f"Purging idle worker: '{worker}'")
                self.remove(worker)

    def remove(self, worker):
        removed = self[worker.service].pop(worker.address, None)
        #if len(self[service]) == 0:
        #    self.pop(service)
        logger.debug(f"removed '{worker}'")
        logger.trace(f"workers: '{self}'")

    def next(self, service):
        # last: FIFO if False, LIFO if True
        if len(self[service]) == 0:
            # or kwatch the KeyError that .popitem ?
            raise NoWorkerError

        address, worker = self[service].popitem(last=False)
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

    def print_frames(self, frames, comment=""):
        addr = hexlify(frames[0])
        if frames[1] == PPP_HEARTBEAT:
            second = "PPP_HEARTBEAT"
        elif frames[1] == PPP_READY:
            second = "PPP_READY"
        else:
            second = frames[2]

        formatted = [addr, second] + frames[2:]
        if comment:
            print(f"{comment}: {formatted}")
        else:
            print(formatted)


    def handle_backend(self, frames):
        if not frames:
            logger.error("empty multipart message on backend")
            raise ValueError("empty multipart message on backend")
        # maybes should be moved to the if statement below
        self.workers.ready(Worker.from_multipart(frames))
        logger.trace(f"workers: {self.workers}")

        msg = frames[1:]
        if len(msg) == 2:
            logger.debug("len(msg) == 2, msg == {}".format(msg))
            # validate control message
            hexaddr = hexlify(frames[0]).decode("utf8")
            servstr = msg[1].decode("utf8")
            if msg[0] not in (PPP_HEARTBEAT, PPP_READY):
                logger.error(f"Invalid msg '{msg}' from {hexaddr}")
            else:
                if msg[0] == PPP_HEARTBEAT:
                    logger.trace(f"PPP_HEARTBEAT from {hexaddr}/{servstr}")
                elif msg[0] == PPP_READY:
                    logger.trace(f"PPP_READY from {hexaddr}/{servstr}")
        else:
            # returning reply to client
            # worker returns multipart frames with
            # client address
            #logger.debug(f"from worker: {frames}")
            #logger.trace(f"to client: {msg}")
            # return ?
            self.frontend.send_multipart(msg)

    def handle_frontend(self, frames):
        if not frames:
            logger.error("empty multipart message on frontend")
            raise ValueError("empty multipart message on frontend")

        #logger.debug(f"from client: {frames}")

        service = frames[2]
        try:
            worker = self.workers.next(service)
            request = [worker] + frames

            #logger.trace(f"to worker: {request}")
            # return ?
            self.print_frames(request, "sent to backend")
            self.backend.send_multipart(request)
        except KeyError:
            # does this drop the message?
            logger.warning(f"no worker for {service} ({frames[0]})")
            pass


    def send_heartbeats(self):
        if time() >= self.heartbeat_at:
            # iterating over a dict, we get the key (address)
            # to avoid
            # RuntimeError: OrderedDict mutated during iteration
            # but we end up using 2x the memory for a short while
            # using a sperate dict like the guide did might be best..
            heartbeats = deepcopy(self.workers)
            for worker in heartbeats.all_workers():
                msg = [worker.address, PPP_HEARTBEAT]
                try:
                    # nonblocking on ROUTER sockets. Will either
                    # raise error if ROUTER_MANDATORY is set
                    # or otherwise silently drop the message
                    logger.trace(f"heartbeating to: '{worker}'")
                    self.backend.send_multipart(msg)
                except zmq.error.ZMQError as e:
                    if str(e) == "Host unreachable":
                        # this would raise a RuntimeError
                        # if we were still orering over the
                        # same OrderedDict
                        # too far indendent...
                        logger.warning(f"Unreachable: '{worker}'")
                        self.workers.remove(worker)
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
            #if self.workers:
            #    poller = self.poll_both
            #else:
            #    poller = self.poll_workers

            # sine im only using one poller i could maybe use one socket
            poller = self.poll_both
            socks = dict(poller.poll(PPP_HEARTBEAT_INTERVAL*1000)) #ms

            # handle worker activity
            if socks.get(self.backend) == zmq.POLLIN:
                frames = self.backend.recv_multipart()
                self.print_frames(frames, "read from backend")

                self.handle_backend(frames)

            # since the poller will release us here if the heartbeat
            # interval has passed, send heartbeat to idle workers
            # if its time
            self.send_heartbeats()

            if socks.get(self.frontend) == zmq.POLLIN:
                frames = self.frontend.recv_multipart()
                self.print_frames(frames, "read from frontend")
                self.handle_frontend(frames)

            self.workers.purge()
