#!/usr/local/bin/python3

from Column import Column

class Project:
    def __init__(self, name, columnNames=[], columnNamesToIgnoreForButtons=[], fetcher = None):
        self.name = name
        self.columnNames = columnNames
        self.phid = None
        self.columns = []
        self.ticketsByID = []
        self.buttonsMenuColumnNames = []
        self.buttonsMenuColumns = []
        self.columnNamesToIgnoreForButtons = columnNamesToIgnoreForButtons
        self.fetcher = fetcher

    def fetchPHID(self):
        self.phid = self.fetcher.fetchProjectPHID(self.name)

    def fetchButtonsMenuColumns(self):
        columnsData = self.fetcher.fetchColumnsData(self, self.columnNamesToIgnoreForButtons)
        self.buttonsMenuColumnNames = list(map(lambda x: x['fields']['name'], columnsData))
        self.buttonsMenuColumns = list(map(lambda x: Column(x['fields']['name'], self, x['phid']), columnsData))
