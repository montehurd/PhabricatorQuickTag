#!/usr/local/bin/python3

class ClickEndpoint:
    def __init__(self, name, key, value, stateCheckerLambda = None):
        self.name = name
        self.key = key
        self.value = value
        self.stateCheckerLambda = stateCheckerLambda
