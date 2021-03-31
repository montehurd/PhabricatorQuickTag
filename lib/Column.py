#!/usr/local/bin/python3

class Column:
    def __init__(self, name, project, phid=None):
        self.name = name
        self.phid = phid
        self.tickets = []
        self.project = project
        self.ticketsByID = []
        self.ticketsHTMLByID = {}
        self.currentSourceColumnMenuHTMLLambda = None
        self.nonSourceProjectColumnMenuHTMLLambdas = []
        self.statusMenuHTMLLambda = None
        self.priorityMenuHTMLLambda = None
