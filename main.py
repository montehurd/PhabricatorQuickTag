#!/usr/local/bin/python3

import sys, webview
sys.path.insert(0, './lib')
import Utilities
from Fetcher import Fetcher
from Project import Project
from WebviewController import WebviewController

configurationJSON = None
def getConfigurationValue(key):
    global configurationJSON
    if configurationJSON == None:
        configurationJSON = Utilities.jsonFromFile('configuration.json')
    return configurationJSON['configuration'][key]

def getDehydratedSourceProjects(fetcher):
    return list(map(lambda projectJSON:
        Project(
            name = projectJSON['name'],
            columnNames = projectJSON['ticketSourceColumns'],
            fetcher = fetcher
        ),
        getConfigurationValue('sourceProjects')
    ))

def getDehydratedDestinationProject(fetcher):
    return Project(
        name = getConfigurationValue('destinationProject')['name'],
        columnNamesToIgnoreForButtons = getConfigurationValue('destinationProject')['ignoreColumns'],
        fetcher = fetcher
    )

if __name__ == '__main__':
    fetcher = Fetcher(getConfigurationValue('url'), getConfigurationValue('token'))
    webviewController = WebviewController(
        webview = webview,
        sourceProjects = getDehydratedSourceProjects(fetcher),
        destinationProject = getDehydratedDestinationProject(fetcher),
        fetcher = fetcher
    )
