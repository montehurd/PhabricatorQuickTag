#!/usr/local/bin/python3

import re, json

class Column:
    def __init__(self, name, project, phid=None, fetcher = None):
        self.name = name
        self.phid = phid
        self.tickets = []
        self.project = project
        self.ticketsHTMLIncludingWrapperDivsAndMenus = ''
        self.fetcher = fetcher
        self.menuHTMLLambdas = []
        self.__ticketsRemarkup = ''
        self.ticketsByID = []

    @property
    def ticketsRemarkup(self):
        return ''.join(map(lambda item:
f''' TICKET_START:{item['id']}:
= T{item['id']} =
== {item['fields']['name']} ==

{item['fields']['description']['raw']}

TICKET_END '''
        , self.tickets))

    def __fetchTicketsHTMLByID(self):
        ticketsHTML = self.fetcher.fetchHTMLFromColumnTicketsRemarkup(self.ticketsRemarkup)
        allTicketsHTML = re.split(pattern=r'(<p>)?TICKET_START:(.*?):(</p>)?(.*?)(<p>)?TICKET_END(</p>)?', string=ticketsHTML, flags=re.DOTALL)
        ticketsHTMLByID = {}
        if len(allTicketsHTML) < 7:
            return ticketsHTMLByID
        for i in range(0, len(allTicketsHTML) - 1, 7):
            ticketID = allTicketsHTML[i + 2]
            ticketHTML = allTicketsHTML[i + 4]
            ticketsHTMLByID[ticketID] = ticketHTML.strip()
        return ticketsHTMLByID

    def __headingHTML(self, destinationProjectName = None):
        ticketsInSourceProjectString = f"""{len(self.tickets)} ticket{'' if len(self.tickets) == 1 else 's'} currently in <b>{self.project.name} > {self.name}</b>"""
        destinationProjectString = f""" not already appearing in a <b>{destinationProjectName}</b> column{'.' if len(self.tickets) == 0 else ''}""" if destinationProjectName != None else ''
        return f"""
            <div class=column_subtitle>
                {ticketsInSourceProjectString}{destinationProjectString}:
            </div>
        """

    def __wrappedTicketHTML(self, ticketID, ticketHTML):
        return f'''
            <div class=ticket id="T{ticketID}">
              <button class=hide onclick="this.closest('div#T{ticketID}').remove()">Hide</button>
              {ticketHTML}
              {self.__allMenusHTML(ticketID, self.ticketsByID[int(ticketID)])}
            </div>
        '''

    def __allMenusHTML(self, ticketID, ticketJSON):
        menusHTML = ''.join(list(map(lambda menuHTMLLambda: menuHTMLLambda(ticketID, ticketJSON), self.menuHTMLLambdas)))
        return f'''
            <div class="menus phui-tag-core phui-tag-color-object">
                <span class=buttonActionMessage id="buttonActionMessage{ticketID}"></span>
                <h2>Quick options</h2>
                {menusHTML}
                Comment: ( recorded with any <strong>Quick options</strong> chosen above )
                <br>
                <textarea id="ticketID{ticketID}" style="height: 70px; width: 100%;"></textarea>
            </div>
      '''

    def fetchTicketsHTML(self, destinationProjectName = None):
        ticketsHTMLByID = self.__fetchTicketsHTMLByID()
        wrappedTicketsHTML = ''.join([self.__wrappedTicketHTML(ticketID, ticketHTML) for ticketID, ticketHTML in ticketsHTMLByID.items()])
        self.ticketsHTMLIncludingWrapperDivsAndMenus = f'''
            {self.__headingHTML(destinationProjectName)}
            {wrappedTicketsHTML}
        '''
