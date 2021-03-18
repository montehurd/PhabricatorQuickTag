#!/usr/local/bin/python3

import Utilities

__configurationJSON = None

def loadConfiguration():
    global __configurationJSON
    __configurationJSON = Utilities.jsonFromFile('configuration.json')

def getConfigurationValue(key):
    global __configurationJSON
    return __configurationJSON['configuration'][key]

def saveCurrentConfiguration():
    global __configurationJSON
    Utilities.jsonToFile('configuration.json', __configurationJSON)

def saveDestinationProject(projectName):
    destinationProject = getConfigurationValue('destinationProject')
    destinationProject['name'] = projectName
    saveCurrentConfiguration()

def saveSourceProject(projectName):
    sourceProjects = getConfigurationValue('sourceProjects')
    if not any(project['name'] == projectName for project in sourceProjects):
        sourceProjects.insert(0, {
            'name': projectName,
            'columns': []
        })
        saveCurrentConfiguration()
    else:
        print(f'{projectName} already exists in project sources')

def isSourceProjectColumnPresentInConfigurationJSON(columnName, projectName):
    projects = getConfigurationValue('sourceProjects')
    project = next(project for project in projects if project['name'] == projectName)
    isColumnPresent = columnName in project['columns']
    return isColumnPresent

def isDestinationProjectIgnoreColumnPresentInConfigurationJSON(columnName):
    return columnName in getConfigurationValue('destinationProject')['ignoreColumns']
