#!/usr/local/bin/python3

class Project:
    def __init__(self, phid, columnPHIDs=[]):
        self.name = None
        self.columnPHIDs = columnPHIDs
        self.phid = phid
        self.columns = []
        self.buttonsMenuColumns = []
        self.status = None
        self.icon = None
