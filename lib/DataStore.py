#!/usr/local/bin/python3

import Utilities

configurationJSON = None

def loadConfiguration():
    global configurationJSON
    configurationJSON = Utilities.jsonFromFile('configuration.json')

def getConfigurationValue(key):
    global configurationJSON
    return configurationJSON['configuration'][key]

def __isSourceProjectColumnPresentInConfigurationJSON(parentKeyName, columnKeyName, columnName, projectName):
    projects = getConfigurationValue(parentKeyName)
    project = next(project for project in projects if project['name'] == projectName)
    isColumnPresent = columnName in project[columnKeyName]
    return isColumnPresent

def isSourceProjectColumnPresentInConfigurationJSON(columnName, projectName):
    return __isSourceProjectColumnPresentInConfigurationJSON('sourceProjects', 'columns', columnName, projectName)

def toggleSourceProjectColumnInConfigurationJSON(columnName, columnInsertionIndex, projectName):
    sourceProjects = getConfigurationValue('sourceProjects')
    project = next(project for project in sourceProjects if project['name'] == projectName)
    if isSourceProjectColumnPresentInConfigurationJSON(columnName, projectName):
        project['columns'].remove(columnName)
    else:
        project['columns'].insert(columnInsertionIndex, columnName)

def isDestinationProjectIgnoreColumnPresentInConfigurationJSON(columnName):
    return columnName in getConfigurationValue('destinationProject')['ignoreColumns']

def toggleDestinationProjectColumnInConfigurationJSON(columnName, columnInsertionIndex):
    project = getConfigurationValue('destinationProject')
    if isDestinationProjectIgnoreColumnPresentInConfigurationJSON(columnName):
        project['ignoreColumns'].remove(columnName)
    else:
        project['ignoreColumns'].insert(columnInsertionIndex, columnName)

def saveCurrentConfiguration():
    global configurationJSON
    Utilities.jsonToFile('configuration.json', configurationJSON)
