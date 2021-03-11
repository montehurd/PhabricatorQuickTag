#!/usr/local/bin/python3

import re, json
# from ButtonMenuFactory import ButtonMenuFactory

class Column:
    def __init__(self, name, project, phid=None, menus=[], fetcher = None):
        self.name = name
        self.phid = phid
        self.tickets = []
        # self.ticketsByID = []
        self.project = project
        self.ticketsHTMLIncludingWrapperDivsAndMenus = ''
        self.menus = menus
        self.fetcher = fetcher
        # self.newMenusHTML = 'BEEP'

        self.menuHTMLLambdas = []

    def fetchPHID(self):
        self.phid = self.fetcher.fetchColumnPHID(self.name, self.project.phid)

    def addWrapperDivAndMenuToTicketHTML(self, match):
        ticketID = match.group(1)
        ticketHTML = match.group(2)
        ticketJSON = self.ticketsByID[int(ticketID)]
        return f'''
            <div class=ticket id="T{ticketID}">
              <button class=hide onclick="this.closest('div#T{ticketID}').remove()">Hide</button>
              {ticketHTML}
              {self.allMenusHTML(ticketID, ticketJSON)}
            </div>
        '''

    def allTicketsRemarkup(self):
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
            {self.fetcher.fetchHTMLFromColumnTicketsRemarkup(self.allTicketsRemarkup())}
        """

        self.ticketsHTMLIncludingWrapperDivsAndMenus = re.sub(pattern=r'TICKET_START:(.*?):(.*?)TICKET_END', repl=self.addWrapperDivAndMenuToTicketHTML, string=ticketsHTML, flags=re.DOTALL)

    def fetchTickets(self, destinationProjectPHID):
        tickets = list(self.fetcher.fetchColumnTickets(self.phid))
        # dict with ticketID as key and ticketJSON as value (excluding tickets already tagged with destinationProjectPHID)
        ticketsByID = dict((x['id'], x) for x in tickets if not destinationProjectPHID in x['attachments']['projects']['projectPHIDs'])
        self.ticketsByID = ticketsByID
        # print(json.dumps(self.ticketsByID, indent=4))
        self.tickets = self.ticketsByID.values()

    # Consider: move this method to ClickEndpoint (or Button?) object
    def buttonActionForEndpoint(self, endpoint, ticketID, menuID, savesComment = True):
        needsValueArgumentInArray = False
        value = endpoint.value
        if isinstance(value, list):
            needsValueArgumentInArray = True
            value = endpoint.value[0]
        needsValueArgumentInArrayString = 'true' if needsValueArgumentInArray else 'false'
        savesCommentString = 'true' if savesComment else 'false'
        return f'''buttonAction('{menuID}', {ticketID}, '{endpoint.name}', '{endpoint.key}', '{value}', {needsValueArgumentInArrayString}, {savesCommentString})'''

    # Consider: move this method to ClickEndpoint (or Button?) object
    def buttonIDForEndpoint(self, endpoint, ticketID, menuID):
        value = endpoint.value[0] if isinstance(endpoint.value, list) else endpoint.value
        return f'{menuID}:{ticketID}:{endpoint.name}:{endpoint.key}:{value}'

    # Consider: move this method to ClickEndpoint (or Button?) object
    def buttonSelectionStateCSSForEndpoint(self, endpoint, ticketJSON, title):
        isSelected = False if endpoint.stateCheckerLambda == None else endpoint.stateCheckerLambda(endpoint, ticketJSON, title)
        return "class='selected'" if isSelected else ''

    def buttonHTML(self, button, ticketID, ticketJSON, menuID):
        # need to know what to check for in ticketJSON for checking if the button should appear in selected state.
        # the endpoint at 'stateEndpointIndex' controls this state. look to it for what should be selected, also used for button 'id' string.
        buttonStateEndpoint = button.clickEndpoints[button.stateEndpointIndex]
        buttonOnClickActions = list(map(lambda endpoint: self.buttonActionForEndpoint(endpoint, ticketID, menuID, endpoint == buttonStateEndpoint), button.clickEndpoints))
        buttonSelectionStateCSS = self.buttonSelectionStateCSSForEndpoint(buttonStateEndpoint, ticketJSON, button.title)
        buttonID = self.buttonIDForEndpoint(buttonStateEndpoint, ticketID, menuID)
        return f'''<button id="{buttonID}" {buttonSelectionStateCSS} onclick="{';'.join(buttonOnClickActions)}" onblur="showButtonActionMessage({ticketID}, '')">{button.title}</button>'''

    def menuHTML(self, ticketID, menu, ticketJSON):
        buttonsHTML = ''.join(
            list(map(lambda button: self.buttonHTML(button, ticketID, ticketJSON, menu.id), menu.buttons))
        )
        return f'''
            <div class="menu">
            {menu.title}:
            <br>
            {buttonsHTML}
            </div>
            '''

    def allMenusHTML(self, ticketID, ticketJSON):
        menus = ''.join(
            list(map(lambda menu: self.menuHTML(ticketID, menu, ticketJSON), self.menus))
        )

        # print('\n\n======')
        # print('COLUMNS: From manifest:')
        # for column in self.project.columns:
        #     print(f'''\t{column.name} : {column.phid}''')
        # print('COLUMNS: Current column on source project:')
        # for column in self.project.buttonsMenuColumns:
        #     print(f'''\t{column.name} : {column.phid}''')
        # print('======\n\n')

        # print(self.project.buttonsMenuColumnNames)
        # print(json.dumps(self.project.buttonsMenuColumns, indent=4))


                # <br>{ButtonMenuFactory(self.fetcher).ticketPriorityButtonMenuHTML(ticketID, ticketJSON)}<br><br>
                # <br>{ButtonMenuFactory(self.fetcher).ticketStatusButtonMenuHTML(ticketID, ticketJSON)}<br><br>

                # {self.newMenusHTML}


# TODO:
# pass column an array of 'menuHTMLLambdas', that way can curry project info in, then execute those lambdas here adding ticketID and ticketJSON


        newMenuHTML = ''.join(list(map(lambda menuHTMLLambda: menuHTMLLambda(ticketID, ticketJSON), self.menuHTMLLambdas)))



        return f'''
            <div class="menus phui-tag-core phui-tag-color-object">
                <span class=buttonActionMessage id="buttonActionMessage{ticketID}"></span>
                <h2>Quick options</h2>
                {menus}
                {newMenuHTML}
                Comment: ( recorded with any <strong>Quick options</strong> chosen above )
                <br>
                <textarea id="ticketID{ticketID}" style="height: 70px; width: 100%;"></textarea>
            </div>
      '''
