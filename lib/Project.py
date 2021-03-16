#!/usr/local/bin/python3

class Project:
    def __init__(self, name, columnNames=[], columnNamesToIgnoreForButtons=[]):
        self.name = name
        self.columnNames = columnNames
        self.phid = None
        self.columns = []
        self.buttonsMenuColumnNames = []
        self.buttonsMenuColumns = []
        self.columnNamesToIgnoreForButtons = columnNamesToIgnoreForButtons
