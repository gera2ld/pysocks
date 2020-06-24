#!/usr/bin/env python
# coding=utf-8

class ProtocolMixIn:
    def __init__(self, writer):
        self.writer = writer
        self.data_len = 0
