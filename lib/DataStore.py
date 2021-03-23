#!/usr/local/bin/python3

import Utilities

__configurationJSON = None

def loadConfiguration():
    global __configurationJSON
    __configurationJSON = Utilities.jsonFromFile('configuration.json')

def getConfigurationValue(key):
    global __configurationJSON
    return __configurationJSON['configuration'][key]

def getCurrentConfiguration():
    global __configurationJSON
    return __configurationJSON['configuration']

def saveCurrentConfiguration():
    global __configurationJSON
    Utilities.jsonToFile('configuration.json', __configurationJSON)
