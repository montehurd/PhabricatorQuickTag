#!/usr/local/bin/python3

import Utilities

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

    def __title(self):
        return f'''{self.project.name} > {self.name} {'' if self.project.status != 'closed' else ' (CLOSED)'}'''

    def __subtitle(self, destinationProjectsCount):
        destinationProjectName = 'Ticket Destination' if destinationProjectsCount > 0 else None
        ticketsInSourceProjectString = f"""{len(self.tickets)} ticket{'' if len(self.tickets) == 1 else 's'} currently in <b>{self.project.name} > {self.name}</b>"""
        destinationProjectString = f" not already appearing in a <b>{destinationProjectName}</b> column" if destinationProjectName != None else ''
        return f"{ticketsInSourceProjectString}{destinationProjectString}"

    def __ticketsHTML(self):
        allTicketsHTML = []
        for ticketID, ticketHTML in self.ticketsHTMLByID.items():
            ticketJSON = self.ticketsByID[int(ticketID)]
            currentSourceColumnMenuHTML = self.currentSourceColumnMenuHTMLLambda(ticketID = ticketID, ticketJSON = ticketJSON)
            nonSourceProjectColumnMenuHTML = ''.join(list(map(lambda menuHTMLLambda: menuHTMLLambda(ticketID = ticketID, ticketJSON = ticketJSON), self.nonSourceProjectColumnMenuHTMLLambdas)))
            statusMenuHTML = self.statusMenuHTMLLambda(ticketID = ticketID, ticketJSON = ticketJSON)
            priorityMenuHTML = self.priorityMenuHTMLLambda(ticketID = ticketID, ticketJSON = ticketJSON)
            assignedTo = self.userNames.get(ticketJSON['fields']['ownerPHID'], 'None')
            authoredBy = self.userNames.get(ticketJSON['fields']['authorPHID'], 'None')
            dateCreatedTimeStamp = ticketJSON['fields'].get('dateCreated', None)
            dateCreatedString = f' on {Utilities.localTimezoneDateStringFromTimeStamp(dateCreatedTimeStamp)}' if dateCreatedTimeStamp != None else ''
            wrappedTicketHTML = self.__ticketHTML(ticketID, ticketHTML, currentSourceColumnMenuHTML, nonSourceProjectColumnMenuHTML, statusMenuHTML, priorityMenuHTML, assignedTo, authoredBy, dateCreatedString)
            allTicketsHTML.append(wrappedTicketHTML)
        return ''.join(allTicketsHTML)

    def __ticketHTML(self, ticketID, ticketHTML, currentSourceColumnMenuHTML, nonSourceProjectColumnMenuHTML, statusMenuHTML, priorityMenuHTML, assignedTo, authoredBy, dateCreatedString):
        return f'''
            <div class=ticket id="T{ticketID}">
              <button class="toggle_ticket expanded" onclick="__toggleCollapseExpandButton(this)" title="Toggle ticket"></button>
              {ticketHTML}
              <div class=ticket_users>
                  <span class=ticket_assigned_to>
                      <span class=ticket_user_heading>Assigned to:</span>
                      {assignedTo}
                  </span>
                  <span class=ticket_authored_by>
                      <span class=ticket_user_heading>Authored by:</span>
                      {authoredBy}
                      {dateCreatedString}
                  </span>
              </div>
              <div class="quick_options phui-tag-core phui-tag-color-object">
                <span class=buttonActionMessage id="buttonActionMessage{ticketID}"></span>
                <h2>Quick options</h2>
                <div class="menus">
                    {currentSourceColumnMenuHTML}
                    <div class="destination_projects_menus">
                        {nonSourceProjectColumnMenuHTML}
                    </div>
                    {statusMenuHTML}
                    {priorityMenuHTML}
                </div>
                Comment: ( recorded with any <strong>Quick options</strong> chosen above )
                <br>
                <textarea id="ticketID{ticketID}" style="height: 70px; width: 100%;"></textarea>
              </div>
            </div>
        '''
        
    def html(self, destinationProjectsCount):
        return f'''
            <div class="column_source">
                <span class="column_identifier">
                    {self.__title()}
                </span>
            </div>
            <div class=project_column>
                <div class=column_subtitle>
                    {self.__subtitle(destinationProjectsCount)}
                </div>
                {self.__ticketsHTML()}
            </div>
        '''