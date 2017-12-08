#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import logging

class DBException(Exception):
    def __init__(self, message, errors=0):
        super().__init__(message)

        self.errors = errors
        logging.error(message)

class FileException(Exception):
    def __init__(self, message, errors=0):
        super().__init__(message)

        self.errors = errors
        logging.error(message)

class NotImplementException(Exception):
    def __init__(self, message, errors=0):
        super().__init__(message)

        self.errors = errors
        logging.error(message)

class UnknownException(Exception):
    def __init__(self, message, errors=0):
        super().__init__(message)

        self.errors = errors
        logging.error(message)
