#!/usr/local/bin/python3

import DataStore, ButtonManifestRegistry, Utilities, re
from DirectionType import DirectionType
from ProjectType import ProjectType

class ButtonActions:
    def __init__(self, window, delegate):
        self.window = window
        self.delegate = delegate

    def showLoadingIndicator(self):
        return self.delegate.showLoadingIndicator()

    def hideLoadingIndicator(self):
        return self.delegate.hideLoadingIndicator()

    def showAlert(self, title, description):
        return self.delegate.showAlert(title, description)

    def reload(self, hydrateTickets = True):
        ButtonManifestRegistry.clear()
        DataStore.loadConfiguration()
        self.delegate.load(hydrateTickets = hydrateTickets)
        return True

    def showTickets(self):
        return self.window.evaluate_js('__showTickets()')

    def hideTickets(self):
        return self.window.evaluate_js('__hideTickets()')

    def printSuccess(self):
        print('success!')

    def printFailure(self):
        print('failure!')

    def saveURLAndToken(self):
        url = self.window.evaluate_js(f'__getPhabricatorUrl()')
        token = self.window.evaluate_js(f'__getPhabricatorToken()')
        configuration = DataStore.getCurrentConfiguration()
        configuration['url'] = url.strip()
        configuration['token'] = token.strip()
        DataStore.saveCurrentConfiguration()
        return True

    def reloadFetcher(self):
        self.delegate.reloadFetcher()
        return True

    def refetchPrioritiesAndStatuses(self):
        self.delegate.refetchPrioritiesAndStatuses()
        return True

    def clearSourceAndDestinationProjects(self):
        destinationProjects = DataStore.getConfigurationValue('destinationProjects')
        destinationProjects.clear()
        sourceProjects = DataStore.getConfigurationValue('sourceProjects')
        sourceProjects.clear()
        DataStore.saveCurrentConfiguration()

    def refetchUpstreamCSSLinkURL(self):
        cssURL = self.delegate.extractCSSURL()
        self.window.evaluate_js(f'__setUpstreamCSSLinkURL("{cssURL}")')
        return True

    def resetUpstreamBaseURL(self):
        configuration = DataStore.getCurrentConfiguration()
        self.window.evaluate_js(f'''__setUpstreamBaseURL("{configuration['url']}")''')
        return True

    def reloadConfigurationUI(self):
        self.reload(hydrateTickets = False)

    def hideProjectSearch(self):
        return self.window.evaluate_js('__hideProjectSearch()')

    def __saveProjectPHID(self, projectPHID, projectType):
        dataStoreKey = DataStore.dataStoreKeyForProjectType(projectType)
        projects = DataStore.getConfigurationValue(dataStoreKey)
        if not any(project['phid'] == projectPHID for project in projects):
            projects.insert(0, {
                'phid': projectPHID,
                'columns': []
            })
            DataStore.saveCurrentConfiguration()
        else:
            print(f'{projectPHID} already exists in "{dataStoreKey}"')

    def saveProjectSearchChoice(self, projectPHID, projectType):
        self.__saveProjectPHID(projectPHID, projectType)
        return True

    def resetProjectSearch(self):
        return self.window.evaluate_js('__resetProjectSearch()')

    def showProjectSearch(self, projectType, title):
        return self.window.evaluate_js(f"__showProjectSearch(`{projectType.name}`, `{title}`)")

    def toggleButton(self, buttonID):
        return self.window.evaluate_js(f"__toggleButton('{buttonID}')")

    def deleteMenu(self, buttonID):
        return self.window.evaluate_js(f"__deleteMenu('{buttonID}')")

    def deleteProjectTickets(self, projectPHID):
        return self.window.evaluate_js(f"__deleteProjectTickets('{projectPHID}')")

    def hideToggleAllTicketsContainerIfNoSourceProjects(self):
        return self.window.evaluate_js(f"__hideToggleAllTicketsContainerIfNoSourceProjects()")

    def toggleProjectColumnInConfigurationJSON(self, columnPHID, indexOfColumnToToggle, projectPHID, projectType):
        dataStoreKey = DataStore.dataStoreKeyForProjectType(projectType)
        projects = DataStore.getConfigurationValue(dataStoreKey)
        project = next(project for project in projects if project['phid'] == projectPHID)
        if DataStore.isProjectColumnPresentInConfigurationJSON(columnPHID, projectPHID, projectType):
            project['columns'].remove(columnPHID)
        else:
            project['columns'].insert(indexOfColumnToToggle, columnPHID)
        DataStore.saveCurrentConfiguration()
        return True

    def removeProjectFromConfigurationJSON(self, projectPHID, projectType):
        dataStoreKey = DataStore.dataStoreKeyForProjectType(projectType)
        projects = DataStore.getConfigurationValue(dataStoreKey)
        project = next(project for project in projects if project['phid'] == projectPHID)
        projects.remove(project)
        DataStore.saveCurrentConfiguration()
        DataStore.loadConfiguration()
        return True

    def __setTicketActionMessage(self, ticketID, message):
        return self.window.evaluate_js(f'__setTicketActionMessage("{Utilities.getNumericIDFromTicketID(ticketID)}", "{message}")')

    def showTicketFailure(self, ticketID):
        return self.__setTicketActionMessage(ticketID, '💩 Failure')

    def showTicketSuccess(self, ticketID):
        return self.__setTicketActionMessage(ticketID, '🎉 Success')

    def setComment(self, ticketID, comment):
        returnedComment = self.window.evaluate_js(f'__setComment("{Utilities.getNumericIDFromTicketID(ticketID)}", "{comment}")')
        return returnedComment == comment

    def selectButton(self, buttonID):
        return self.window.evaluate_js(f'__selectButton("{buttonID}")')

    def deselectOtherButtonsInMenu(self, buttonID):
        return self.window.evaluate_js(f'__deselectOtherButtonsInMenu("{buttonID}")')

    def __isButtonSelected(self, buttonID):
        return self.window.evaluate_js(f'__isButtonSelected("{buttonID}")')

    def toggleTicketOnProjectColumn(self, ticketID, projectPHID, columnPHID, buttonID):
        if self.__isButtonSelected(buttonID):
            if not self.delegate.removeTicketFromProject(ticketID, projectPHID):
                return False
        else:
            if not self.delegate.addTicketToProject(ticketID, projectPHID):
                return False
            if not self.delegate.addTicketToColumn(ticketID, columnPHID):
                return False
        return True

    def updateTicketStatus(self, ticketID, value):
        return self.delegate.updateTicketStatus(ticketID, value)

    def updateTicketPriority(self, ticketID, value):
        return self.delegate.updateTicketPriority(ticketID, value)

    def moveConfigurationProjectVertically(self, projectPHID, projectType, directionType):
        result = DataStore.moveProject(projectPHID, projectType, directionType)
        if result == False:
            return False
        DataStore.saveCurrentConfiguration()
        DataStore.loadConfiguration()
        return True

    def moveDOMConfigurationProjectVertically(self, projectPHID, projectType, directionType):
        containerSelector = f'''div#projects_configuration_{'sources' if projectType == ProjectType.SOURCE else 'destinations'}'''
        return self.window.evaluate_js(f'''__moveVertically("{containerSelector} > div.menu#_{projectPHID}", "{directionType.name}")''')

    def moveDOMProjectTicketsVertically(self, projectPHID, projectType, directionType):
        if projectType == ProjectType.DESTINATION:
            return True
        return self.window.evaluate_js(f'__moveVertically("div.project_columns#_{projectPHID}", "{directionType.name}")')

    def moveDOMAddToColumnMenusVertically(self, projectPHID, projectType, directionType):
        if projectType == ProjectType.SOURCE:
            return True
        return self.window.evaluate_js(f'__moveAllVertically("div.destination_projects_menus > div.menu#_{projectPHID}", "{directionType.name}")')
