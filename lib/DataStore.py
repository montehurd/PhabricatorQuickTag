#!/usr/local/bin/python3

import Utilities

configurationJSON = None

def loadConfiguration():
    global configurationJSON
    configurationJSON = Utilities.jsonFromFile('configuration.json')

def getConfigurationValue(key):
    global configurationJSON
    return configurationJSON['configuration'][key]

def isColumnAlreadyPresentInConfigurationJSON(parentKeyName, columnKeyName, columnName, projectName):
    global configurationJSON
    projects = configurationJSON['configuration'][parentKeyName]
    project = next(project for project in projects if project['name'] == projectName)
    isColumnAlreadyPresent = columnName in project[columnKeyName]
    return isColumnAlreadyPresent

def isColumnAlreadyPresentInSourceConfigurationJSON(columnName, projectName):
    return isColumnAlreadyPresentInConfigurationJSON('sourceProjects', 'ticketSourceColumns', columnName, projectName)

def toggleColumnInSourceConfigurationJSON(columnName, columnInsertionIndex, projectName):
    global configurationJSON
    sourceProjects = configurationJSON['configuration']['sourceProjects']
    project = next(project for project in sourceProjects if project['name'] == projectName)
    if isColumnAlreadyPresentInSourceConfigurationJSON(columnName, projectName):
        project['ticketSourceColumns'].remove(columnName)
    else:
        project['ticketSourceColumns'].insert(columnInsertionIndex, columnName)

def saveCurrentConfiguration():
    global configurationJSON
    Utilities.jsonToFile('configuration.json', configurationJSON)
