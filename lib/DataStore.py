#!/usr/local/bin/python3

import Utilities
from ProjectType import ProjectType

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

def dataStoreKeyForProjectType(projectType):
    if projectType == ProjectType.DESTINATION:
        return 'destinationProjects'
    elif projectType == ProjectType.SOURCE:
        return 'sourceProjects'
    else:
        raise Exception(f'Unhandled projectType: "{projectType}"')

def isProjectColumnPresentInConfigurationJSON(columnPHID, projectPHID, projectType):
    dataStoreKey = dataStoreKeyForProjectType(projectType)
    projects = getConfigurationValue(dataStoreKey)
    project = next(project for project in projects if project['phid'] == projectPHID)
    isColumnPresent = columnPHID in project['columns']
    return isColumnPresent
