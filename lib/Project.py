#!/usr/local/bin/python3

class Project:
    def __init__(self, phid, columnNames=[], columnNamesToIgnoreForButtons=[]):
        self.name = None
        self.columnNames = columnNames
        self.phid = phid
        self.columns = []
        self.buttonsMenuColumnNames = []
        self.buttonsMenuColumns = []
        self.columnNamesToIgnoreForButtons = columnNamesToIgnoreForButtons
