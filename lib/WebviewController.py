#!/usr/local/bin/python3

import Utilities, time, re, json, webview, ButtonManifestRegistry, DataStore
from string import Template
from ProjectsHydrator import ProjectsHydrator
from ButtonFactory import ButtonFactory
from Project import Project

class WebviewController:
    def __init__(self, window, fetcher):
        self.fetcher = fetcher
        self.sourceProjects = []
        self.destinationProject = None
        self.window = window
        self.window.loaded += self.onDOMLoaded

    def extractCSSURL(self):
        # HACK: grabbing the css url from the 'flag' page html. perhaps there's a better way? some API?
        html = self.fetcher.fetchHTML('/flag')
        match = re.search(r'<link[^>]* rel="stylesheet"[^>]* href="([^"]*?core\.pkg\.css)"', html)
        return match.group(1)

    def getWrapperHTML(self):
        return Template(Utilities.stringFromFile('lib/Template.html')).substitute(
            TEMPLATE_BASE_URL = self.fetcher.baseURL,
            TEMPLATE_CSS_URL = self.extractCSSURL(),
            TEMPLATE_API_TOKEN = self.fetcher.apiToken
        )

    def setInnerHTML(self, selector, html):
        return self.window.evaluate_js(f"""
            document.querySelector('{selector}').innerHTML = `{Utilities.escapeBackticks(html)}`
            // reminder: can return a result by placing the value on the next line
            """
        )

    def setLoadingMessage(self, message):
        return self.setInnerHTML('div.loading-message', message)

    def projectsConfigurationHTML(self):
        sourcesHTML = ''.join(map(lambda project: ButtonFactory(self.fetcher).toggleSourceProjectColumnInConfigurationButtonMenuHTML(project.name, project.buttonsMenuColumnNames, project.name), self.sourceProjects))
        destinationHTML = ButtonFactory(self.fetcher).toggleDestinationProjectColumnInConfigurationButtonMenuHTML(self.destinationProject.name, self.destinationProject.buttonsMenuColumnNames) if self.destinationProject != None else ''
        mouseOverAndOut = f''' onmouseover="this.classList.add('menu_highlighted');this.querySelectorAll('div.right_project_menu').forEach(e => e.style.visibility = 'visible');" onmouseout="this.classList.remove('menu_highlighted');this.querySelectorAll('div.right_project_menu').forEach(e => e.style.visibility = 'hidden');"'''
        return f'''
                <div class=projects_configuration_header>
                    <div class=projects_configuration_title>
                        <b>⚙️&nbsp;&nbsp;Current Configuration</b>
                        <div class=projects_configuration_body_buttons>
                            {ButtonFactory(self.fetcher).reloadButtonHTML()}
                        </div>
                    </div>
                </div>
                <div class=projects_configuration_body>
                    <div class=project_configuration_heading {mouseOverAndOut}>
                        <div class=right_project_menu>
                            {ButtonFactory(self.fetcher).showProjectSearchButtonHTML(title = 'Add a Source Project', mode = 'source')}
                        </div>
                        <b>Ticket Sources:</b>
                    </div>
                    {sourcesHTML}
                    <div class=project_configuration_heading {mouseOverAndOut}>
                        <div class=right_project_menu>
                            {ButtonFactory(self.fetcher).showProjectSearchButtonHTML(title = 'Add or change Destination Project', mode = 'destination')}
                        </div>
                        <b>Ticket Destination Columns:</b> (optional)
                    </div>
                    {destinationHTML}
                </div>
        '''

    def projectsTicketsHTML(self):
        print(f'Fetching complete')
        print(f'Processing hydrated object graph')
        html = []
        for project in self.sourceProjects:
            for column in project.columns:
                html.append(f'<div class=column_source>Ticket Source: <span class=column_identifier>{project.name} > {column.name}</span></div>')
                html.append(column.ticketsHTMLIncludingWrapperDivsAndMenus)
        print(f'Page HTML assembled')
        return ''.join(html)

    def getDehydratedSourceProjects(self):
        return list(map(lambda projectJSON:
            Project(
                name = projectJSON['name'],
                columnNames = projectJSON['columns']
            ),
            DataStore.getConfigurationValue('sourceProjects')
        ))

    def getDehydratedDestinationProject(self):
        if 'name' not in DataStore.getConfigurationValue('destinationProject').keys():
            return None
        if DataStore.getConfigurationValue('destinationProject')['name'] == None:
            return None
        return Project(
            name = DataStore.getConfigurationValue('destinationProject')['name'],
            columnNamesToIgnoreForButtons = DataStore.getConfigurationValue('destinationProject')['ignoreColumns']
        )

    def load(self, hydrateTickets = True):
        self.sourceProjects = self.getDehydratedSourceProjects()
        self.destinationProject = self.getDehydratedDestinationProject()
        self.window.load_html(self.getWrapperHTML())
        time.sleep(1.0)

        self.setLoadingMessage('Beginning data retrieval')
        ProjectsHydrator(
            sourceProjects = self.sourceProjects,
            destinationProject = self.destinationProject,
            fetcher = self.fetcher,
            loadingMessageSetter = self.setLoadingMessage
        ).hydrateProjects(hydrateTickets = hydrateTickets)

        self.setLoadingMessage('')

        # can start html generation now that projects are hydrated
        self.setInnerHTML('div.projects_configuration', self.projectsConfigurationHTML())
        if not hydrateTickets:
            return
        self.setInnerHTML('div.projects_tickets', self.projectsTicketsHTML())

    def onDOMLoaded(self):
        self.window.loaded -= self.onDOMLoaded # unsubscribe event listener
        self.load()

    def reload(self, hydrateTickets = True):
        ButtonManifestRegistry.clear()
        DataStore.loadConfiguration()
        self.load(hydrateTickets = hydrateTickets)

    def projectSearchTermEntered(self, searchTerm, mode):
        searchResultsSelector = 'div.projects_search_results'
        if len(searchTerm.strip()) == 0:
            self.setInnerHTML(searchResultsSelector, '')
        else:
            projectNames = self.fetcher.fetchProjectNamesMatchingSearchTerm(searchTerm)
            projectSearchResultButtonsHTML = ''.join(map(lambda projectName: ButtonFactory(self.fetcher).projectSearchResultButtonHTML(projectName, mode), projectNames))
            self.setInnerHTML(searchResultsSelector, projectSearchResultButtonsHTML)

    def expose(self, window):
        window.expose(self.reload) # expose to JS as 'pywebview.api.reload'
        window.expose(self.projectSearchTermEntered) # expose to JS as 'pywebview.api.projectSearchTermEntered'
