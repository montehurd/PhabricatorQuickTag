#!/usr/local/bin/python3

import Utilities, time, re, json, webview, DataStore
from string import Template
from Project import Project
from Column import Column
from Fetcher import Fetcher
from Debounce import debounce
from ButtonActions import ButtonActions
from ButtonFactory import ButtonFactory
from ProjectType import ProjectType

class WebviewController:
    def __init__(self, window):
        DataStore.loadConfiguration()
        self.fetcher = self.__getFetcher()
        self.sourceProjects = []
        self.destinationProjects = []
        self.window = window
        self.buttonFactory = ButtonFactory(buttonActions = ButtonActions(window = self.window, delegate = self))
        self.window.loaded += self.__onDOMLoaded
        self.prioritiesData, self.statusesData = self.__fetchPrioritiesAndStatuses()

    def __getFetcher(self):
        return Fetcher(DataStore.getConfigurationValue('url'), DataStore.getConfigurationValue('token'))

    def extractCSSURL(self):
        if self.__isEmptyStringURLOrToken():
            return ''
        # HACK: grabbing the css url from the 'flag' page html. perhaps there's a better way? some API?
        html = self.fetcher.fetchHTML('/flag')
        match = re.search(r'<link[^>]* rel="stylesheet"[^>]* href="([^"]*?core\.pkg\.css)"', html)
        return match.group(1)

    def __getTemplateHTML(self):
        return Template(Utilities.stringFromFile('lib/Template.html')).substitute(
            TEMPLATE_BASE_URL = self.fetcher.baseURL,
            TEMPLATE_CSS_URL = self.extractCSSURL(),
            TEMPLATE_API_TOKEN = self.fetcher.apiToken,
            # Included html tags on the next two here vs in the html file simply to keep syntax hilighting working in the html file - '$TEMPLATE_CSS', specifically, gives Atom fits.
            TEMPLATE_CSS = f"""<style type="text/css">\n{Utilities.stringFromFile('lib/Template.css')}\n</style>""",
            TEMPLATE_JS = f"""<script type="text/javascript">\n{Utilities.stringFromFile('lib/Template.js')}\n</script>""",
            TEMPLATE_URL = DataStore.getConfigurationValue('url'),
            TEMPLATE_TOKEN = DataStore.getConfigurationValue('token')
        )

    def __setInnerHTML(self, selector, html):
        html = html.replace('$', '&#36;') # needed for dollar signs within a remarkup code block, such as ```$100``` in a ticket description
        html = Utilities.escapeBackticks(html)
        return self.window.evaluate_js(f"__setInnerHTML('{selector}', `{html}`)")

    def __setLoadingMessage(self, message):
        print(message)
        self.window.set_title(f"{'' if len(message.strip()) > 0 else 'Phabricator Quick Tag: Quickly tag tickets from columns on source projects into columns on destination projects.'}{message}")

    def __setConfigurationHTML(self):
        self.__setInnerHTML('div#projects_configuration_body_buttons', self.buttonFactory.reloadButtonHTML())
        self.__setInnerHTML('div#sources_right_menu', self.buttonFactory.showProjectSearchButtonHTML(title = 'Add a Source Project or Tag', projectType = ProjectType.SOURCE))
        self.__setInnerHTML('div#destination_right_menu', self.buttonFactory.showProjectSearchButtonHTML(title = 'Add a Destination Project', projectType = ProjectType.DESTINATION))
        sourceProjectsMenuButtonsHTML = ''.join(map(lambda project: self.buttonFactory.toggleProjectColumnInConfigurationButtonMenuHTML(project.name, project.buttonsMenuColumns, project.phid, ProjectType.SOURCE, project.status, project.icon), self.sourceProjects))
        self.__setInnerHTML('div#projects_configuration_sources', sourceProjectsMenuButtonsHTML)
        destinationProjectsMenuButtonsHTML = ''.join(map(lambda project: self.buttonFactory.toggleProjectColumnInConfigurationButtonMenuHTML(project.name, project.buttonsMenuColumns, project.phid, ProjectType.DESTINATION, project.status, project.icon), self.destinationProjects))
        self.__setInnerHTML('div#projects_configuration_destinations', destinationProjectsMenuButtonsHTML)
        self.window.evaluate_js(f"""
            __setPhabricatorUrl('{DataStore.getConfigurationValue('url')}');
            __setPhabricatorToken('{DataStore.getConfigurationValue('token')}');
        """
        )
        self.__setInnerHTML('div.projects_configuration_url_and_token_buttons', self.buttonFactory.urlAndTokenSaveButtonHTML())
        self.window.evaluate_js(f'''__showProjectsConfigurationBody({'false' if self.__isEmptyStringURLOrToken() else 'true'})''')

    def __projectsTicketsHTML(self):
        print(f'Fetching complete')
        print(f'Processing hydrated object graph')
        projectsTicketsHTML = ''.join(map(lambda project: project.html(destinationProjectsCount = len(self.destinationProjects)), self.sourceProjects))
        print(f'Page HTML assembled')
        return projectsTicketsHTML

    def __getDehydratedProjects(self, projectType):
        dataStoreKey = DataStore.dataStoreKeyForProjectType(projectType)
        return list(map(lambda projectJSON:
            Project(
                phid = projectJSON['phid'],
                columnPHIDs = projectJSON['columns'],
                showTicketsWithNoColumn = projectJSON.get('showTicketsWithNoColumn', False)
            ),
            DataStore.getConfigurationValue(dataStoreKey)
        ))

    def __fetchColumns(self, project):
        columnsData = self.fetcher.fetchColumnsData(project.phid)
        return list(map(lambda columnData: Column(columnData['fields']['name'], project, columnData['phid']), columnsData))

    def __projectPHIDs(self, projectType):
        projects = self.sourceProjects if projectType == ProjectType.SOURCE else self.destinationProjects
        return list(map(lambda project: project.phid, projects))

    def __allProjectPHIDs(self):
        return self.__projectPHIDs(ProjectType.SOURCE) + self.__projectPHIDs(ProjectType.DESTINATION)

    def __columnPHIDs(self, projectType):
        phids = []
        for project in self.sourceProjects if projectType == ProjectType.SOURCE else self.destinationProjects:
            phids = phids + project.columnPHIDs
        return phids

    def __allColumnPHIDs(self):
        return self.__columnPHIDs(ProjectType.SOURCE) + self.__columnPHIDs(ProjectType.DESTINATION)

    def __allProjects(self):
        return self.sourceProjects + self.destinationProjects

    def __isSourceProject(self, projectPHID):
        return projectPHID in self.__projectPHIDs(ProjectType.SOURCE)

    # hydrate source and destination projects and their columns
    def hydrateProjects(self, hydrateTickets = True):
        self.__setLoadingMessage('Fetching project and column names')
        namesAndStatusesByPHID = self.fetcher.fetchNamesAndStatusesForPHIDs(self.__allProjectPHIDs() + self.__allColumnPHIDs())
        for project in self.__allProjects():
            if project.phid in namesAndStatusesByPHID.keys():
                project.name = namesAndStatusesByPHID[project.phid]['name']
                project.status = namesAndStatusesByPHID[project.phid]['status']

        self.__setLoadingMessage(f"Fetching project icons")
        icons = self.fetcher.fetchProjectsIcons(self.__allProjectPHIDs())
        for project in self.__allProjects():
            project.icon = icons.get(project.phid)

        projectColumnMenuHTMLLambdas = {}
        for project in self.destinationProjects:
            self.__setLoadingMessage(f"Fetching '{project.name}' columns")
            project.buttonsMenuColumns = self.__fetchColumns(project)

            if hydrateTickets:
                destinationColumns = list(filter(lambda column: (column.phid in project.columnPHIDs), project.buttonsMenuColumns))
                if len(destinationColumns) > 0:
                    projectColumnMenuHTMLLambdas[project.phid] = lambda ticketID, ticketJSON, name=project.name, columns=destinationColumns, projectPHID=project.phid : self.buttonFactory.ticketAddToColumnButtonMenuHTML(f'Add to column on destination project ( <i>{name}</i> )', ticketID, ticketJSON, columns, projectPHID)

        userPHIDs = set()
        for project in self.sourceProjects:
            # fetch source project columns
            self.__setLoadingMessage(f"Fetching '{project.name}' columns")
            project.buttonsMenuColumns = self.__fetchColumns(project)
            if not hydrateTickets:
                continue

            currentSourceColumnMenuHTMLLambda = lambda ticketID, ticketJSON, name=project.name, columns=project.buttonsMenuColumns, projectPHID=project.phid : self.buttonFactory.ticketAddToColumnButtonMenuHTML(f'Current column on source project ( <i>{name}</i> )', ticketID, ticketJSON, columns, projectPHID)

            # make column object for each column name
            project.columns = list(map(lambda columnPHID: Column(name = None, project = project, phid = columnPHID), project.columnPHIDs))

            if project.showTicketsWithNoColumn:
                project.columns.insert(0, Column(name = 'In no columns', project = project, phid = None, isNoColumnTicketsPlaceholder = True))

            for column in project.columns:
                if column.phid in namesAndStatusesByPHID.keys():
                    column.status = namesAndStatusesByPHID[column.phid]['status']
                    column.name = namesAndStatusesByPHID[column.phid]['name']
                self.__setLoadingMessage(f"Fetching '{project.name} > {column.name}' tickets")
                if column.isNoColumnTicketsPlaceholder == False:
                    tickets = list(self.fetcher.fetchColumnTickets(column.phid))
                else:
                    tickets = list(self.fetcher.fetchNoColumnProjectTickets(project.phid))

                ticketsByID = dict((ticket['id'], ticket) for ticket in tickets if self.__shouldShowTicket(ticket, project.phid, column.phid))
                column.ticketsByID = ticketsByID
                column.tickets = column.ticketsByID.values()
                nonSourceProjectColumnMenuHTMLLambdas = [v for (k,v) in projectColumnMenuHTMLLambdas.items() if k != project.phid]
                column.currentSourceColumnMenuHTMLLambda = currentSourceColumnMenuHTMLLambda
                column.nonSourceProjectColumnMenuHTMLLambdas = nonSourceProjectColumnMenuHTMLLambdas
                column.statusMenuHTMLLambda = lambda ticketID, ticketJSON, statusesData=self.statusesData : self.buttonFactory.ticketStatusButtonMenuHTML('Status', ticketID, ticketJSON, statusesData)
                column.priorityMenuHTMLLambda = lambda ticketID, ticketJSON, prioritiesData=self.prioritiesData : self.buttonFactory.ticketPriorityButtonMenuHTML('Priority', ticketID, ticketJSON, prioritiesData)
                # fetch column tickets html for their remarkup
                self.__setLoadingMessage(f"Fetching '{project.name} > {column.name}' tickets html")
                column.ticketsHTMLByID = self.fetcher.fetchTicketsHTMLByID(column.tickets)
                userPHIDs = userPHIDs.union(self.__getUserPHIDs(tickets))

        self.__setLoadingMessage(f"Fetching user names")
        userNames = self.fetcher.fetchUserNamesForUserPHIDs(userPHIDs)
        for project in self.sourceProjects:
            for column in project.columns:
                column.userNames = userNames

    def __getUserPHIDs(self, tickets):
        authors = set(map(lambda ticket: ticket['fields']['authorPHID'], tickets))
        owners = set(map(lambda ticket: ticket['fields']['ownerPHID'], tickets))
        people = authors.union(owners)
        return list(filter(None, people))

    def __allSourceProjectsTicketCount(self):
        count = 0
        for project in self.sourceProjects:
            for column in project.columns:
                count += len(column.tickets)
        return count

    def load(self, hydrateTickets = True):
        self.sourceProjects = self.__getDehydratedProjects(ProjectType.SOURCE)
        self.destinationProjects = self.__getDehydratedProjects(ProjectType.DESTINATION)
        self.hideToggleAllTicketsContainer()
        self.__setLoadingMessage('Beginning data retrieval')
        self.showLoadingIndicator()
        self.hydrateProjects(hydrateTickets = hydrateTickets)
        self.__setLoadingMessage('')
        # can start html generation now that projects are hydrated
        self.__setConfigurationHTML()
        if not hydrateTickets:
            self.hideLoadingIndicator()
            return
        if self.__allSourceProjectsTicketCount() > 0:
            self.showToggleAllTicketsContainer()
        self.__setInnerHTML('div.projects_tickets', self.__projectsTicketsHTML())
        self.hideLoadingIndicator()

    def __shouldShowTicket(self, ticket, projectPHID, columnPHID):
        # show if projectPHID is also a destination project and columnPHID is in sourceColumns
        # (this is basically an exception which causes tickets to show in the case where their project is both a source *and* a destination)
        destinationPHIDs = self.__projectPHIDs(ProjectType.DESTINATION)
        sourceColumnPHIDs = self.__columnPHIDs(ProjectType.SOURCE)
        if projectPHID in destinationPHIDs and columnPHID in sourceColumnPHIDs:
            return True
        # don't show if the ticket is tagged on a destination project
        for destinationProject in self.destinationProjects:
            if destinationProject.phid in ticket['attachments']['projects']['projectPHIDs']:
                return False
        return True

    def __onDOMLoaded(self):
        self.window.loaded -= self.__onDOMLoaded # unsubscribe event listener
        self.window.load_html(self.__getTemplateHTML())
        time.sleep(1.0)
        self.load()

    def projectSearchTermEntered(self, searchTerm, projectTypeName):
        self.__debouncedProjectSearchTermEntered(searchTerm, ProjectType[projectTypeName])

    @debounce(0.3)
    def __debouncedProjectSearchTermEntered(self, searchTerm, projectType):
        searchResultsSelector = 'div.projects_search_results'
        if len(searchTerm.strip()) == 0:
            self.__setInnerHTML(searchResultsSelector, '')
        else:
            projects = self.fetcher.fetchProjectsMatchingSearchTerm(searchTerm)
            icons = self.fetcher.fetchProjectsIcons(projects.keys())
            projectSearchResultButtonsHTML = '' if len(projects) == 0 else ''.join(map(lambda item: self.buttonFactory.projectSearchResultButtonHTML(title = f' {item[1]}', phid = item[0], projectType = projectType, cssClass = f"projects_search_result {icons[item[0]]['icon']}"), projects.items()))
            self.__setInnerHTML(searchResultsSelector, projectSearchResultButtonsHTML)

    def reloadFetcher(self):
        self.fetcher = self.__getFetcher()
        return True

    def __isEmptyStringURLOrToken(self):
        configuration = DataStore.getCurrentConfiguration()
        return len(configuration['url'].strip()) == 0 or len(configuration['token'].strip()) == 0

    def isSavedURLAndTokenSameAsInTextboxes(self):
        url = self.window.evaluate_js(f'__getPhabricatorUrl()')
        token = self.window.evaluate_js(f'__getPhabricatorToken()')
        configuration = DataStore.getCurrentConfiguration()
        isSame = configuration['url'] == url.strip() and configuration['token'] == token.strip()
        return isSame

    def __fetchPrioritiesAndStatuses(self):
        if self.__isEmptyStringURLOrToken():
            return [], []
        return self.fetcher.fetchPriorities(), self.fetcher.fetchStatuses()

    def refetchPrioritiesAndStatuses(self):
        self.prioritiesData, self.statusesData = self.__fetchPrioritiesAndStatuses()
        return True

    def showLoadingIndicator(self):
        return self.window.evaluate_js(f"__showLoadingIndicator()")

    def hideLoadingIndicator(self):
        return self.window.evaluate_js(f"__hideLoadingIndicator()")

    def showToggleAllTicketsContainer(self):
        return self.window.evaluate_js(f"__showToggleAllTicketsContainer()")

    def hideToggleAllTicketsContainer(self):
        return self.window.evaluate_js(f"__hideToggleAllTicketsContainer()")

    def showAlert(self, title, description):
        return self.window.evaluate_js(f"__showAlert(`{title}`, `{description}`)")

    def __getComment(self, ticketID):
        comment = self.window.evaluate_js(f'__getComment("{Utilities.getNumericIDFromTicketID(ticketID)}")')
        return comment if len(comment.strip()) else None

    def addTicketToProject(self, ticketID, projectPHID):
        return self.fetcher.addTicketToProject(
            ticketID = ticketID,
            projectPHID = projectPHID
        )

    def removeTicketFromProject(self, ticketID, projectPHID):
        return self.fetcher.removeTicketFromProject(
            ticketID = ticketID,
            projectPHID = projectPHID,
            comment = self.__getComment(ticketID)
        )

    def addTicketToColumn(self, ticketID, columnPHID):
        return self.fetcher.addTicketToColumn(
            ticketID = ticketID,
            columnPHID = columnPHID,
            comment = self.__getComment(ticketID)
        )

    def updateTicketStatus(self, ticketID, value):
        return self.fetcher.updateTicketStatus(
            ticketID = ticketID,
            value = value,
            comment = self.__getComment(ticketID)
        )

    def updateTicketPriority(self, ticketID, value):
        return self.fetcher.updateTicketPriority(
            ticketID = ticketID,
            value = value,
            comment = self.__getComment(ticketID)
        )

    def expose(self, window):
        window.expose(self.projectSearchTermEntered) # expose to JS as 'pywebview.api.projectSearchTermEntered'
        window.expose(self.isSavedURLAndTokenSameAsInTextboxes) # expose to JS as 'pywebview.api.isSavedURLAndTokenSameAsInTextboxes'
        window.expose(printDebug) # expose to JS as 'pywebview.api.printDebug'

def printDebug(message):
    print(message)
