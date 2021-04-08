#!/usr/local/bin/python3

import ButtonManifestRegistry, Utilities, DataStore
from ButtonManifest import ButtonManifest
from DirectionType import DirectionType
from ProjectType import ProjectType
from ColumnsSelectionType import ColumnsSelectionType

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
                self.buttonActions.reloadFetcher,
                self.buttonActions.refetchPrioritiesAndStatuses,
                self.buttonActions.clearSourceAndDestinationProjects,
                self.buttonActions.hideTickets,
                self.buttonActions.refetchUpstreamCSSLinkURL,
                self.buttonActions.resetUpstreamBaseURL,
                self.buttonActions.reloadConfigurationUI,
                self.buttonActions.hideLoadingIndicator,
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

    def __projectSearchResultButtonManifest(self, projectName, projectPHID, projectType):
        return ButtonManifest(
            id = Utilities.cssSafeGUID(),
            title = projectName,
            isInitiallySelected = False,
            clickActions = [
                self.buttonActions.showLoadingIndicator,
                lambda projectPHID=projectPHID, projectType=projectType :
                    self.buttonActions.saveProjectSearchChoice(projectPHID, projectType)
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

    def projectSearchResultButtonHTML(self, title, phid, projectType):
        buttonManifest = self.__projectSearchResultButtonManifest(title, phid, projectType)
        ButtonManifestRegistry.add([buttonManifest])
        return buttonManifest.html(cssClass = 'projects_search_result')

    def __showProjectSearchButtonManifest(self, title, projectType):
        return ButtonManifest(
            id = Utilities.cssSafeGUID(),
            title = title,
            isInitiallySelected = False,
            clickActions = [
                self.buttonActions.resetProjectSearch,
                lambda projectType=projectType :
                    self.buttonActions.showProjectSearch(projectType = projectType, title = title)
            ],
            successActions = [
                self.buttonActions.printSuccess
            ],
            failureActions = [
                self.buttonActions.printFailure
            ]
        )

    def showProjectSearchButtonHTML(self, title, projectType):
        buttonManifest = self.__showProjectSearchButtonManifest(title, projectType)
        ButtonManifestRegistry.add([buttonManifest])
        return buttonManifest.html(cssClass = 'add')

    def __rightProjectMenuDiv(self, rightButtonsHTML):
        return f'''
            <div class="right_project_menu">
                {rightButtonsHTML}
            </div>
        '''

    def __wrapWithButtonMenuTag(self, menuTitle, menuButtons, showRightProjectMenu = False, rightButtonsHTML = '', id = None):
        rightProjectMenuDiv = self.__rightProjectMenuDiv(rightButtonsHTML = rightButtonsHTML) if showRightProjectMenu else ''
        mouseOverAndOut = f' onmouseover="__configurationProjectMouseOver(this)" onmouseout="__configurationProjectMouseOut(this)"' if showRightProjectMenu else ''
        id = f' id="{id}"' if id != None else ''
        return f'''
            <div class="menu" {mouseOverAndOut} {id}>
                <div class="menu_title">
                    {menuTitle}
                </div>
                <buttonmenu>
                    {menuButtons}
                </buttonmenu>
                {rightProjectMenuDiv}
            </div>
        '''

    def __toggleProjectColumnInConfigurationJSONButtonManifest(self, buttonID, title, indexOfColumnToToggle, columnPHID, projectPHID, projectType, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [
                self.buttonActions.showLoadingIndicator,
                self.buttonActions.hideTickets,
                lambda columnPHID=columnPHID, indexOfColumnToToggle=indexOfColumnToToggle, projectPHID=projectPHID :
                    self.buttonActions.toggleProjectColumnInConfigurationJSON(columnPHID, indexOfColumnToToggle, projectPHID, projectType)
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

    def toggleProjectColumnInConfigurationButtonMenuHTML(self, menuTitle, columns, projectPHID, projectType):
        buttonManifests = list(map(lambda indexAndColumnTuple: self.__toggleProjectColumnInConfigurationJSONButtonManifest(
            buttonID = Utilities.cssSafeGUID(),
            title = indexAndColumnTuple[1].name,
            indexOfColumnToToggle = indexAndColumnTuple[0],
            columnPHID = indexAndColumnTuple[1].phid,
            projectPHID = projectPHID,
            projectType = projectType,
            isInitiallySelected = DataStore.isProjectColumnPresentInConfigurationJSON(indexAndColumnTuple[1].phid, projectPHID, projectType)
        ), enumerate(columns)))
        ButtonManifestRegistry.add(buttonManifests)

        deleteButtonManifest = self.__removeProjectFromConfigurationJSONButtonManifest(projectPHID, projectType)
        ButtonManifestRegistry.add([deleteButtonManifest])

        upButtonHTML = self.__moveProjectButtonHTML('↑', projectPHID, projectType, DirectionType.UP)
        downButtonHTML = self.__moveProjectButtonHTML('↓', projectPHID, projectType, DirectionType.DOWN)

        selectAllButtonHTML = self.__selectProjectColumnsButtonHTML('All', projectPHID, projectType, ColumnsSelectionType.ALL)
        deselectAllButtonHTML = self.__selectProjectColumnsButtonHTML('None', projectPHID, projectType, ColumnsSelectionType.NONE)

        return self.__wrapWithButtonMenuTag(
            menuTitle = f'''{menuTitle}''',
            menuButtons = f'''
                {' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))}
            ''',
            showRightProjectMenu = True,
            rightButtonsHTML = upButtonHTML + downButtonHTML + selectAllButtonHTML + deselectAllButtonHTML + deleteButtonManifest.html(cssClass = 'delete'),
            id = f'_{projectPHID}'
        )

    def __removeProjectFromConfigurationJSONButtonManifest(self, projectPHID, projectType):
        buttonID = Utilities.cssSafeGUID()
        return ButtonManifest(
            id = buttonID,
            title = 'Remove',
            isInitiallySelected = False,
            clickActions = [
                self.buttonActions.showLoadingIndicator,
                lambda projectPHID=projectPHID :
                    self.buttonActions.removeProjectFromConfigurationJSON(projectPHID, projectType)
            ],
            successActions = [
                self.buttonActions.hideLoadingIndicator,
                lambda buttonID=buttonID :
                    self.buttonActions.deleteMenu(buttonID),
                lambda projectPHID=projectPHID :
                    self.buttonActions.deleteProjectTickets(projectPHID),
                self.buttonActions.hideToggleAllTicketsContainerIfNoSourceProjects,
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

    def ticketAddToColumnButtonMenuHTML(self, menuTitle, ticketID, ticketJSON, columns, projectPHID):
        buttonManifests = list(map(lambda column: self.__ticketToggleColumnButtonManifest(
            buttonID = Utilities.cssSafeGUID(),
            title = column.name,
            ticketID = f'T{ticketID}',
            projectPHID = projectPHID,
            columnPHID = column.phid,
            isInitiallySelected = self.__isColumnPHIDPresentInTicketJSON(column.phid, ticketJSON)
        ), columns))

        ButtonManifestRegistry.add(buttonManifests)

        return self.__wrapWithButtonMenuTag(
            menuTitle = menuTitle,
            menuButtons = ' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests)),
            showRightProjectMenu = False,
            rightButtonsHTML = '',
            id = f'_{projectPHID}'
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

    def __moveProjectButtonManifest(self, buttonID, title, projectPHID, projectType, directionType):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = False,
            clickActions = [
                self.buttonActions.showLoadingIndicator,
                lambda projectPHID=projectPHID, projectType=projectType, directionType=directionType :
                    self.buttonActions.moveConfigurationProjectVertically(projectPHID, projectType, directionType)
            ],
            successActions = [
                self.buttonActions.hideLoadingIndicator,
                lambda projectPHID=projectPHID, projectType=projectType, directionType=directionType :
                    self.buttonActions.moveDOMConfigurationProjectVertically(projectPHID, projectType, directionType),
                lambda projectPHID=projectPHID, projectType=projectType, directionType=directionType :
                    self.buttonActions.moveDOMProjectTicketsVertically(projectPHID, projectType, directionType),
                lambda projectPHID=projectPHID, projectType=projectType, directionType=directionType :
                    self.buttonActions.moveDOMAddToColumnMenusVertically(projectPHID, projectType, directionType),
                self.buttonActions.printSuccess
            ],
            failureActions = [
                self.buttonActions.hideLoadingIndicator,
                self.buttonActions.printFailure
            ]
        )

    def __moveProjectButtonHTML(self, title, projectPHID, projectType, directionType):
        buttonManifest = self.__moveProjectButtonManifest(
            buttonID = Utilities.cssSafeGUID(),
            title = title,
            projectPHID = projectPHID,
            projectType = projectType,
            directionType = directionType
        )

        ButtonManifestRegistry.add([buttonManifest])

        return buttonManifest.html(cssClass = 'move')

    def __selectProjectColumnsButtonManifest(self, buttonID, title, projectPHID, projectType, columnsSelectionType):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = False,
            clickActions = [
                self.buttonActions.hideTickets,
                self.buttonActions.showLoadingIndicator,
                lambda projectPHID=projectPHID, projectType=projectType, columnsSelectionType=columnsSelectionType :
                    self.buttonActions.selectConfigurationProjectColumns(projectPHID, projectType, columnsSelectionType)
            ],
            successActions = [
                self.buttonActions.hideLoadingIndicator,
                self.buttonActions.printSuccess
            ],
            failureActions = [
                self.buttonActions.hideLoadingIndicator,
                self.buttonActions.printFailure
            ]
        )

    def __selectProjectColumnsButtonHTML(self, title, projectPHID, projectType, columnsSelectionType):
        buttonManifest = self.__selectProjectColumnsButtonManifest(
            buttonID = Utilities.cssSafeGUID(),
            title = title,
            projectPHID = projectPHID,
            projectType = projectType,
            columnsSelectionType = columnsSelectionType
        )

        ButtonManifestRegistry.add([buttonManifest])

        return buttonManifest.html(cssClass = 'select')
