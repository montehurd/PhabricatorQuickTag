#!/usr/local/bin/python3

import Utilities, time, re, json, webview, ButtonManifestRegistry, DataStore, uuid
from string import Template
from ProjectsHydrator import ProjectsHydrator
from ButtonManifest import ButtonManifest
from Project import Project

class WebviewController:
    def __init__(self, window, fetcher):
        self.fetcher = fetcher
        self.sourceProjects = []
        self.destinationProject = None
        self.window = window
        self.window.loaded += self.__onDOMLoaded
        self.prioritiesData = self.fetcher.fetchPriorities()
        self.statusesData = self.fetcher.fetchStatuses()

    def __extractCSSURL(self):
        # HACK: grabbing the css url from the 'flag' page html. perhaps there's a better way? some API?
        html = self.fetcher.fetchHTML('/flag')
        match = re.search(r'<link[^>]* rel="stylesheet"[^>]* href="([^"]*?core\.pkg\.css)"', html)
        return match.group(1)

    def __getTemplateHTML(self):
        return Template(Utilities.stringFromFile('lib/Template.html')).substitute(
            TEMPLATE_BASE_URL = self.fetcher.baseURL,
            TEMPLATE_CSS_URL = self.__extractCSSURL(),
            TEMPLATE_API_TOKEN = self.fetcher.apiToken
        )

    def __getTemplateCSS(self):
        return Utilities.stringFromFile('lib/Template.css')

    def __setInnerHTML(self, selector, html):
        return self.window.evaluate_js(f"__setInnerHTML('{selector}', `{Utilities.escapeBackticks(html)}`)")

    def __setLoadingMessage(self, message):
        print(message)
        self.window.set_title(f"{'' if len(message.strip()) > 0 else 'Phabricator Quick Tag'}{message}")

    def __setConfigurationButtonsHTML(self):
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

    def __load(self, hydrateTickets = True):
        self.sourceProjects = self.__getDehydratedSourceProjects()
        self.destinationProject = self.__getDehydratedDestinationProject()
        self.__setLoadingMessage('Beginning data retrieval')
        ProjectsHydrator(
            sourceProjects = self.sourceProjects,
            destinationProject = self.destinationProject,
            fetcher = self.fetcher,
            loadingMessageSetter = self.__setLoadingMessage,
            ticketAddToColumnButtonMenuHTMLFunction = self.__ticketAddToColumnButtonMenuHTML,
            ticketStatusButtonMenuHTMLFunction = self.__ticketStatusButtonMenuHTML,
            ticketPriorityButtonMenuHTMLFunction = self.__ticketPriorityButtonMenuHTML
        ).hydrateProjects(hydrateTickets = hydrateTickets)

        self.__setLoadingMessage('')

        # can start html generation now that projects are hydrated
        self.__setConfigurationButtonsHTML()
        if not hydrateTickets:
            return
        self.__setInnerHTML('div.projects_tickets', self.__projectsTicketsHTML())

    def __onDOMLoaded(self):
        self.window.loaded -= self.__onDOMLoaded # unsubscribe event listener
        self.window.load_html(self.__getTemplateHTML())
        self.window.load_css(self.__getTemplateCSS())
        time.sleep(1.0)
        self.__load()

    def reload(self, hydrateTickets = True):
        ButtonManifestRegistry.clear()
        DataStore.loadConfiguration()
        self.__load(hydrateTickets = hydrateTickets)

    def projectSearchTermEntered(self, searchTerm, mode):
        searchResultsSelector = 'div.projects_search_results'
        if len(searchTerm.strip()) == 0:
            self.__setInnerHTML(searchResultsSelector, '')
        else:
            projects = self.fetcher.fetchProjectsMatchingSearchTerm(searchTerm)
            projectSearchResultButtonsHTML = ''.join(map(lambda item: self.__projectSearchResultButtonHTML(title = item[1], phid = item[0], mode = mode), projects.items()))
            self.__setInnerHTML(searchResultsSelector, projectSearchResultButtonsHTML)

    def textboxTermEntered(self, term, key):
        configuration = DataStore.getCurrentConfiguration()
        configuration[key] = term
        DataStore.saveCurrentConfiguration()

    def __showTickets(self):
        return self.window.evaluate_js('__showTickets()')

    def __reloadButtonManifest(self):
        return ButtonManifest(
            id = Utilities.cssSafeGUID(),
            title = 'Reload Tickets',
            isInitiallySelected = False,
            clickActions = [
                self.reload
            ],
            successActions = [
                self.__showTickets,
                printSuccess
            ],
            failureActions = [
                printFailure
            ]
        )

    def __reloadButtonHTML(self):
        buttonManifest = self.__reloadButtonManifest()
        ButtonManifestRegistry.add([buttonManifest])
        return buttonManifest.html(cssClass = 'reload_tickets')

    def __showModalOverlay(self):
        return self.window.evaluate_js('__showModalOverlay()')

    def __hideModalOverlay(self):
        return self.window.evaluate_js('__hideModalOverlay()')

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
                lambda projectPHID=projectPHID, mode=mode :
                    self.__saveProjectSearchChoice(projectPHID, mode)
            ],
            successActions = [
                self.__hideProjectSearch,
                self.__reloadConfigurationUI,
                self.__hideModalOverlay
            ],
            failureActions = [
                printFailure
            ]
        )

    def __projectSearchResultButtonHTML(self, title, phid, mode):
        buttonManifest = self.__projectSearchResultButtonManifest(title, phid, mode)
        ButtonManifestRegistry.add([buttonManifest])
        return buttonManifest.html(cssClass = 'projects_search_result')

    def __hideProjectSearchButtonManifest(self, title):
        return ButtonManifest(
            id = Utilities.cssSafeGUID(),
            title = title,
            isInitiallySelected = False,
            clickActions = [
                self.__hideProjectSearch,
                self.__hideModalOverlay
            ],
            successActions = [
                printSuccess
            ],
            failureActions = [
                printFailure
            ]
        )

    def __hideProjectSearchButtonHTML(self, title):
        buttonManifest = self.__hideProjectSearchButtonManifest(title)
        ButtonManifestRegistry.add([buttonManifest])
        return buttonManifest.html(cssClass = 'projects_search_hide')

    def __showProjectSearch(self, mode, hideButtonHTML, title):
        return self.window.evaluate_js(f"__showProjectSearch(`{mode}`, `{hideButtonHTML}`, `{title}`)")

    def __resetProjectSearch(self):
        return self.window.evaluate_js('__resetProjectSearch()')

    def __showProjectSearchButtonManifest(self, title, mode):
        hideButtonHTML = self.__hideProjectSearchButtonHTML(title = 'Hide')
        return ButtonManifest(
            id = Utilities.cssSafeGUID(),
            title = title,
            isInitiallySelected = False,
            clickActions = [
                self.__resetProjectSearch,
                self.__showModalOverlay,
                lambda mode=mode :
                    self.__showProjectSearch(mode = mode, hideButtonHTML = hideButtonHTML, title = title)
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
                self.__hideTickets,
                self.__removeDestinationProjectFromConfigurationJSON
            ],
            successActions = [
                lambda buttonID=buttonID :
                    self.__deleteMenu(buttonID),
                printSuccess
            ],
            failureActions = [
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
                self.__hideTickets,
                lambda columnPHID=columnPHID, indexOfColumnToToggle=indexOfColumnToToggle :
                    self.__toggleDestinationProjectColumnInConfigurationJSON(columnPHID, indexOfColumnToToggle)
            ],
            successActions = [
                lambda buttonID=buttonID :
                    self.__toggleButton(buttonID)
            ],
            failureActions = [
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
                self.__hideTickets,
                lambda projectPHID=projectPHID :
                    self.__removeSourceProjectFromConfigurationJSON(projectPHID)
            ],
            successActions = [
                lambda buttonID=buttonID :
                    self.__deleteMenu(buttonID),
                printSuccess
            ],
            failureActions = [
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
                self.__hideTickets,
                lambda columnPHID=columnPHID, indexOfColumnToToggle=indexOfColumnToToggle, projectPHID=projectPHID :
                    self.__toggleSourceProjectColumnInConfigurationJSON(columnPHID, indexOfColumnToToggle, projectPHID)
            ],
            successActions = [
                lambda buttonID=buttonID :
                    self.__toggleButton(buttonID)
            ],
            failureActions = [
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
                lambda ticketID=ticketID, projectPHID=projectPHID, columnPHID=columnPHID, buttonID=buttonID :
                    self.__toggleTicketOnProjectColumn(ticketID, projectPHID, columnPHID, buttonID)
            ],
            successActions = [
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
                lambda ticketID=ticketID, value=value :
                    self.__updateTicketStatus(ticketID, value)
            ],
            successActions = [
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
                lambda ticketID=ticketID, value=value :
                    self.__updateTicketPriority(ticketID, value),
                lambda title=title :
                    print(title)
            ],
            successActions = [
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
        window.expose(self.textboxTermEntered) # expose to JS as 'pywebview.api.textboxTermEntered'
        window.expose(printDebug) # expose to JS as 'pywebview.api.printDebug'

def printDebug(message):
    print(message)

def printSuccess():
    print('success!')

def printFailure():
    print('failure!')
