#!/usr/local/bin/python3

class Column:
    def __init__(self, name=None, project=None, phid=None):
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
        self.userNames = {}
        self.status = None
