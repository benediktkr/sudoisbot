#!/usr/bin/env python3

from loguru import logger
from binascii import hexlify
import time

import zmq

from sudoisbot.network import MDP

INTERNAL_SERVICE_PREFIX = b"mmi."
HEARTBEAT_LIVENESS = 3 # 3-5 is reasonable
HEARTBEAT_INTERVAL = 3 # seconds
HEARTBEAT_EXPIRY = HEARTBEAT_INTERVAL * HEARTBEAT_LIVENESS



class Service(object):
    def __init__(self, name):
        assert isinstance(name, bytes)
        self.name = name
        self.requests = list()
        self.waiting = list()  # list of waitig workers

    def __repr__(self):
        n = self.name.decode('ascii')
        r = len(self.requests)
        ws = ','.join(([str(a) for a in self.waiting]))

        return f"<Service '{n}': [{ws}] ({r} requests)>"

class Worker(object):
    def __init__(self, identity, address):
        self.identity = identity # hex
        self.address = address
        self.expiry = time.time() + HEARTBEAT_EXPIRY
        self.service = None

    @property
    def age(self):
        return int(HEARTBEAT_EXPIRY - self.expiry)

    def reset_expiry(self):
        self.expiry = time.time() + HEARTBEAT_EXPIRY
        return self.expiry

    def __str__(self):
        return self.identity.decode('ascii')

    def __repr__(self):
        if self.service:
            s = self.service.name.decode('ascii')
        else:
            s = "UNREGISTERED"
        i = self.identity.decode('ascii')
        return f"<Worker {i}/{s}>"


