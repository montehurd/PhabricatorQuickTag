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

    def fetchPHID(self):
        self.phid = self.fetcher.fetchColumnPHID(self.name, self.project.phid)

    def __addWrapperDivAndMenuToTicketHTML(self, match):
        ticketID = match.group(1)
        ticketHTML = match.group(2)
        ticketJSON = self.ticketsByID[int(ticketID)]
        return f'''
            <div class=ticket id="T{ticketID}">
              <button class=hide onclick="this.closest('div#T{ticketID}').remove()">Hide</button>
              {ticketHTML}
              {self.__allMenusHTML(ticketID, ticketJSON)}
            </div>
        '''

    def __allTicketsRemarkup(self):
        # https://secure.phabricator.com/book/phabricator/article/remarkup/
        return ''.join(map(lambda item:
f'''TICKET_START:{item['id']}:
= T{item['id']} =
== {item['fields']['name']} ==

{item['fields']['description']['raw']}
TICKET_END'''
        , self.tickets))

    def fetchTicketsHTML(self, destinationProjectName):
        ticketsHTML = f"""
            <div class=column_subtitle>
                {len(self.tickets)} ticket{'' if len(self.tickets) == 1 else 's'} currently in <b>{self.project.name} > {self.name}</b> not already appearing in a <b>{destinationProjectName}</b> column{'.' if len(self.tickets) == 0 else ':'}
            </div>
            {self.fetcher.fetchHTMLFromColumnTicketsRemarkup(self.__allTicketsRemarkup())}
        """

        self.ticketsHTMLIncludingWrapperDivsAndMenus = re.sub(pattern=r'TICKET_START:(.*?):(.*?)TICKET_END', repl=self.__addWrapperDivAndMenuToTicketHTML, string=ticketsHTML, flags=re.DOTALL)

    def fetchTickets(self, destinationProjectPHID):
        tickets = list(self.fetcher.fetchColumnTickets(self.phid))
        # dict with ticketID as key and ticketJSON as value (excluding tickets already tagged with destinationProjectPHID)
        ticketsByID = dict((x['id'], x) for x in tickets if not destinationProjectPHID in x['attachments']['projects']['projectPHIDs'])
        self.ticketsByID = ticketsByID
        # print(json.dumps(self.ticketsByID, indent=4))
        self.tickets = self.ticketsByID.values()

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
