#!/usr/local/bin/python3

import ButtonManifestRegistry, Utilities, DataStore
from ButtonManifest import ButtonManifest

class ButtonFactory:
    def __init__(self, buttonActions):
        self.buttonActions = buttonActions

    def __reloadButtonManifest(self):
        return ButtonManifest(
            id = Utilities.cssSafeGUID(),
            title = 'Reload Tickets',
            isInitiallySelected = False,
            clickActions = [
                self.buttonActions.showLoadingIndicator,
                self.buttonActions.reload
            ],
            successActions = [
                self.buttonActions.hideLoadingIndicator,
                self.buttonActions.showTickets,
                self.buttonActions.printSuccess
            ],
            failureActions = [
                self.buttonActions.hideLoadingIndicator,
                self.buttonActions.printFailure
            ]
        )

    def reloadButtonHTML(self):
        buttonManifest = self.__reloadButtonManifest()
        ButtonManifestRegistry.add([buttonManifest])
        return buttonManifest.html(cssClass = 'reload_tickets')

    def __urlAndTokenSaveButtonManifest(self):
        return ButtonManifest(
            id = Utilities.cssSafeGUID(),
            title = 'Save',
            isInitiallySelected = False,
            clickActions = [
                self.buttonActions.showLoadingIndicator,
                self.buttonActions.saveURLAndToken
            ],
            successActions = [
                self.buttonActions.hideLoadingIndicator,
                self.buttonActions.reloadFetcher,
                self.buttonActions.refetchPrioritiesAndStatuses,
                self.buttonActions.clearSourceAndDestinationProjects,
                self.buttonActions.hideTickets,
                self.buttonActions.refetchUpstreamCSSLinkURL,
                self.buttonActions.resetUpstreamBaseURL,
                self.buttonActions.reloadConfigurationUI,
                self.buttonActions.printSuccess
            ],
            failureActions = [
                self.buttonActions.hideLoadingIndicator,
                self.buttonActions.printFailure
            ]
        )

    def urlAndTokenSaveButtonHTML(self):
        buttonManifest = self.__urlAndTokenSaveButtonManifest()
        ButtonManifestRegistry.add([buttonManifest])
        return buttonManifest.html(cssClass = 'save_url_and_token')

    def __projectSearchResultButtonManifest(self, projectName, projectPHID, mode):
        return ButtonManifest(
            id = Utilities.cssSafeGUID(),
            title = projectName,
            isInitiallySelected = False,
            clickActions = [
                self.buttonActions.showLoadingIndicator,
                lambda projectPHID=projectPHID, mode=mode :
                    self.buttonActions.saveProjectSearchChoice(projectPHID, mode)
            ],
            successActions = [
                self.buttonActions.hideLoadingIndicator,
                self.buttonActions.hideProjectSearch,
                self.buttonActions.reloadConfigurationUI
            ],
            failureActions = [
                self.buttonActions.hideLoadingIndicator,
                self.buttonActions.printFailure
            ]
        )

    def projectSearchResultButtonHTML(self, title, phid, mode):
        buttonManifest = self.__projectSearchResultButtonManifest(title, phid, mode)
        ButtonManifestRegistry.add([buttonManifest])
        return buttonManifest.html(cssClass = 'projects_search_result')

    def __showProjectSearchButtonManifest(self, title, mode):
        return ButtonManifest(
            id = Utilities.cssSafeGUID(),
            title = title,
            isInitiallySelected = False,
            clickActions = [
                self.buttonActions.resetProjectSearch,
                lambda mode=mode :
                    self.buttonActions.showProjectSearch(mode = mode, title = title)
            ],
            successActions = [
                self.buttonActions.printSuccess
            ],
            failureActions = [
                self.buttonActions.printFailure
            ]
        )

    def showProjectSearchButtonHTML(self, title, mode):
        buttonManifest = self.__showProjectSearchButtonManifest(title, mode)
        ButtonManifestRegistry.add([buttonManifest])
        return buttonManifest.html(cssClass = 'add')

    def __rightProjectMenuDiv(self, deleteProjectButtonHTML):
        return f'''
            <div class="right_project_menu">
                {deleteProjectButtonHTML}
            </div>
        '''

    def __wrapWithButtonMenuTag(self, menuTitle, menuButtons, showRightProjectMenu = False, deleteProjectButtonHTML = ''):
        rightProjectMenuDiv = self.__rightProjectMenuDiv(deleteProjectButtonHTML = deleteProjectButtonHTML) if showRightProjectMenu else ''
        mouseOverAndOut = f' onmouseover="__configurationProjectMouseOver(this)" onmouseout="__configurationProjectMouseOut(this)"' if showRightProjectMenu else ''
        return f'''
            <div class="menu" {mouseOverAndOut}>
                <div class="menu_title">
                    {menuTitle}
                </div>
                <buttonmenu>
                    {menuButtons}
                </buttonmenu>
                {rightProjectMenuDiv}
            </div>
        '''

    def __toggleProjectColumnInConfigurationJSONButtonManifest(self, buttonID, title, indexOfColumnToToggle, columnPHID, projectPHID, mode, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [
                self.buttonActions.showLoadingIndicator,
                self.buttonActions.hideTickets,
                lambda columnPHID=columnPHID, indexOfColumnToToggle=indexOfColumnToToggle, projectPHID=projectPHID :
                    self.buttonActions.toggleProjectColumnInConfigurationJSON(columnPHID, indexOfColumnToToggle, projectPHID, mode)
            ],
            successActions = [
                self.buttonActions.hideLoadingIndicator,
                lambda buttonID=buttonID :
                    self.buttonActions.toggleButton(buttonID)
            ],
            failureActions = [
                self.buttonActions.hideLoadingIndicator,
                self.buttonActions.printFailure
            ]
        )

    def toggleProjectColumnInConfigurationButtonMenuHTML(self, menuTitle, columns, projectPHID, mode):
        buttonManifests = list(map(lambda indexAndColumnTuple: self.__toggleProjectColumnInConfigurationJSONButtonManifest(
            buttonID = Utilities.cssSafeGUID(),
            title = indexAndColumnTuple[1].name,
            indexOfColumnToToggle = indexAndColumnTuple[0],
            columnPHID = indexAndColumnTuple[1].phid,
            projectPHID = projectPHID,
            mode = mode,
            isInitiallySelected = DataStore.isProjectColumnPresentInConfigurationJSON(indexAndColumnTuple[1].phid, projectPHID, mode)
        ), enumerate(columns)))
        ButtonManifestRegistry.add(buttonManifests)

        deleteButtonManifest = self.__removeProjectFromConfigurationJSONButtonManifest(projectPHID, mode)
        ButtonManifestRegistry.add([deleteButtonManifest])

        return self.__wrapWithButtonMenuTag(
            menuTitle = f'''{menuTitle}''',
            menuButtons = f'''
                {' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))}
            ''',
            showRightProjectMenu = True,
            deleteProjectButtonHTML = deleteButtonManifest.html(cssClass = 'delete')
        )

    def __removeProjectFromConfigurationJSONButtonManifest(self, projectPHID, mode):
        buttonID = Utilities.cssSafeGUID()
        return ButtonManifest(
            id = buttonID,
            title = 'Remove',
            isInitiallySelected = False,
            clickActions = [
                self.buttonActions.showLoadingIndicator,
                self.buttonActions.hideTickets,
                lambda projectPHID=projectPHID :
                    self.buttonActions.removeProjectFromConfigurationJSON(projectPHID, mode)
            ],
            successActions = [
                self.buttonActions.hideLoadingIndicator,
                lambda buttonID=buttonID :
                    self.buttonActions.deleteMenu(buttonID),
                self.buttonActions.printSuccess
            ],
            failureActions = [
                self.buttonActions.hideLoadingIndicator,
                self.buttonActions.printFailure
            ]
        )

    def __ticketToggleColumnButtonManifest(self, buttonID, title, ticketID, projectPHID, columnPHID, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [
                self.buttonActions.showLoadingIndicator,
                lambda ticketID=ticketID, projectPHID=projectPHID, columnPHID=columnPHID, buttonID=buttonID :
                    self.buttonActions.toggleTicketOnProjectColumn(ticketID, projectPHID, columnPHID, buttonID)
            ],
            successActions = [
                self.buttonActions.hideLoadingIndicator,
                lambda ticketID=ticketID :
                    self.buttonActions.showTicketSuccess(ticketID),
                lambda buttonID=buttonID :
                    self.buttonActions.toggleButton(buttonID),
                lambda buttonID=buttonID :
                    self.buttonActions.deselectOtherButtonsInMenu(buttonID),
                lambda buttonID=buttonID :
                    self.buttonActions.setComment(ticketID, '')
            ],
            failureActions = [
                self.buttonActions.hideLoadingIndicator,
                lambda ticketID=ticketID :
                    self.buttonActions.showTicketFailure(ticketID)
            ]
        )

    def ticketAddToColumnButtonMenuHTML(self, menuTitle, ticketID, ticketJSON, columns):
        buttonManifests = list(map(lambda column: self.__ticketToggleColumnButtonManifest(
            buttonID = Utilities.cssSafeGUID(),
            title = column.name,
            ticketID = f'T{ticketID}',
            projectPHID = column.project.phid,
            columnPHID = column.phid,
            isInitiallySelected = self.__isColumnPHIDPresentInTicketJSON(column.phid, ticketJSON)
        ), columns))

        ButtonManifestRegistry.add(buttonManifests)

        return self.__wrapWithButtonMenuTag(
            menuTitle = menuTitle,
            menuButtons = ' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))
        )

    def __isColumnPHIDPresentInTicketJSON(self, columnPHID, ticketJSON):
        boards = ticketJSON['attachments']['columns']['boards']
        arrayOfColumnPHIDArrays = map(lambda board:
            map(lambda column: column['phid'], board['columns']),
            boards.values()
        )
        arrayOfColumnPHIDs = [item for sublist in arrayOfColumnPHIDArrays for item in sublist]
        return columnPHID in arrayOfColumnPHIDs

    def __ticketStatusButtonManifest(self, buttonID, title, ticketID, value, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [
                self.buttonActions.showLoadingIndicator,
                lambda ticketID=ticketID, value=value :
                    self.buttonActions.updateTicketStatus(ticketID, value)
            ],
            successActions = [
                self.buttonActions.hideLoadingIndicator,
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
                self.buttonActions.hideLoadingIndicator,
                lambda ticketID=ticketID :
                    self.buttonActions.showTicketFailure(ticketID)
            ]
        )

    def ticketStatusButtonMenuHTML(self, menuTitle, ticketID, ticketJSON, statusesData):
        buttonManifests = list(map(lambda status: self.__ticketStatusButtonManifest(
            buttonID = Utilities.cssSafeGUID(),
            title = status['name'],
            ticketID = f'T{ticketID}',
            value = status['value'],
            isInitiallySelected = ticketJSON['fields']['status']['name'] == status['name']
        ), statusesData))

        ButtonManifestRegistry.add(buttonManifests)

        return self.__wrapWithButtonMenuTag(
            menuTitle = menuTitle,
            menuButtons = ' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))
        )

    def __ticketPriorityButtonManifest(self, buttonID, title, ticketID, value, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [ # lambda currying: https://stackoverflow.com/a/452659
                self.buttonActions.showLoadingIndicator,
                lambda ticketID=ticketID, value=value :
                    self.buttonActions.updateTicketPriority(ticketID, value)
            ],
            successActions = [
                self.buttonActions.hideLoadingIndicator,
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
                self.buttonActions.hideLoadingIndicator,
                lambda ticketID=ticketID :
                    self.buttonActions.showTicketFailure(ticketID)
            ]
        )

    def ticketPriorityButtonMenuHTML(self, menuTitle, ticketID, ticketJSON, prioritiesData):
        buttonManifests = list(map(lambda priority: self.__ticketPriorityButtonManifest(
            buttonID = Utilities.cssSafeGUID(),
            title = priority['name'],
            ticketID = f'T{ticketID}',
            value = priority['keywords'][0],
            isInitiallySelected = ticketJSON['fields']['priority']['name'] == priority['name']
        ), prioritiesData))

        ButtonManifestRegistry.add(buttonManifests)

        return self.__wrapWithButtonMenuTag(
            menuTitle = menuTitle,
            menuButtons = ' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))
        )
