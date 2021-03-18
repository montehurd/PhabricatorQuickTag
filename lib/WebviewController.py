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
        self.window.loaded += self.__onDOMLoaded

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
        return self.window.evaluate_js(f"""
            document.querySelector('{selector}').innerHTML = `{Utilities.escapeBackticks(html)}`
            // reminder: can return a result by placing the value on the next line
            """
        )

    def __setLoadingMessage(self, message):
        return self.__setInnerHTML('div.loading-message', message)

    def __setConfigurationButtonsHTML(self):
        self.__setInnerHTML('div#projects_configuration_body_buttons', ButtonFactory(self.fetcher).reloadButtonHTML())
        self.__setInnerHTML('div#sources_right_menu', ButtonFactory(self.fetcher).showProjectSearchButtonHTML(title = 'Add a Source Project', mode = 'source'))
        self.__setInnerHTML('div#destination_right_menu', ButtonFactory(self.fetcher).showProjectSearchButtonHTML(title = 'Add or change Destination Project', mode = 'destination'))
        sourceProjectsMenuButtonsHTML = ''.join(map(lambda project: ButtonFactory(self.fetcher).toggleSourceProjectColumnInConfigurationButtonMenuHTML(project.name, project.buttonsMenuColumnNames, project.name), self.sourceProjects))
        self.__setInnerHTML('div#projects_configuration_sources', sourceProjectsMenuButtonsHTML)
        destinationProjectMenuButtonsHTML = ButtonFactory(self.fetcher).toggleDestinationProjectColumnInConfigurationButtonMenuHTML(self.destinationProject.name, self.destinationProject.buttonsMenuColumnNames) if self.destinationProject != None else ''
        self.__setInnerHTML('div#projects_configuration_destination', destinationProjectMenuButtonsHTML)

    def __projectsTicketsHTML(self):
        print(f'Fetching complete')
        print(f'Processing hydrated object graph')
        html = []
        for project in self.sourceProjects:
            for column in project.columns:
                html.append(f'<div class=column_source>Ticket Source: <span class=column_identifier>{project.name} > {column.name}</span></div>')
                html.append(column.ticketsHTMLIncludingWrapperDivsAndMenus)
        print(f'Page HTML assembled')
        return ''.join(html)

    def __getDehydratedSourceProjects(self):
        return list(map(lambda projectJSON:
            Project(
                name = projectJSON['name'],
                columnNames = projectJSON['columns']
            ),
            DataStore.getConfigurationValue('sourceProjects')
        ))

    def __getDehydratedDestinationProject(self):
        if 'name' not in DataStore.getConfigurationValue('destinationProject').keys():
            return None
        if DataStore.getConfigurationValue('destinationProject')['name'] == None:
            return None
        return Project(
            name = DataStore.getConfigurationValue('destinationProject')['name'],
            columnNamesToIgnoreForButtons = DataStore.getConfigurationValue('destinationProject')['ignoreColumns']
        )

    def __load(self, hydrateTickets = True):
        self.sourceProjects = self.__getDehydratedSourceProjects()
        self.destinationProject = self.__getDehydratedDestinationProject()

        self.__setLoadingMessage('Beginning data retrieval')
        ProjectsHydrator(
            sourceProjects = self.sourceProjects,
            destinationProject = self.destinationProject,
            fetcher = self.fetcher,
            loadingMessageSetter = self.__setLoadingMessage
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
            projectNames = self.fetcher.fetchProjectNamesMatchingSearchTerm(searchTerm)
            projectSearchResultButtonsHTML = ''.join(map(lambda projectName: ButtonFactory(self.fetcher).projectSearchResultButtonHTML(projectName, mode), projectNames))
            self.__setInnerHTML(searchResultsSelector, projectSearchResultButtonsHTML)

    def expose(self, window):
        window.expose(self.reload) # expose to JS as 'pywebview.api.reload'
        window.expose(self.projectSearchTermEntered) # expose to JS as 'pywebview.api.projectSearchTermEntered'
