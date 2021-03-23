#!/usr/local/bin/python3

class Project:
    def __init__(self, phid, columnPHIDs=[], columnPHIDsToIgnoreForButtons=[]):
        self.name = None
        self.columnPHIDs = columnPHIDs
        self.phid = phid
        self.columns = []
        self.buttonsMenuColumns = []
        self.columnPHIDsToIgnoreForButtons = columnPHIDsToIgnoreForButtons
