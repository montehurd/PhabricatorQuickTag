#!/usr/local/bin/python3

from ButtonActions import ButtonActions
from ButtonManifest import ButtonManifest
import ButtonManifests, ButtonStateCheckers
import uuid, json, DataStore

def printSuccess():
    print('success!')

def printFailure():
    print('failure!')

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
                lambda ticketID=ticketID :
                    self.buttonActions.showTicketSuccess(ticketID),
                # printSuccess,
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
            failureActions = [
                # printFailure
                lambda ticketID=ticketID :
                    self.buttonActions.showTicketFailure(ticketID),
            ]
        )

    def __rightProjectMenuDiv(self, deleteProjectButtonHTML):
        return f'''
            <div class="right_project_menu">
                {deleteProjectButtonHTML}
            </div>
        '''

    def __wrapWithButtonMenuTag(self, menuTitle, menuButtons, showRightProjectMenu = False, deleteProjectButtonHTML = ''):
        rightProjectMenuDiv = self.__rightProjectMenuDiv(deleteProjectButtonHTML = deleteProjectButtonHTML) if showRightProjectMenu else ''
        mouseOverAndOut = f''' onmouseover="this.classList.add('menu_highlighted');this.querySelectorAll('div.right_project_menu').forEach(e => e.style.visibility = 'visible');" onmouseout="this.classList.remove('menu_highlighted');this.querySelectorAll('div.right_project_menu').forEach(e => e.style.visibility = 'hidden');"''' if showRightProjectMenu else ''
        return f'''
            <div class="menu" {mouseOverAndOut}>
                {menuTitle}
                <br>
                <buttonmenu>
                    {menuButtons}
                </buttonmenu>
                {rightProjectMenuDiv}
            </div>
        '''

    def ticketPriorityButtonMenuHTML(self, menuTitle, ticketID, ticketJSON):
        buttonManifests = list(map(lambda priority: self.__ticketPriorityButtonManifest(
            buttonID = self.__cssSafeGUID(),
            title = priority['name'],
            ticketID = f'T{ticketID}',
            value = priority['keywords'][0],
            isInitiallySelected = ticketJSON['fields']['priority']['name'] == priority['name']
        ), ButtonMenuFactory.__prioritiesData))

        ButtonManifests.add(buttonManifests)

        return self.__wrapWithButtonMenuTag(
            menuTitle = menuTitle,
            menuButtons = ' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))
        )

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
                lambda ticketID=ticketID :
                    self.buttonActions.showTicketSuccess(ticketID),
                lambda buttonID=buttonID :
                    self.buttonActions.selectButton(buttonID),
                lambda buttonID=buttonID :
                    self.buttonActions.deselectOtherButtonsInMenu(buttonID),
                lambda buttonID=buttonID :
                    self.buttonActions.setComment(ticketID, '')
            ],
            failureActions = [
                lambda ticketID=ticketID :
                    self.buttonActions.showTicketFailure(ticketID),
            ]
        )

    def ticketStatusButtonMenuHTML(self, menuTitle, ticketID, ticketJSON):
        buttonManifests = list(map(lambda status: self.__ticketStatusButtonManifest(
            buttonID = self.__cssSafeGUID(),
            title = status['name'],
            ticketID = f'T{ticketID}',
            value = status['value'],
            isInitiallySelected = ticketJSON['fields']['status']['name'] == status['name']
        ), ButtonMenuFactory.__statusesData))

        ButtonManifests.add(buttonManifests)

        return self.__wrapWithButtonMenuTag(
            menuTitle = menuTitle,
            menuButtons = ' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))
        )

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
                lambda ticketID=ticketID :
                    self.buttonActions.showTicketSuccess(ticketID),
                lambda buttonID=buttonID :
                    self.buttonActions.selectButton(buttonID),
                lambda buttonID=buttonID :
                    self.buttonActions.deselectOtherButtonsInMenu(buttonID),
                lambda buttonID=buttonID :
                    self.buttonActions.setComment(ticketID, '')
            ],
            failureActions = [
                lambda ticketID=ticketID :
                    self.buttonActions.showTicketFailure(ticketID),
            ]
        )

    def ticketAddToColumnButtonMenuHTML(self, menuTitle, ticketID, ticketJSON, columns):
        # print(json.dumps(ticketJSON, indent=4))
        buttonManifests = list(map(lambda column: self.__ticketAddToColumnButtonManifest(
            buttonID = self.__cssSafeGUID(),
            title = column.name,
            ticketID = f'T{ticketID}',
            projectPHID = column.project.phid,
            columnPHID = column.phid,
            isInitiallySelected = ButtonStateCheckers.isColumnPHIDPresentInTicketJSON(column.phid, ticketJSON)
        ), columns))

        ButtonManifests.add(buttonManifests)

        return self.__wrapWithButtonMenuTag(
            menuTitle = menuTitle,
            menuButtons = ' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))
        )

    def __toggleSourceProjectColumnInConfigurationJSONButtonManifest(self, buttonID, title, indexOfColumnNameToToggle, allColumnNames, projectName, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [
                self.buttonActions.hideTickets,
                lambda allColumnNames=allColumnNames, indexOfColumnNameToToggle=indexOfColumnNameToToggle, projectName=projectName :
                    self.buttonActions.toggleSourceProjectColumnInConfigurationJSON(allColumnNames, indexOfColumnNameToToggle, projectName)
            ],
            successActions = [
                lambda buttonID=buttonID :
                    self.buttonActions.toggleButton(buttonID)
            ],
            failureActions = [
                printFailure
            ]
        )

    def __removeSourceProjectFromConfigurationJSONButtonManifest(self, projectName):
        buttonID = self.__cssSafeGUID()
        return ButtonManifest(
            id = buttonID,
            title = 'Remove',
            isInitiallySelected = False,
            clickActions = [
                self.buttonActions.hideTickets,
                lambda projectName=projectName :
                    self.buttonActions.removeSourceProjectFromConfigurationJSON(projectName)
            ],
            successActions = [
                lambda buttonID=buttonID :
                    self.buttonActions.deleteMenu(buttonID),
                # self.buttonActions.reloadConfigurationUI,
                printSuccess
            ],
            failureActions = [
                printFailure
            ]
        )

    def toggleSourceProjectColumnInConfigurationButtonMenuHTML(self, menuTitle, allColumnNames, projectName):
        buttonManifests = list(map(lambda indexAndColumnNameTuple: self.__toggleSourceProjectColumnInConfigurationJSONButtonManifest(
            buttonID = self.__cssSafeGUID(),
            title = indexAndColumnNameTuple[1],
            indexOfColumnNameToToggle = indexAndColumnNameTuple[0],
            allColumnNames = allColumnNames,
            projectName = projectName,
            isInitiallySelected = ButtonStateCheckers.isSourceProjectColumnPresentInConfigurationJSON(indexAndColumnNameTuple[1], projectName)
        ), enumerate(allColumnNames)))
        ButtonManifests.add(buttonManifests)

        deleteButtonManifest = self.__removeSourceProjectFromConfigurationJSONButtonManifest(projectName)
        ButtonManifests.add([deleteButtonManifest])

        return self.__wrapWithButtonMenuTag(
            menuTitle = f'''{menuTitle}''',
            menuButtons = f'''
                {' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))}
            ''',
            showRightProjectMenu = True,
            deleteProjectButtonHTML = deleteButtonManifest.html(cssClass = 'delete')
        )

    def __toggleDestinationProjectColumnInConfigurationJSONButtonManifest(self, buttonID, title, indexOfColumnNameToToggle, allColumnNames, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [
                self.buttonActions.hideTickets,
                lambda allColumnNames=allColumnNames, indexOfColumnNameToToggle=indexOfColumnNameToToggle :
                    self.buttonActions.toggleDestinationProjectColumnInConfigurationJSON(allColumnNames, indexOfColumnNameToToggle)
            ],
            successActions = [
                lambda buttonID=buttonID :
                    self.buttonActions.toggleButton(buttonID)
            ],
            failureActions = [
                printFailure
            ]
        )

    def toggleDestinationProjectColumnInConfigurationButtonMenuHTML(self, menuTitle, allColumnNames):
        buttonManifests = list(map(lambda indexAndColumnNameTuple: self.__toggleDestinationProjectColumnInConfigurationJSONButtonManifest(
            buttonID = self.__cssSafeGUID(),
            title = indexAndColumnNameTuple[1],
            indexOfColumnNameToToggle = indexAndColumnNameTuple[0],
            allColumnNames = allColumnNames,
            isInitiallySelected = not ButtonStateCheckers.isDestinationProjectIgnoreColumnPresentInConfigurationJSON(indexAndColumnNameTuple[1])
        ), enumerate(allColumnNames)))

        ButtonManifests.add(buttonManifests)

        return self.__wrapWithButtonMenuTag(
            menuTitle = menuTitle,
            menuButtons = ' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))
        )
