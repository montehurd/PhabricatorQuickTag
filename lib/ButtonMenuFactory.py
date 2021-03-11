#!/usr/local/bin/python3

from ButtonActions import ButtonActions
from ButtonManifest import ButtonManifest
import ButtonManifests
import uuid, json

def printSuccess():
    print('success!')

def printFailure():
    print('failure!')

# functions to return ButtonManifest(s) with clickActions configured for respective button types
class ButtonMenuFactory:

    __prioritiesData = []
    __statusesData = []

    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.buttonActions = ButtonActions(self.fetcher)

        # use and check class vars size here so fetch only happens once no matter how many inits happen
        if len(ButtonMenuFactory.__prioritiesData) == 0:
            ButtonMenuFactory.__prioritiesData = self.fetcher.fetchPriorities()
        if len(ButtonMenuFactory.__statusesData) == 0:
            ButtonMenuFactory.__statusesData = self.fetcher.fetchStatuses()

    def __cssSafeGUID(self):
        return f'_{uuid.uuid4().hex}'

    def __ticketPriorityButtonManifest(self, buttonID, title, ticketID, value, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [ # lambda currying: https://stackoverflow.com/a/452659
                # self.buttonActions.hideTickets,
                lambda ticketID=ticketID, value=value :
                    self.buttonActions.updateTicketPriority(ticketID, value),
                    # self.buttonActions.updateTicketPriority(ticketID, value, self.getComment(ticketID)),
                lambda title=title :
                    print(title)
            ],
            successActions = [
                printSuccess,
                # self.buttonActions.showTickets,
                lambda buttonID=buttonID :
                    # self.buttonActions.toggleButton(buttonID),
                    self.buttonActions.selectButton(buttonID),
                # self.reload
                lambda buttonID=buttonID :
                    self.buttonActions.deselectOtherButtonsInMenu(buttonID),
                lambda buttonID=buttonID :
                    self.buttonActions.setComment(ticketID, '')
            ],
            failureActions = [printFailure]
        )

    def ticketPriorityButtonMenuHTML(self, ticketID, ticketJSON):
        buttonManifests = list(map(lambda priority: self.__ticketPriorityButtonManifest(
            buttonID = self.__cssSafeGUID(),
            title = priority['name'],
            ticketID = f'T{ticketID}',
            value = priority['keywords'][0],
            isInitiallySelected = ticketJSON['fields']['priority']['name'] == priority['name']
        ), ButtonMenuFactory.__prioritiesData))

        ButtonManifests.add(buttonManifests)

        return f'''
            <buttonmenu>
                {' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))}
            </buttonmenu>
        '''


    def __ticketStatusButtonManifest(self, buttonID, title, ticketID, value, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [
                lambda ticketID=ticketID, value=value :
                    self.buttonActions.updateTicketStatus(ticketID, value)
            ],
            successActions = [
                printSuccess,
                lambda buttonID=buttonID :
                    self.buttonActions.selectButton(buttonID),
                lambda buttonID=buttonID :
                    self.buttonActions.deselectOtherButtonsInMenu(buttonID),
                lambda buttonID=buttonID :
                    self.buttonActions.setComment(ticketID, '')
            ],
            failureActions = [printFailure]
        )

    def ticketStatusButtonMenuHTML(self, ticketID, ticketJSON):
        buttonManifests = list(map(lambda status: self.__ticketStatusButtonManifest(
            buttonID = self.__cssSafeGUID(),
            title = status['name'],
            ticketID = f'T{ticketID}',
            value = status['value'],
            isInitiallySelected = ticketJSON['fields']['status']['name'] == status['name']
        ), ButtonMenuFactory.__statusesData))

        ButtonManifests.add(buttonManifests)

        return f'''
            <buttonmenu>
                {' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))}
            </buttonmenu>
        '''


















    def __ticketAddToColumnButtonManifest(self, buttonID, title, ticketID, projectPHID, columnPHID, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected, # maybe could make the button toggle by checking isInitiallySelected and if so use click only the 'removeTicketFromColumn' clickAction (would need to write a 'removeTicketFromColumn' action) - would have to use the existing 'toggleButton' success action instead of selectButton
            clickActions = [
                lambda ticketID=ticketID, projectPHID=projectPHID :
                    self.buttonActions.addTicketToProject(ticketID, projectPHID),
                lambda ticketID=ticketID, columnPHID=columnPHID :
                    self.buttonActions.addTicketToColumn(ticketID, columnPHID)
            ],
            successActions = [
                printSuccess,
                lambda buttonID=buttonID :
                    self.buttonActions.selectButton(buttonID),
                lambda buttonID=buttonID :
                    self.buttonActions.deselectOtherButtonsInMenu(buttonID),
                lambda buttonID=buttonID :
                    self.buttonActions.setComment(ticketID, '')
            ],
            failureActions = [printFailure]
        )


