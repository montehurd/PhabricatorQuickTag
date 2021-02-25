#!/usr/local/bin/python3

class Button:
    def __init__(self, title, clickEndpoints, stateEndpointIndex=0):
        self.title = title
        self.clickEndpoints = clickEndpoints
        self.stateEndpointIndex = stateEndpointIndex