class Broker(object):

    def __init__(self, router_mandatory=False):
        self.router_mandatory = router_mandatory

        self.services = dict()
        self.workers = dict() # set?
        self.waiting = list()

        self.heartbeat_at = time.time() + HEARTBEAT_INTERVAL

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.linger = 0
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    def bind(self, endpoint):
        logger.info(f"Listening on {endpoint}")
        self.socket.bind(endpoint)

    def mediate(self):

        while True:
            #print(self.services)
            #print(self.workers)
            #print(self.waiting)
            #print("------")

            try:
                items = self.poller.poll(HEARTBEAT_INTERVAL * 1000) # ms
            except KeyboardInterrupt:
                logger.info("C-c caught")
                break

            if items:
                msg = self.socket.recv_multipart()
                if msg[3] != MDP.W_HEARTBEAT:
                    self.dump(msg, "recv")

                sender = msg.pop(0)
                empty = msg.pop(0)
                assert empty == b""
                header = msg.pop(0)

                if header == MDP.C_CLIENT:
                    self.process_client(sender, msg)
                elif header == MDP.W_WORKER:
                    self.process_worker(sender, msg)
                else:
                    logger.error(f"Invalid header: '{header}', msg: '{msg}'")

            self.purge_workers()
            self.send_heartbeats()

    def dump(self, frames, direction):
        print("=======")
        for frame in frames:
            if direction == "recv":
                print("<------", end="  ")
            elif direction == "send":
                print("------>", end="  ")

            size = str(len(frame))
            print(f"[{size.zfill(3)}]", end =" ")

            is_cmd = False
            for command in MDP.commands[1:]:
                cmd = "W_" + command.decode('ascii')
                attr = getattr(MDP, cmd)
                if frame == attr:
                    print(cmd)
                    is_cmd = True

            if not is_cmd:
                try:
                    print(frame.decode("ascii"))
                except UnicodeDecodeError:
                    print(f"0x{hexlify(frame).decode('ascii')}")

    def destroy(self):
        """Disconnect all workers and destroy context"""
        while self.workers():
            self.delete_worker(self.workers.values()[0], True)
        self.context.destroy()

    def process_client(self, sender, msg):
        # if len(msg) < 2:
        #     # should have service_name + body
        #     s = hexlify(sender)
        #     logger.error(f"Invalid client message from {s}: '{msg}'")
        #     return

        # fix this, putting back things that were popped off before
        servicename = msg.pop(0)

        # set reply return address to the client sender
        msg = [sender, b''] + msg
        if servicename.startswith(INTERNAL_SERVICE_PREFIX):
            logger.debug(f"internal service: {servicename}")
            self.service_internal(servicename, msg)
        else:
            self.dispatch(self.require_service(servicename), msg)


    def process_worker(self, sender, msg):
        if len(msg) < 1:
            # at least a command
            logger.error(f"Invalid worker message from: '{sender}': '{msg}'")
            return

        command = msg.pop(0)
        worker_ready = hexlify(sender) in self.workers
        worker_ready2 = self.worker_ready_exists(sender)
        worker = self.require_worker(sender)

        if command == MDP.W_READY:
            try:
                servicename = msg.pop(0)
            except IndexError:
                logger.error(f"Missing service (W_READY), '{sender}': '{msg}'")
                return

            if worker_ready:
                logger.error(f"Worker '{sender}' already ready")
                self.delete_worker(worker, True)

            elif servicename.startswith(INTERNAL_SERVICE_PREFIX):
                logger.error(f"Invalid service '{service}' from '{sender}'")
                self.delete_worker(worker, True)

            else:
                self.worker_waiting(worker, servicename)

        elif command == MDP.W_REPLY:
            # responding to client
            # service name must be somewhere, find it, NOPE IT ISNT

            if worker_ready:
                client = msg.pop(0)
                empty = msg.pop(0)
                if empty != b"":
                    logger.error(
                        f"Expected empty frame but got '{empty}': '{msg}")
                    return
                msg = [client, b"", MDP.C_CLIENT, worker.service.name] + msg
                self.dump(msg, "send")
                self.socket.send_multipart(msg)
                self.worker_waiting(worker)

            else:
                self.delete_worker(worker, True)

        elif command == MDP.W_HEARTBEAT:
            if worker_ready:
                worker.expiry = time.time() + HEARTBEAT_EXPIRY
            else:
                self.delete_worker(worker, True)

        elif command == MDP.W_DISCONNECT:
            self.delete_worker(worker, False)

        else:
            logger.error("Invalid command '{command}': '{msg}'")



    def delete_worker(self, worker, disconnect):
        assert worker is not None

        if disconnect:
            self.send_to_worker(worker, MDP.W_DISCONNECT, None, None)

        if worker.service is not None:
            # changed by me
            service = self.services[worker.service.name]
            service.waiting.remove(worker)

        popped = self.workers.pop(worker.identity)
        if popped is None:
            logger.error(f"Couldn't pop {worker.identity}")
        logger.warning(f"Deleted {worker}")


    def worker_ready_exists(self, address):
        for service in self.services.values():
            if hexlify(address) in service.waiting:
                return True
        return False


    def require_worker(self, address):
        """find the worker if it exists or creates a new worker"""

        assert address is not None

        identity = hexlify(address)
        try:
            return self.workers[identity]
        except KeyError:
            worker = Worker(identity, address)
            self.workers[identity] = worker
            return worker

    def require_service(self, name):
        assert name is not None

        try:
            return self.services[name]
        except KeyError:
            service = Service(name)
            self.services[name] = service
            return service

    def service_internal(self, service, msg):
        """Handle internal service according to 8/MMI specification"""

        prefix = len(INTERNAL_SERVICE_PREFIX)
        int_service = service[prefix:]
        if int_service == b"service":
            name = msg[-1]
            returncode = b"200" if name in self.services else b"404"
            msg.append(returncode)
        if int_service == b"list":
            if len(self.services) > 0:
                msg.append(b"200")
            else:
                msg.append(b"400")
            for name, srvc in self.services.items():
                msg.append(name)
                idents = [w.identity for w in srvc.waiting]
                msg.append(str(len(idents)).encode('ascii'))
                msg.extend(idents)
        if int_service == b"queues":
            if len(self.services) == 0:
                msg.append(b"400")
            else:
                msg.append(b"200")

            for srvc in self.services.values():
                reqs = str(len(srvc.requests)).encode('ascii')
                msg.append(srvc.name)
                msg.append(reqs)

        if int_service == b"workers":
            count = len(self.workers)
            if count == 0:
                msg.append(b"404")
            else:
                msg.append(b"200")

            msg.append(str(count).encode('ascii'))
            for worker in self.workers.values():
                msg.append(worker.identity + b"/" + worker.service.name)

        if int_service == b"purge":
            purged = self.purge_workers()
            if len(purged) > 0:
                msg.append(b"410")
            else:
                msg.append(b"204")
        else:
            returncode = b"400"

        routing_envelope = msg[:2]
        protocol = [MDP.C_CLIENT, service]
        self.socket.send_multipart(routing_envelope + protocol + msg[2:])


    def send_heartbeats(self):
        now = time.time()
        if now > self.heartbeat_at:
            for service in self.services.values():
                for worker in service.waiting:
                    logger.trace(f"heartbeating to {worker}")
                    self.send_to_worker(worker, MDP.W_HEARTBEAT, None, None)

            self.heartbeat_at = now + HEARTBEAT_INTERVAL

    def purge_workers(self):
        """Look for and kill inactive workers. They are sorted from
        oldest to newest, the guide wants to stop at first active worker
        but workers can die even though an older worker is active so
        we go all the way"""

        now = time.time()

        expired = list()
        for service in self.services.values():
            for worker in service.waiting:
                if now > worker.expiry:
                    logger.info(f"Purging expired worker: {worker}")
                    expired.append(worker.identity)
                    self.delete_worker(worker, False)
        return expired


    def worker_waiting(self, worker, attach_to=None):
        if attach_to:
            service = self.require_service(attach_to)
            worker.service = service
            service.waiting.append(worker)
            #print('attached to ' + str(attach_to))
        else:
            service = self.services[worker.service.name]
            service.waiting.append(worker)


        worker.reset_expiry()
        #self.waiting.append(worker)
        self.dispatch(worker.service, None)

    def dispatch(self, service, msg):
        assert service is not None
        assert isinstance(service, Service)


        if not isinstance(service, Service):
            logger.error(f"this is now {type(service)}")
            raise SystemExit

        if msg is not None:
            service.requests.append(msg)

        self.purge_workers()

        while service.waiting and service.requests:
            msg = service.requests.pop(0) #
            worker = service.waiting.pop(0)
            #self.waiting.remove(worker)
            self.send_to_worker(worker, MDP.W_REQUEST, None, msg)





    def send_to_worker(self, worker, command, option=None, msg=None):
        if msg is None:
            msg = []
        if not isinstance(msg, list):
            msg = [msg]

        if option is not None:
            msg = [option] + msg

        msg = [worker.address, b"", MDP.W_WORKER, command] + msg

        if command != MDP.W_HEARTBEAT:
            self.dump(msg, "send")

        self.socket.send_multipart(msg)
