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

def saveDestinationProjectPHID(projectPHID):
    destinationProject = getConfigurationValue('destinationProject')
    destinationProject['phid'] = projectPHID
    saveCurrentConfiguration()

def saveSourceProjectPHID(projectPHID):
    sourceProjects = getConfigurationValue('sourceProjects')
    if not any(project['phid'] == projectPHID for project in sourceProjects):
        sourceProjects.insert(0, {
            'phid': projectPHID,
            'columns': []
        })
        saveCurrentConfiguration()
    else:
        print(f'{projectPHID} already exists in project sources')

def isSourceProjectColumnPresentInConfigurationJSON(columnName, projectPHID):
    projects = getConfigurationValue('sourceProjects')
    project = next(project for project in projects if project['phid'] == projectPHID)
    isColumnPresent = columnName in project['columns']
    return isColumnPresent

def isDestinationProjectIgnoreColumnPresentInConfigurationJSON(columnName):
    return columnName in getConfigurationValue('destinationProject')['ignoreColumns']