# ClickEndpoint(name = 'maniphest.edit', key = 'column', value = [column.phid], stateCheckerLambda = currentColumnButtonStateChecker)
    def __currentColumnButtonStateChecker(self, columnPHID, ticketJSON):
        boards = ticketJSON['attachments']['columns']['boards']
        # print('====')
        # print(json.dumps(boards, indent=4))
        # print('====')
        # return False
        arrayOfColumnPHIDArrays = map(lambda board:
            map(lambda column: column['phid'], board['columns']),
            boards.values()
        )
        arrayOfColumnPHIDs = [item for sublist in arrayOfColumnPHIDArrays for item in sublist]
        buttonColumnPHID = columnPHID # endpoint.value[0]
        return buttonColumnPHID in arrayOfColumnPHIDs

    def ticketAddToColumnButtonMenuHTML(self, ticketID, ticketJSON, columns):
        print(json.dumps(ticketJSON, indent=4))
        buttonManifests = list(map(lambda column: self.__ticketAddToColumnButtonManifest(
            buttonID = self.__cssSafeGUID(),
            title = column.name,
            ticketID = f'T{ticketID}',
            projectPHID = column.project.phid,
            columnPHID = column.phid,
            # isInitiallySelected = False, #ticketJSON['fields']['status']['name'] == status['name']     TODO - inspect ticketJSON here to see how to check if column.phid is in ticketJSON's attachments
            isInitiallySelected = self.__currentColumnButtonStateChecker(column.phid, ticketJSON)
        ), columns))

        ButtonManifests.add(buttonManifests)

        return f'''
            <buttonmenu>
                {' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))}
            </buttonmenu>
        '''








    # def addTicketToProject(self, ticketID, projectPHID):
    # def addTicketToColumn(self, ticketID, columnPHID):






    # TODO: implement the following actions:


    # __configurationSourceColumnToggleButtonManifest(self, buttonID, title, projectName, columnName, isInitiallySelected = False)
    # configurationSourceColumnToggleButtonManifests(self, ticketID)

    # __configurationDestinationColumnToggleButtonManifest(self, buttonID, title, projectName, columnName, isInitiallySelected = False)
    # configurationDestinationColumnToggleButtonManifests(self, ticketID)

    # __ticketSourceColumnButtonManifest(self, buttonID, title, ticketID, newColumnPHID, isInitiallySelected = False)
    # ticketSourceColumnButtonManifests(self, ticketID)

    # __ticketAddToProjectColumnButtonManifest(self, buttonID, title, ticketID, projectPHID, newColumnPHID, isInitiallySelected = False)
    # ticketAddToProjectColumnButtonManifests(self, ticketID)

    # a new show message action for errors and success - show it as a floating div? maybe in upper corner, or bar on bottom or top of screen?
        # just one or one for error and one for success? the error one could show message? or just rely on console for that for now?


    # TODO:
    # move new classes out of this file when done tweaking them
