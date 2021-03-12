#!/usr/local/bin/python3

import DataStore

def isSourceProjectColumnPresentInConfigurationJSON(columnName, projectName):
    projects = DataStore.getConfigurationValue('sourceProjects')
    project = next(project for project in projects if project['name'] == projectName)
    isColumnPresent = columnName in project['columns']
    return isColumnPresent

def isDestinationProjectIgnoreColumnPresentInConfigurationJSON(columnName):
    return columnName in DataStore.getConfigurationValue('destinationProject')['ignoreColumns']

def isColumnPHIDPresentInTicketJSON(columnPHID, ticketJSON):
    boards = ticketJSON['attachments']['columns']['boards']
    arrayOfColumnPHIDArrays = map(lambda board:
        map(lambda column: column['phid'], board['columns']),
        boards.values()
    )
    arrayOfColumnPHIDs = [item for sublist in arrayOfColumnPHIDArrays for item in sublist]
    return columnPHID in arrayOfColumnPHIDs
