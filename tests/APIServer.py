#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-


import sys
import queue
import signal
import argparse
import threading

import context
import Worker
import Request
import Route

class APIServer():
    def __init__(self, ip, port, threads):
        # Ctrl + C handler
        signal.signal(signal.SIGINT, self.signal_handler)

        # Set some basic variable, and data structure
        self.ip = ip
        self.port = port
        self.counter = 0
        self.request_queue = queue.Queue()
        self.threads = []
        self.event = threading.Event()

        # Setup Flask with Route
        self.app = Route.initialize(self.counter, self.request_queue)

        # Create worker thread
        self.num_of_worker_threads = threads
        for i in range(0, self.num_of_worker_threads, 1):
            thread = Worker.HTTPRequestHandler(i, str(i), self.threads, self.event, self.request_queue)
            thread.start()
            self.threads.append(thread)

    def signal_handler(self, signal, frame):
        print("Got it!")
        for i in range(0, self.num_of_worker_threads, 1):
            self.request_queue.put(None)
        self.event.set()

        print("Waiting for worker join!")
        for thread in self.threads:
            thread.join()

        print("Ready to quit!")
        exit(0)

    def run(self):
        self.app.run(host=self.ip, port=self.port)

"""
Argument init
"""
def arg_initialize(argv):
    parser = argparse.ArgumentParser(description="Start to running API server.")
    parser.add_argument("--threads", type=int, default=1, help="Specify number of worker threads. Default is 1.")
    parser.add_argument("--ip", help="Specify the binding address. Default is localhost.", default="localhost")
    parser.add_argument("--port", help="Specify the binding port. Default is 5000.", default=5000)

    return parser.parse_args()

"""
Main function
"""
if __name__ == "__main__":
    argv = sys.argv

    args = arg_initialize(argv)
    server = APIServer(args.ip, args.port, args.threads)
    server.run()
