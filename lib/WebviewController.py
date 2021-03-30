#!/usr/local/bin/python3

import Utilities, time, re, json, webview, DataStore
from string import Template
from Project import Project
from Column import Column
from Fetcher import Fetcher
from Debounce import debounce
from ButtonActions import ButtonActions
from ButtonFactory import ButtonFactory

class WebviewController:
    def __init__(self, window):
        DataStore.loadConfiguration()
        self.fetcher = self.__getFetcher()
        self.sourceProjects = []
        self.destinationProject = None
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
        return self.window.evaluate_js(f"__setInnerHTML('{selector}', `{Utilities.escapeBackticks(html)}`)")

    def __setLoadingMessage(self, message):
        print(message)
        self.window.set_title(f"{'' if len(message.strip()) > 0 else 'Phabricator Quick Tag: Quickly tag tickets from columns on various projects into any column on a destination project.'}{message}")

    def __setConfigurationHTML(self):
        self.__setInnerHTML('div#projects_configuration_body_buttons', self.buttonFactory.reloadButtonHTML())
        self.__setInnerHTML('div#sources_right_menu', self.buttonFactory.showProjectSearchButtonHTML(title = 'Add a Source Project', mode = 'source'))
        self.__setInnerHTML('div#destination_right_menu', self.buttonFactory.showProjectSearchButtonHTML(title = 'Add or change Destination Project', mode = 'destination'))
        sourceProjectsMenuButtonsHTML = ''.join(map(lambda project: self.buttonFactory.toggleSourceProjectColumnInConfigurationButtonMenuHTML(project.name, project.buttonsMenuColumns, project.phid), self.sourceProjects))
        self.__setInnerHTML('div#projects_configuration_sources', sourceProjectsMenuButtonsHTML)
        destinationProjectMenuButtonsHTML = self.buttonFactory.toggleDestinationProjectColumnInConfigurationButtonMenuHTML(self.destinationProject.name, self.destinationProject.buttonsMenuColumns) if self.destinationProject != None else ''
        self.__setInnerHTML('div#projects_configuration_destination', destinationProjectMenuButtonsHTML)
        self.window.evaluate_js(f"""
            __setPhabricatorUrl('{DataStore.getConfigurationValue('url')}');
            __setPhabricatorToken('{DataStore.getConfigurationValue('token')}');
        """
        )
        self.__setInnerHTML('div.projects_configuration_url_and_token_buttons', self.buttonFactory.urlAndTokenSaveButtonHTML())
        self.window.evaluate_js(f'''__showProjectsConfigurationBody({'false' if self.__isEmptyStringURLOrToken() else 'true'})''')

    def __columnSubtitle(self, column):
        destinationProjectName = self.destinationProject.name if self.destinationProject != None else None
        ticketsInSourceProjectString = f"""{len(column.tickets)} ticket{'' if len(column.tickets) == 1 else 's'} currently in <b>{column.project.name} > {column.name}</b>"""
        destinationProjectString = f""" not already appearing in a <b>{destinationProjectName}</b> column{'.' if len(column.tickets) == 0 else ''}""" if destinationProjectName != None else ''
        return f"{ticketsInSourceProjectString}{destinationProjectString}:"

    def __wrappedTicketHTML(self, ticketID, ticketHTML, ticketMenusHTML):
        return f'''
            <div class=ticket id="T{ticketID}">
              <button class=hide onclick="this.closest('div#T{ticketID}').remove()">Hide</button>
              {ticketHTML}
              <div class="menus phui-tag-core phui-tag-color-object">
                <span class=buttonActionMessage id="buttonActionMessage{ticketID}"></span>
                <h2>Quick options</h2>
                {ticketMenusHTML}
                Comment: ( recorded with any <strong>Quick options</strong> chosen above )
                <br>
                <textarea id="ticketID{ticketID}" style="height: 70px; width: 100%;"></textarea>
              </div>
            </div>
        '''

    def __columnTicketsHTML(self, column):
        allTicketsHTML = []
        for ticketID, ticketHTML in column.ticketsHTMLByID.items():
            ticketMenusHTML = ''.join(list(map(lambda menuHTMLLambda: menuHTMLLambda(ticketID = ticketID, ticketJSON = column.ticketsByID[int(ticketID)]), column.menuHTMLLambdas)))
            wrappedTicketHTML = self.__wrappedTicketHTML(ticketID, ticketHTML, ticketMenusHTML)
            allTicketsHTML.append(wrappedTicketHTML)
        return ''.join(allTicketsHTML)

    def __projectsTicketsHTML(self):
        print(f'Fetching complete')
        print(f'Processing hydrated object graph')
        html = []
        for project in self.sourceProjects:
            for column in project.columns:
                html.append(
                    f'''
                        <div class=column_source>
                            Ticket Source: <span class=column_identifier>{project.name} > {column.name}</span>
                        </div>
                        <div class=column_subtitle>
                            {self.__columnSubtitle(column)}
                        </div>
                        {self.__columnTicketsHTML(column = column)}
                    '''
                )
        print(f'Page HTML assembled')
        return ''.join(html)

    def __getDehydratedDestinationProject(self):
        if 'phid' not in DataStore.getConfigurationValue('destinationProject').keys():
            return None
        if DataStore.getConfigurationValue('destinationProject')['phid'] == None:
            return None
        return Project(
            phid = DataStore.getConfigurationValue('destinationProject')['phid'],
            columnPHIDsToIgnoreForButtons = DataStore.getConfigurationValue('destinationProject')['ignoreColumns']
        )

    def __getDehydratedProjects(self, dataStoreKey):
        return list(map(lambda projectJSON:
            Project(
                phid = projectJSON['phid'],
                columnPHIDs = projectJSON['columns']
            ),
            DataStore.getConfigurationValue(dataStoreKey)
        ))

    def __ticketStatusAndPriorityMenuHTML(self, ticketID, ticketJSON):
        return f'''
            {self.buttonFactory.ticketStatusButtonMenuHTML('Status', ticketID, ticketJSON, self.statusesData)}
            {self.buttonFactory.ticketPriorityButtonMenuHTML('Priority', ticketID, ticketJSON, self.prioritiesData)}
        '''

    def __fetchColumns(self, project):
        columnsData = self.fetcher.fetchColumnsData(project.phid)
        return list(map(lambda columnData: Column(columnData['fields']['name'], project, columnData['phid']), columnsData))

    def __allProjectPHIDs(self):
        phids = list(map(lambda project: project.phid, self.sourceProjects))
        if self.destinationProject and self.destinationProject.phid != None:
            phids.append(self.destinationProject.phid)
        return phids

    def __allColumnPHIDs(self):
        allColumnPHIDs = self.destinationProject.columnPHIDsToIgnoreForButtons if self.destinationProject != None else []
        for project in self.sourceProjects:
            allColumnPHIDs = allColumnPHIDs + project.columnPHIDs
        return allColumnPHIDs

    # hydrate source and destination projects and their columns
    def hydrateProjects(self, hydrateTickets = True):
        self.__setLoadingMessage('Fetching project and column names')
        openItemNamesByPHID = self.fetcher.fetchNamesForStatusOpenPHIDs(self.__allProjectPHIDs() + self.__allColumnPHIDs())

        for sourceProject in self.sourceProjects:
            sourceProject.name = openItemNamesByPHID[sourceProject.phid]
        if self.destinationProject != None:
            self.destinationProject.name = openItemNamesByPHID[self.destinationProject.phid]

        addToDestinationColumnMenuHTMLLambdas = []

        if self.destinationProject != None:
            self.__setLoadingMessage(f"Fetching '{self.destinationProject.name}' columns")
            self.destinationProject.buttonsMenuColumns = self.__fetchColumns(self.destinationProject)

            if hydrateTickets:
                destinationColumns = list(filter(lambda column: (column.phid not in self.destinationProject.columnPHIDsToIgnoreForButtons), self.destinationProject.buttonsMenuColumns))
                if len(destinationColumns) > 0:
                    addToDestinationColumnMenuHTMLLambdas.append(
                        lambda ticketID, ticketJSON, columns=destinationColumns :
                            self.buttonFactory.ticketAddToColumnButtonMenuHTML(f'Add to column on destination project ( <i>{self.destinationProject.name}</i> )', ticketID, ticketJSON, columns)
                    )

        for project in self.sourceProjects:
            # fetch source project columns
            self.__setLoadingMessage(f"Fetching '{project.name}' columns")
            project.buttonsMenuColumns = self.__fetchColumns(project)
            if not hydrateTickets:
                continue
            currentSourceColumnMenuHTMLLambda = [
                lambda ticketID, ticketJSON, columns=project.buttonsMenuColumns :
                    self.buttonFactory.ticketAddToColumnButtonMenuHTML(f'Current column on source project ( <i>{project.name}</i> )', ticketID, ticketJSON, columns)
            ]

            # make column object for each column name
            project.columns = list(map(lambda columnPHID: Column(name = openItemNamesByPHID[columnPHID], project = project, phid = columnPHID), project.columnPHIDs))

            for column in project.columns:
                self.__setLoadingMessage(f"Fetching '{project.name} > {column.name}' tickets")
                tickets = list(self.fetcher.fetchColumnTickets(column.phid))
                # dict with ticketID as key and ticketJSON as value (excluding tickets already tagged with destinationProjectPHID)
                ticketsByID = dict((x['id'], x) for x in tickets if self.destinationProject == None or not self.destinationProject.phid in x['attachments']['projects']['projectPHIDs'])
                column.ticketsByID = ticketsByID
                # print(json.dumps(self.ticketsByID, indent=4))
                column.tickets = column.ticketsByID.values()
                column.menuHTMLLambdas = currentSourceColumnMenuHTMLLambda + column.menuHTMLLambdas + addToDestinationColumnMenuHTMLLambdas + [self.__ticketStatusAndPriorityMenuHTML]
                # fetch column tickets html for their remarkup
                self.__setLoadingMessage(f"Fetching '{project.name} > {column.name}' tickets html")
                column.ticketsHTMLByID = self.fetcher.fetchTicketsHTMLByID(column.tickets)

    def load(self, hydrateTickets = True):
        self.sourceProjects = self.__getDehydratedProjects('sourceProjects')
        self.destinationProject = self.__getDehydratedDestinationProject()
        self.__setLoadingMessage('Beginning data retrieval')
        self.showLoadingIndicator()
        self.hydrateProjects(hydrateTickets = hydrateTickets)
        self.__setLoadingMessage('')

        # can start html generation now that projects are hydrated
        self.__setConfigurationHTML()
        if not hydrateTickets:
            self.hideLoadingIndicator()
            return
        self.__setInnerHTML('div.projects_tickets', self.__projectsTicketsHTML())
        self.hideLoadingIndicator()

    def __onDOMLoaded(self):
        self.window.loaded -= self.__onDOMLoaded # unsubscribe event listener
        self.window.load_html(self.__getTemplateHTML())
        time.sleep(1.0)
        self.load()

    def projectSearchTermEntered(self, searchTerm, mode):
        self.__debouncedProjectSearchTermEntered(searchTerm, mode)

    @debounce(0.3)
    def __debouncedProjectSearchTermEntered(self, searchTerm, mode):
        searchResultsSelector = 'div.projects_search_results'
        if len(searchTerm.strip()) == 0:
            self.__setInnerHTML(searchResultsSelector, '')
        else:
            projects = self.fetcher.fetchProjectsMatchingSearchTerm(searchTerm)
            projectSearchResultButtonsHTML = '' if len(projects) == 0 else ''.join(map(lambda item: self.buttonFactory.projectSearchResultButtonHTML(title = item[1], phid = item[0], mode = mode), projects.items()))
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

    def __rightProjectMenuDiv(self, deleteProjectButtonHTML):
        return f'''
            <div class="right_project_menu">
                {deleteProjectButtonHTML}
            </div>
        '''

    def showLoadingIndicator(self):
        return self.window.evaluate_js(f"__showLoadingIndicator()")

    def hideLoadingIndicator(self):
        return self.window.evaluate_js(f"__hideLoadingIndicator()")

    def showAlert(self, title, description):
        return self.window.evaluate_js(f"__showAlert(`{title}`, `{description}`)")

    def __getComment(self, ticketID):
        comment = self.window.evaluate_js(f'__getComment("{Utilities.getNumericIDFromTicketID(ticketID)}")')
        return comment if len(comment.strip()) else None

    def addTicketToProject(self, ticketID, projectPHID):
        return self.fetcher.callEndpoint(
            path = '/api/maniphest.edit',
            key = 'projects.add',
            value = projectPHID,
            objectIdentifier = ticketID,
            comment = None,
            needsValueArgumentInArray = True
        )

    def removeTicketFromProject(self, ticketID, projectPHID):
        return self.fetcher.callEndpoint(
            path = '/api/maniphest.edit',
            key = 'projects.remove',
            value = projectPHID,
            objectIdentifier = ticketID,
            comment = self.__getComment(ticketID),
            needsValueArgumentInArray = True
        )

    def addTicketToColumn(self, ticketID, columnPHID):
        return self.fetcher.callEndpoint(
            path = '/api/maniphest.edit',
            key = 'column',
            value = columnPHID,
            objectIdentifier = ticketID,
            comment = self.__getComment(ticketID),
            needsValueArgumentInArray = True
        )

    def updateTicketStatus(self, ticketID, value):
        return self.fetcher.callEndpoint(
            path = '/api/maniphest.edit',
            key = 'status',
            value = value,
            objectIdentifier = ticketID,
            comment = self.__getComment(ticketID)
        )

    def updateTicketPriority(self, ticketID, value):
        return self.fetcher.callEndpoint(
            path = '/api/maniphest.edit',
            key = 'priority',
            value = value,
            objectIdentifier = ticketID,
            comment = self.__getComment(ticketID)
        )

    def expose(self, window):
        window.expose(self.projectSearchTermEntered) # expose to JS as 'pywebview.api.projectSearchTermEntered'
        window.expose(self.isSavedURLAndTokenSameAsInTextboxes) # expose to JS as 'pywebview.api.isSavedURLAndTokenSameAsInTextboxes'
        window.expose(printDebug) # expose to JS as 'pywebview.api.printDebug'

def printDebug(message):
    print(message)
