#!/usr/local/bin/python3

import Utilities

configurationJSON = None

def loadConfiguration():
    global configurationJSON
    configurationJSON = Utilities.jsonFromFile('configuration.json')

def getConfigurationValue(key):
    global configurationJSON
    return configurationJSON['configuration'][key]

def __isColumnPresentInConfigurationJSON(parentKeyName, columnKeyName, columnName, projectName):
    global configurationJSON
    projects = configurationJSON['configuration'][parentKeyName]
    project = next(project for project in projects if project['name'] == projectName)
    isColumnPresent = columnName in project[columnKeyName]
    return isColumnPresent

def isColumnPresentInSourceConfigurationJSON(columnName, projectName):
    return __isColumnPresentInConfigurationJSON('sourceProjects', 'ticketSourceColumns', columnName, projectName)

def toggleColumnInSourceConfigurationJSON(columnName, columnInsertionIndex, projectName):
    global configurationJSON
    sourceProjects = configurationJSON['configuration']['sourceProjects']
    project = next(project for project in sourceProjects if project['name'] == projectName)
    if isColumnPresentInSourceConfigurationJSON(columnName, projectName):
        project['ticketSourceColumns'].remove(columnName)
    else:
        project['ticketSourceColumns'].insert(columnInsertionIndex, columnName)

def saveCurrentConfiguration():
    global configurationJSON
    Utilities.jsonToFile('configuration.json', configurationJSON)
