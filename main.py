#!/usr/local/bin/python3

import sys, webview
sys.path.insert(0, './lib')
from Fetcher import Fetcher
from Project import Project
from WebviewController import WebviewController
import DataStore

def getDehydratedSourceProjects(fetcher):
    return list(map(lambda projectJSON:
        Project(
            name = projectJSON['name'],
            columnNames = projectJSON['ticketSourceColumns'],
            fetcher = fetcher
        ),
        DataStore.getConfigurationValue('sourceProjects')
    ))

def getDehydratedDestinationProject(fetcher):
    return Project(
        name = DataStore.getConfigurationValue('destinationProject')['name'],
        columnNamesToIgnoreForButtons = DataStore.getConfigurationValue('destinationProject')['ignoreColumns'],
        fetcher = fetcher
    )

if __name__ == '__main__':
    DataStore.loadConfiguration()
    fetcher = Fetcher(DataStore.getConfigurationValue('url'), DataStore.getConfigurationValue('token'))
    webviewController = WebviewController(
        webview = webview,
        sourceProjects = getDehydratedSourceProjects(fetcher),
        destinationProject = getDehydratedDestinationProject(fetcher),
        fetcher = fetcher
    )
