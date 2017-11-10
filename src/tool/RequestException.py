#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

class DBException(Exception):
    def __init__(self, message, errors=0):
        super().__init__(message)

        self.errors = errors

class FileException(Exception):
    def __init__(self, message, errors=0):
        super().__init__(message)

        self.errors = errors

class NotImplementException(Exception):
    def __init__(self, message, errors=0):
        super().__init__(message)

        self.errors = errors
