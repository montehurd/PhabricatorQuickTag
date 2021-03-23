#!/usr/local/bin/python3

class Column:
    def __init__(self, name, project, phid=None):
        self.name = name
        self.phid = phid
        self.tickets = []
        self.project = project
        self.menuHTMLLambdas = []
        self.ticketsByID = []
        self.ticketsHTMLByID = {}
