#!/usr/local/bin/python3

import Utilities, time, re, json, webview, ButtonManifestRegistry, DataStore, uuid
from string import Template
from ButtonManifest import ButtonManifest
from Project import Project
from Column import Column
from Fetcher import Fetcher
from Debounce import debounce

class WebviewController:
    def __init__(self, window):
        DataStore.loadConfiguration()
        self.fetcher = self.__getFetcher()
        self.sourceProjects = []
        self.destinationProject = None
        self.window = window
        self.window.loaded += self.__onDOMLoaded
        self.prioritiesData, self.statusesData = self.__fetchPrioritiesAndStatuses()

    def __getFetcher(self):
        return Fetcher(DataStore.getConfigurationValue('url'), DataStore.getConfigurationValue('token'))

    def __extractCSSURL(self):
        if self.__isEmptyStringURLOrToken():
            return ''
        # HACK: grabbing the css url from the 'flag' page html. perhaps there's a better way? some API?
        html = self.fetcher.fetchHTML('/flag')
        match = re.search(r'<link[^>]* rel="stylesheet"[^>]* href="([^"]*?core\.pkg\.css)"', html)
        return match.group(1)

    def __getTemplateHTML(self):
        return Template(Utilities.stringFromFile('lib/Template.html')).substitute(
            TEMPLATE_BASE_URL = self.fetcher.baseURL,
            TEMPLATE_CSS_URL = self.__extractCSSURL(),
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
        self.window.set_title(f"{'' if len(message.strip()) > 0 else 'Phabricator Quick Tag'}{message}")

    def __setConfigurationHTML(self):
        self.__setInnerHTML('div#projects_configuration_body_buttons', self.__reloadButtonHTML())
        self.__setInnerHTML('div#sources_right_menu', self.__showProjectSearchButtonHTML(title = 'Add a Source Project', mode = 'source'))
        self.__setInnerHTML('div#destination_right_menu', self.__showProjectSearchButtonHTML(title = 'Add or change Destination Project', mode = 'destination'))
        sourceProjectsMenuButtonsHTML = ''.join(map(lambda project: self.__toggleSourceProjectColumnInConfigurationButtonMenuHTML(project.name, project.buttonsMenuColumns, project.phid), self.sourceProjects))
        self.__setInnerHTML('div#projects_configuration_sources', sourceProjectsMenuButtonsHTML)
        destinationProjectMenuButtonsHTML = self.__toggleDestinationProjectColumnInConfigurationButtonMenuHTML(self.destinationProject.name, self.destinationProject.buttonsMenuColumns) if self.destinationProject != None else ''
        self.__setInnerHTML('div#projects_configuration_destination', destinationProjectMenuButtonsHTML)
        self.window.evaluate_js(f"""
            __setPhabricatorUrl('{DataStore.getConfigurationValue('url')}');
            __setPhabricatorToken('{DataStore.getConfigurationValue('token')}');
        """
        )
        self.__setInnerHTML('div.projects_configuration_url_and_token_buttons', self.__urlAndTokenSaveButtonHTML())
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

    def __getDehydratedSourceProjects(self):
        return list(map(lambda projectJSON:
            Project(
                phid = projectJSON['phid'],
                columnPHIDs = projectJSON['columns']
            ),
            DataStore.getConfigurationValue('sourceProjects')
        ))

    def __getDehydratedDestinationProject(self):
        if 'phid' not in DataStore.getConfigurationValue('destinationProject').keys():
            return None
        if DataStore.getConfigurationValue('destinationProject')['phid'] == None:
            return None
        return Project(
            phid = DataStore.getConfigurationValue('destinationProject')['phid'],
            columnPHIDsToIgnoreForButtons = DataStore.getConfigurationValue('destinationProject')['ignoreColumns']
        )

    def __ticketStatusAndPriorityMenuHTML(self, ticketID, ticketJSON):
        return f'''
            {self.__ticketStatusButtonMenuHTML('Status', ticketID, ticketJSON)}
            {self.__ticketPriorityButtonMenuHTML('Priority', ticketID, ticketJSON)}
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
                            self.__ticketAddToColumnButtonMenuHTML(f'Add to column on destination project ( <i>{self.destinationProject.name}</i> )', ticketID, ticketJSON, columns)
                    )

        for project in self.sourceProjects:
            # fetch source project columns
            self.__setLoadingMessage(f"Fetching '{project.name}' columns")
            project.buttonsMenuColumns = self.__fetchColumns(project)
            if not hydrateTickets:
                continue
            currentSourceColumnMenuHTMLLambda = [
                lambda ticketID, ticketJSON, columns=project.buttonsMenuColumns :
                    self.__ticketAddToColumnButtonMenuHTML(f'Current column on source project ( <i>{project.name}</i> )', ticketID, ticketJSON, columns)
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

    def __load(self, hydrateTickets = True):
        self.sourceProjects = self.__getDehydratedSourceProjects()
        self.destinationProject = self.__getDehydratedDestinationProject()
        self.__setLoadingMessage('Beginning data retrieval')
        self.hydrateProjects(hydrateTickets = hydrateTickets)
        self.__setLoadingMessage('')

        # can start html generation now that projects are hydrated
        self.__setConfigurationHTML()
        if not hydrateTickets:
            return
        self.__setInnerHTML('div.projects_tickets', self.__projectsTicketsHTML())

    def __onDOMLoaded(self):
        self.window.loaded -= self.__onDOMLoaded # unsubscribe event listener
        self.window.load_html(self.__getTemplateHTML())
        time.sleep(1.0)
        self.__load()

    def reload(self, hydrateTickets = True):
        ButtonManifestRegistry.clear()
        DataStore.loadConfiguration()
        self.__load(hydrateTickets = hydrateTickets)

    def projectSearchTermEntered(self, searchTerm, mode):
        self.__debouncedProjectSearchTermEntered(searchTerm, mode)

    @debounce(0.3)
    def __debouncedProjectSearchTermEntered(self, searchTerm, mode):
        searchResultsSelector = 'div.projects_search_results'
        if len(searchTerm.strip()) == 0:
            self.__setInnerHTML(searchResultsSelector, '')
        else:
            projects = self.fetcher.fetchProjectsMatchingSearchTerm(searchTerm)
            projectSearchResultButtonsHTML = '' if len(projects) == 0 else ''.join(map(lambda item: self.__projectSearchResultButtonHTML(title = item[1], phid = item[0], mode = mode), projects.items()))
            self.__setInnerHTML(searchResultsSelector, projectSearchResultButtonsHTML)

    def __showTickets(self):
        return self.window.evaluate_js('__showTickets()')

    def __reloadButtonManifest(self):
        return ButtonManifest(
            id = Utilities.cssSafeGUID(),
            title = 'Reload Tickets',
            isInitiallySelected = False,
            clickActions = [
                self.__showLoadingIndicator,
                self.reload
            ],
            successActions = [
                self.__hideLoadingIndicator,
                self.__showTickets,
                printSuccess
            ],
            failureActions = [
                self.__hideLoadingIndicator,
                printFailure
            ]
        )

    def __reloadButtonHTML(self):
        buttonManifest = self.__reloadButtonManifest()
        ButtonManifestRegistry.add([buttonManifest])
        return buttonManifest.html(cssClass = 'reload_tickets')

    def __saveURLAndToken(self):
        url = self.window.evaluate_js(f'__getPhabricatorUrl()')
        token = self.window.evaluate_js(f'__getPhabricatorToken()')
        configuration = DataStore.getCurrentConfiguration()
        configuration['url'] = url.strip()
        configuration['token'] = token.strip()
        DataStore.saveCurrentConfiguration()
        return True

    def __reloadFetcher(self):
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

    def __refetchPrioritiesAndStatuses(self):
        self.prioritiesData, self.statusesData = self.__fetchPrioritiesAndStatuses()
        return True

    def __refetchUpstreamCSSLinkURL(self):
        cssURL = self.__extractCSSURL()
        self.window.evaluate_js(f'__setUpstreamCSSLinkURL("{cssURL}")')
        return True

    def __resetUpstreamBaseURL(self):
        configuration = DataStore.getCurrentConfiguration()
        self.window.evaluate_js(f'''__setUpstreamBaseURL("{configuration['url']}")''')
        return True

    def __urlAndTokenSaveButtonManifest(self):
        return ButtonManifest(
            id = Utilities.cssSafeGUID(),
            title = 'Save',
            isInitiallySelected = False,
            clickActions = [
                self.__showLoadingIndicator,
                self.__saveURLAndToken
            ],
            successActions = [
                self.__hideLoadingIndicator,
                self.__reloadFetcher,
                self.__refetchPrioritiesAndStatuses,
                self.__clearSourceAndDestinationProjects,
                self.__hideTickets,
                self.__refetchUpstreamCSSLinkURL,
                self.__resetUpstreamBaseURL,
                self.__reloadConfigurationUI,
                printSuccess
            ],
            failureActions = [
                self.__hideLoadingIndicator,
                printFailure
            ]
        )

    def __clearSourceAndDestinationProjects(self):
        destinationProject = DataStore.getConfigurationValue('destinationProject')
        destinationProject['phid'] = None
        destinationProject['ignoreColumns'] = []
        sourceProjects = DataStore.getConfigurationValue('sourceProjects')
        sourceProjects.clear()
        DataStore.saveCurrentConfiguration()

    def __urlAndTokenSaveButtonHTML(self):
        buttonManifest = self.__urlAndTokenSaveButtonManifest()
        ButtonManifestRegistry.add([buttonManifest])
        return buttonManifest.html(cssClass = 'save_url_and_token')

    def __reloadConfigurationUI(self):
        self.reload(hydrateTickets = False)

    def __hideProjectSearch(self):
        return self.window.evaluate_js('__hideProjectSearch()')

    def __saveProjectSearchChoice(self, projectPHID, mode):
        if mode == 'destination':
            self.__saveDestinationProjectPHID(projectPHID)
        elif mode == 'source':
            self.__saveSourceProjectPHID(projectPHID)
        else:
            print(f'Unhandled mode: "{mode}"')
            return False
        return True

    def __projectSearchResultButtonManifest(self, projectName, projectPHID, mode):
        return ButtonManifest(
            id = Utilities.cssSafeGUID(),
            title = projectName,
            isInitiallySelected = False,
            clickActions = [
                self.__showLoadingIndicator,
                lambda projectPHID=projectPHID, mode=mode :
                    self.__saveProjectSearchChoice(projectPHID, mode)
            ],
            successActions = [
                self.__hideLoadingIndicator,
                self.__hideProjectSearch,
                self.__reloadConfigurationUI
            ],
            failureActions = [
                self.__hideLoadingIndicator,
                printFailure
            ]
        )

    def __projectSearchResultButtonHTML(self, title, phid, mode):
        buttonManifest = self.__projectSearchResultButtonManifest(title, phid, mode)
        ButtonManifestRegistry.add([buttonManifest])
        return buttonManifest.html(cssClass = 'projects_search_result')

    def __showProjectSearch(self, mode, title):
        return self.window.evaluate_js(f"__showProjectSearch(`{mode}`, `{title}`)")

    def __resetProjectSearch(self):
        return self.window.evaluate_js('__resetProjectSearch()')

    def __showProjectSearchButtonManifest(self, title, mode):
        return ButtonManifest(
            id = Utilities.cssSafeGUID(),
            title = title,
            isInitiallySelected = False,
            clickActions = [
                self.__resetProjectSearch,
                lambda mode=mode :
                    self.__showProjectSearch(mode = mode, title = title)
            ],
            successActions = [
                printSuccess
            ],
            failureActions = [
                printFailure
            ]
        )

    def __showProjectSearchButtonHTML(self, title, mode):
        buttonManifest = self.__showProjectSearchButtonManifest(title, mode)
        ButtonManifestRegistry.add([buttonManifest])
        return buttonManifest.html(cssClass = 'add')

    def __rightProjectMenuDiv(self, deleteProjectButtonHTML):
        return f'''
            <div class="right_project_menu">
                {deleteProjectButtonHTML}
            </div>
        '''

    def __showLoadingIndicator(self):
        return self.window.evaluate_js(f"__showLoadingIndicator()")

    def __hideLoadingIndicator(self):
        return self.window.evaluate_js(f"__hideLoadingIndicator()")

    def __showAlert(self, title, description):
        return self.window.evaluate_js(f"__showAlert(`{title}`, `{description}`)")

    def __wrapWithButtonMenuTag(self, menuTitle, menuButtons, showRightProjectMenu = False, deleteProjectButtonHTML = ''):
        rightProjectMenuDiv = self.__rightProjectMenuDiv(deleteProjectButtonHTML = deleteProjectButtonHTML) if showRightProjectMenu else ''
        mouseOverAndOut = f' onmouseover="__configurationProjectMouseOver(this)" onmouseout="__configurationProjectMouseOut(this)"' if showRightProjectMenu else ''
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

    def __deleteMenu(self, buttonID):
        return self.window.evaluate_js(f"__deleteMenu('{buttonID}')")

    def __removeDestinationProjectFromConfigurationJSON(self):
        destinationProject = DataStore.getConfigurationValue('destinationProject')
        destinationProject['phid'] = None
        destinationProject['ignoreColumns'] = []
        DataStore.saveCurrentConfiguration()
        DataStore.loadConfiguration()
        return True

    def __removeDestinationProjectFromConfigurationJSONButtonManifest(self):
        buttonID = Utilities.cssSafeGUID()
        return ButtonManifest(
            id = buttonID,
            title = 'Remove',
            isInitiallySelected = False,
            clickActions = [
                self.__showLoadingIndicator,
                self.__hideTickets,
                self.__removeDestinationProjectFromConfigurationJSON
            ],
            successActions = [
                self.__hideLoadingIndicator,
                lambda buttonID=buttonID :
                    self.__deleteMenu(buttonID),
                printSuccess
            ],
            failureActions = [
                self.__hideLoadingIndicator,
                printFailure
            ]
        )

    def __toggleButton(self, buttonID):
        return self.window.evaluate_js(f"__toggleButton('{buttonID}')")

    def __toggleDestinationProjectColumnInConfigurationJSON(self, columnPHID, indexOfColumnToToggle):
        project = DataStore.getConfigurationValue('destinationProject')
        if self.__isDestinationProjectIgnoreColumnPresentInConfigurationJSON(columnPHID):
            project['ignoreColumns'].remove(columnPHID)
        else:
            project['ignoreColumns'].insert(indexOfColumnToToggle, columnPHID)
        DataStore.saveCurrentConfiguration()
        return True

    def __hideTickets(self):
        self.window.evaluate_js('__hideTickets()')

    def __toggleDestinationProjectColumnInConfigurationJSONButtonManifest(self, buttonID, title, indexOfColumnToToggle, columnPHID, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [
                self.__showLoadingIndicator,
                self.__hideTickets,
                lambda columnPHID=columnPHID, indexOfColumnToToggle=indexOfColumnToToggle :
                    self.__toggleDestinationProjectColumnInConfigurationJSON(columnPHID, indexOfColumnToToggle)
            ],
            successActions = [
                self.__hideLoadingIndicator,
                lambda buttonID=buttonID :
                    self.__toggleButton(buttonID)
            ],
            failureActions = [
                self.__hideLoadingIndicator,
                printFailure
            ]
        )

    def __toggleDestinationProjectColumnInConfigurationButtonMenuHTML(self, menuTitle, columns):
        buttonManifests = list(map(lambda indexAndColumnTuple: self.__toggleDestinationProjectColumnInConfigurationJSONButtonManifest(
            buttonID = Utilities.cssSafeGUID(),
            title = indexAndColumnTuple[1].name,
            indexOfColumnToToggle = indexAndColumnTuple[0],
            columnPHID = indexAndColumnTuple[1].phid,
            isInitiallySelected = not self.__isDestinationProjectIgnoreColumnPresentInConfigurationJSON(indexAndColumnTuple[1].phid)
        ), enumerate(columns)))
        ButtonManifestRegistry.add(buttonManifests)

        deleteButtonManifest = self.__removeDestinationProjectFromConfigurationJSONButtonManifest()
        ButtonManifestRegistry.add([deleteButtonManifest])

        return self.__wrapWithButtonMenuTag(
            menuTitle = menuTitle,
            menuButtons = ' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests)),
            showRightProjectMenu = True,
            deleteProjectButtonHTML = deleteButtonManifest.html(cssClass = 'delete')
        )

    def __removeSourceProjectFromConfigurationJSON(self, projectPHID):
        sourceProjects = DataStore.getConfigurationValue('sourceProjects')
        project = next(project for project in sourceProjects if project['phid'] == projectPHID)
        sourceProjects.remove(project)
        DataStore.saveCurrentConfiguration()
        DataStore.loadConfiguration()
        return True

    def __removeSourceProjectFromConfigurationJSONButtonManifest(self, projectPHID):
        buttonID = Utilities.cssSafeGUID()
        return ButtonManifest(
            id = buttonID,
            title = 'Remove',
            isInitiallySelected = False,
            clickActions = [
                self.__showLoadingIndicator,
                self.__hideTickets,
                lambda projectPHID=projectPHID :
                    self.__removeSourceProjectFromConfigurationJSON(projectPHID)
            ],
            successActions = [
                self.__hideLoadingIndicator,
                lambda buttonID=buttonID :
                    self.__deleteMenu(buttonID),
                printSuccess
            ],
            failureActions = [
                self.__hideLoadingIndicator,
                printFailure
            ]
        )

    def __toggleSourceProjectColumnInConfigurationJSON(self, columnPHID, indexOfColumnToToggle, projectPHID):
        sourceProjects = DataStore.getConfigurationValue('sourceProjects')
        project = next(project for project in sourceProjects if project['phid'] == projectPHID)
        if self.__isSourceProjectColumnPresentInConfigurationJSON(columnPHID, projectPHID):
            project['columns'].remove(columnPHID)
        else:
            project['columns'].insert(indexOfColumnToToggle, columnPHID)
        DataStore.saveCurrentConfiguration()
        return True

    def __toggleSourceProjectColumnInConfigurationJSONButtonManifest(self, buttonID, title, indexOfColumnToToggle, columnPHID, projectPHID, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [
                self.__showLoadingIndicator,
                self.__hideTickets,
                lambda columnPHID=columnPHID, indexOfColumnToToggle=indexOfColumnToToggle, projectPHID=projectPHID :
                    self.__toggleSourceProjectColumnInConfigurationJSON(columnPHID, indexOfColumnToToggle, projectPHID)
            ],
            successActions = [
                self.__hideLoadingIndicator,
                lambda buttonID=buttonID :
                    self.__toggleButton(buttonID)
            ],
            failureActions = [
                self.__hideLoadingIndicator,
                printFailure
            ]
        )

    def __toggleSourceProjectColumnInConfigurationButtonMenuHTML(self, menuTitle, columns, projectPHID):
        buttonManifests = list(map(lambda indexAndColumnTuple: self.__toggleSourceProjectColumnInConfigurationJSONButtonManifest(
            buttonID = Utilities.cssSafeGUID(),
            title = indexAndColumnTuple[1].name,
            indexOfColumnToToggle = indexAndColumnTuple[0],
            columnPHID = indexAndColumnTuple[1].phid,
            projectPHID = projectPHID,
            isInitiallySelected = self.__isSourceProjectColumnPresentInConfigurationJSON(indexAndColumnTuple[1].phid, projectPHID)
        ), enumerate(columns)))
        ButtonManifestRegistry.add(buttonManifests)

        deleteButtonManifest = self.__removeSourceProjectFromConfigurationJSONButtonManifest(projectPHID)
        ButtonManifestRegistry.add([deleteButtonManifest])

        return self.__wrapWithButtonMenuTag(
            menuTitle = f'''{menuTitle}''',
            menuButtons = f'''
                {' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))}
            ''',
            showRightProjectMenu = True,
            deleteProjectButtonHTML = deleteButtonManifest.html(cssClass = 'delete')
        )

    def __isColumnPHIDPresentInTicketJSON(self, columnPHID, ticketJSON):
        boards = ticketJSON['attachments']['columns']['boards']
        arrayOfColumnPHIDArrays = map(lambda board:
            map(lambda column: column['phid'], board['columns']),
            boards.values()
        )
        arrayOfColumnPHIDs = [item for sublist in arrayOfColumnPHIDArrays for item in sublist]
        return columnPHID in arrayOfColumnPHIDs

    def __ticketAddToColumnButtonMenuHTML(self, menuTitle, ticketID, ticketJSON, columns):
        # print(json.dumps(ticketJSON, indent=4))
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

    def __getNumericIDFromTicketID(self, ticketID):
        return re.sub("[^0-9]", '', ticketID)

    def __getComment(self, ticketID):
        comment = self.window.evaluate_js(f'__getComment("{self.__getNumericIDFromTicketID(ticketID)}")')
        return comment if len(comment.strip()) else None

    def __setComment(self, ticketID, comment):
        returnedComment = self.window.evaluate_js(f'__setComment("{self.__getNumericIDFromTicketID(ticketID)}", "{comment}")')
        return returnedComment == comment

    def __deselectOtherButtonsInMenu(self, buttonID):
        return self.window.evaluate_js(f'__deselectOtherButtonsInMenu("{buttonID}")')

    def __setTicketActionMessage(self, ticketID, message):
        return self.window.evaluate_js(f'__setTicketActionMessage("{self.__getNumericIDFromTicketID(ticketID)}", "{message}")')

    def __showTicketFailure(self, ticketID):
        return self.__setTicketActionMessage(ticketID, '💩 Failure')

    def __showTicketSuccess(self, ticketID):
        return self.__setTicketActionMessage(ticketID, '🎉 Success')

    def __addTicketToProject(self, ticketID, projectPHID):
        return self.fetcher.callEndpoint(
            path = '/api/maniphest.edit',
            key = 'projects.add',
            value = projectPHID,
            objectIdentifier = ticketID,
            comment = None,
            needsValueArgumentInArray = True
        )

    def __removeTicketFromProject(self, ticketID, projectPHID):
        return self.fetcher.callEndpoint(
            path = '/api/maniphest.edit',
            key = 'projects.remove',
            value = projectPHID,
            objectIdentifier = ticketID,
            comment = self.__getComment(ticketID),
            needsValueArgumentInArray = True
        )

    def __addTicketToColumn(self, ticketID, columnPHID):
        return self.fetcher.callEndpoint(
            path = '/api/maniphest.edit',
            key = 'column',
            value = columnPHID,
            objectIdentifier = ticketID,
            comment = self.__getComment(ticketID),
            needsValueArgumentInArray = True
        )

    def __isButtonSelected(self, buttonID):
        return self.window.evaluate_js(f'__isButtonSelected("{buttonID}")')

    def __toggleTicketOnProjectColumn(self, ticketID, projectPHID, columnPHID, buttonID):
        if self.__isButtonSelected(buttonID):
            if not self.__removeTicketFromProject(ticketID, projectPHID):
                return False
        else:
            if not self.__addTicketToProject(ticketID, projectPHID):
                return False
            if not self.__addTicketToColumn(ticketID, columnPHID):
                return False
        return True

    def __ticketToggleColumnButtonManifest(self, buttonID, title, ticketID, projectPHID, columnPHID, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [
                self.__showLoadingIndicator,
                lambda ticketID=ticketID, projectPHID=projectPHID, columnPHID=columnPHID, buttonID=buttonID :
                    self.__toggleTicketOnProjectColumn(ticketID, projectPHID, columnPHID, buttonID)
            ],
            successActions = [
                self.__hideLoadingIndicator,
                lambda ticketID=ticketID :
                    self.__showTicketSuccess(ticketID),
                lambda buttonID=buttonID :
                    self.__toggleButton(buttonID),
                lambda buttonID=buttonID :
                    self.__deselectOtherButtonsInMenu(buttonID),
                lambda buttonID=buttonID :
                    self.__setComment(ticketID, '')
            ],
            failureActions = [
                self.__hideLoadingIndicator,
                lambda ticketID=ticketID :
                    self.__showTicketFailure(ticketID),
            ]
        )

    def __selectButton(self, buttonID):
        return self.window.evaluate_js(f'__selectButton("{buttonID}")')

    def __updateTicketStatus(self, ticketID, value):
        return self.fetcher.callEndpoint(
            path = '/api/maniphest.edit',
            key = 'status',
            value = value,
            objectIdentifier = ticketID,
            comment = self.__getComment(ticketID)
        )

    def __ticketStatusButtonManifest(self, buttonID, title, ticketID, value, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [
                self.__showLoadingIndicator,
                lambda ticketID=ticketID, value=value :
                    self.__updateTicketStatus(ticketID, value)
            ],
            successActions = [
                self.__hideLoadingIndicator,
                lambda ticketID=ticketID :
                    self.__showTicketSuccess(ticketID),
                lambda buttonID=buttonID :
                    self.__selectButton(buttonID),
                lambda buttonID=buttonID :
                    self.__deselectOtherButtonsInMenu(buttonID),
                lambda buttonID=buttonID :
                    self.__setComment(ticketID, '')
            ],
            failureActions = [
                self.__hideLoadingIndicator,
                lambda ticketID=ticketID :
                    self.__showTicketFailure(ticketID),
            ]
        )

    def __ticketStatusButtonMenuHTML(self, menuTitle, ticketID, ticketJSON):
        buttonManifests = list(map(lambda status: self.__ticketStatusButtonManifest(
            buttonID = Utilities.cssSafeGUID(),
            title = status['name'],
            ticketID = f'T{ticketID}',
            value = status['value'],
            isInitiallySelected = ticketJSON['fields']['status']['name'] == status['name']
        ), self.statusesData))

        ButtonManifestRegistry.add(buttonManifests)

        return self.__wrapWithButtonMenuTag(
            menuTitle = menuTitle,
            menuButtons = ' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))
        )

    def __updateTicketPriority(self, ticketID, value):
        return self.fetcher.callEndpoint(
            path = '/api/maniphest.edit',
            key = 'priority',
            value = value,
            objectIdentifier = ticketID,
            comment = self.__getComment(ticketID)
        )

    def __ticketPriorityButtonManifest(self, buttonID, title, ticketID, value, isInitiallySelected = False):
        return ButtonManifest(
            id = buttonID,
            title = title,
            isInitiallySelected = isInitiallySelected,
            clickActions = [ # lambda currying: https://stackoverflow.com/a/452659
                self.__showLoadingIndicator,
                lambda ticketID=ticketID, value=value :
                    self.__updateTicketPriority(ticketID, value),
                lambda title=title :
                    print(title)
            ],
            successActions = [
                self.__hideLoadingIndicator,
                lambda ticketID=ticketID :
                    self.__showTicketSuccess(ticketID),
                lambda buttonID=buttonID :
                    self.__selectButton(buttonID),
                lambda buttonID=buttonID :
                    self.__deselectOtherButtonsInMenu(buttonID),
                lambda buttonID=buttonID :
                    self.__setComment(ticketID, '')
            ],
            failureActions = [
                self.__hideLoadingIndicator,
                lambda ticketID=ticketID :
                    self.__showTicketFailure(ticketID),
            ]
        )

    def __ticketPriorityButtonMenuHTML(self, menuTitle, ticketID, ticketJSON):
        buttonManifests = list(map(lambda priority: self.__ticketPriorityButtonManifest(
            buttonID = Utilities.cssSafeGUID(),
            title = priority['name'],
            ticketID = f'T{ticketID}',
            value = priority['keywords'][0],
            isInitiallySelected = ticketJSON['fields']['priority']['name'] == priority['name']
        ), self.prioritiesData))

        ButtonManifestRegistry.add(buttonManifests)

        return self.__wrapWithButtonMenuTag(
            menuTitle = menuTitle,
            menuButtons = ' '.join(map(lambda buttonManifest: buttonManifest.html(), buttonManifests))
        )

    def __saveDestinationProjectPHID(self, projectPHID):
        destinationProject = DataStore.getConfigurationValue('destinationProject')
        destinationProject['phid'] = projectPHID
        destinationProject['ignoreColumns'] = []
        DataStore.saveCurrentConfiguration()

    def __saveSourceProjectPHID(self, projectPHID):
        sourceProjects = DataStore.getConfigurationValue('sourceProjects')
        if not any(project['phid'] == projectPHID for project in sourceProjects):
            sourceProjects.insert(0, {
                'phid': projectPHID,
                'columns': []
            })
            DataStore.saveCurrentConfiguration()
        else:
            print(f'{projectPHID} already exists in project sources')

    def __isSourceProjectColumnPresentInConfigurationJSON(self, columnPHID, projectPHID):
        projects = DataStore.getConfigurationValue('sourceProjects')
        project = next(project for project in projects if project['phid'] == projectPHID)
        isColumnPresent = columnPHID in project['columns']
        return isColumnPresent

    def __isDestinationProjectIgnoreColumnPresentInConfigurationJSON(self, columnPHID):
        return columnPHID in DataStore.getConfigurationValue('destinationProject')['ignoreColumns']

    def expose(self, window):
        window.expose(self.projectSearchTermEntered) # expose to JS as 'pywebview.api.projectSearchTermEntered'
        window.expose(self.isSavedURLAndTokenSameAsInTextboxes) # expose to JS as 'pywebview.api.isSavedURLAndTokenSameAsInTextboxes'
        window.expose(printDebug) # expose to JS as 'pywebview.api.printDebug'

def printDebug(message):
    print(message)

def printSuccess():
    print('success!')

def printFailure():
    print('failure!')
