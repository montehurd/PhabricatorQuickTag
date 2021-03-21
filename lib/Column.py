#!/usr/local/bin/python3

class Column:
    def __init__(self, name, project, phid=None):
        self.name = name
        self.phid = phid
        self.tickets = []
        self.project = project
        self.menuHTMLLambdas = []
        self.__ticketsRemarkup = ''
        self.ticketsByID = []
        self.ticketsHTMLByID = {}
