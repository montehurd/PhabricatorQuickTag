#!/usr/local/bin/python3

import Utilities, time, re, json, webview, ButtonManifests, DataStore
from string import Template
from ProjectsHydrator import ProjectsHydrator
from ButtonMenuFactory import ButtonMenuFactory
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

    def setMainDivInnerHTML(self, html):
        return self.setInnerHTML('div.phabricator-remarkup', html)

    def setLoadingMessage(self, message):
        return self.setInnerHTML('div.loading-message', message)

    def summaryHTML(self):
        sourcesHTML = ''.join(map(lambda project: ButtonMenuFactory(self.fetcher).toggleSourceProjectColumnInConfigurationButtonMenuHTML(project.name, project.buttonsMenuColumnNames, project.name), self.sourceProjects))
        destinationHTML = ButtonMenuFactory(self.fetcher).toggleDestinationProjectColumnInConfigurationButtonMenuHTML(self.destinationProject.name, self.destinationProject.buttonsMenuColumnNames)
        mouseOverAndOut = f''' onmouseover="this.classList.add('menu_highlighted');this.querySelectorAll('div.right_project_menu').forEach(e => e.style.visibility = 'visible');" onmouseout="this.classList.remove('menu_highlighted');this.querySelectorAll('div.right_project_menu').forEach(e => e.style.visibility = 'hidden');"'''
        return f'''
                <div class=projects_summary_header>
                    <div class=projects_summary_title>
                        <b>⚙️&nbsp;&nbsp;Current Configuration</b>
                        <div class=projects_summary_body_buttons>
                            <button onclick="pywebview.api.reload()">Reload</button>
                        </div>
                    </div>
                </div>
                <div class=projects_summary_body>
                    <div class=project_summary_heading {mouseOverAndOut}>
                        <div class=right_project_menu>
                            <button class=add>Add</button>
                        </div>
                        <b>Ticket Sources:</b>
                    </div>
                    {sourcesHTML}
                    <div class=project_summary_heading {mouseOverAndOut}>
                        <div class=right_project_menu>
                            <button class=add>Change</button>
                        </div>
                        <b>Destination Columns:</b>
                    </div>
                    {destinationHTML}
                </div>
        '''

    def projectsHTML(self):
        print(f'Fetching complete')
        print(f'Processing hydrated object graph')
        html = []
        for project in self.sourceProjects:
            for column in project.columns:
                html.append(f'<div class=column_source>Ticket Source: <span class=column_identifier>{project.name} > {column.name}</span></div>')
                html.append(column.ticketsHTMLIncludingWrapperDivsAndMenus)
        print(f'Page HTML assembled')
        return ''.join(html)

    def mainDivInnerHTMLForProjects(self):
        return f'''
            <div class=projects_summary>
                {self.summaryHTML()}
            </div>
            <div class=projects_tickets>
                {self.projectsHTML()}
            </div>
        '''

    def getDehydratedSourceProjects(self):
        return list(map(lambda projectJSON:
            Project(
                name = projectJSON['name'],
                columnNames = projectJSON['columns'],
                fetcher = self.fetcher
            ),
            DataStore.getConfigurationValue('sourceProjects')
        ))

    def getDehydratedDestinationProject(self):
        return Project(
            name = DataStore.getConfigurationValue('destinationProject')['name'],
            columnNamesToIgnoreForButtons = DataStore.getConfigurationValue('destinationProject')['ignoreColumns'],
            fetcher = self.fetcher
        )

    def load(self):
        self.sourceProjects = self.getDehydratedSourceProjects()
        self.destinationProject = self.getDehydratedDestinationProject()
        self.window.load_html(self.getWrapperHTML())
        time.sleep(1.0)

        self.setLoadingMessage('Beginning data retrieval')
        Utilities.callAsyncFuncSynchronously(
            ProjectsHydrator(
                sourceProjects = self.sourceProjects,
                destinationProject = self.destinationProject,
                fetcher = self.fetcher,
                loadingMessageSetter = self.setLoadingMessage
            ).hydrateProjects()
        )

        # can start inner html generation now that projects are hydrated
        mainDivInnerHTML = self.mainDivInnerHTMLForProjects()

        self.setLoadingMessage('')
        self.setMainDivInnerHTML(mainDivInnerHTML)

    def onDOMLoaded(self):
        self.window.loaded -= self.onDOMLoaded # unsubscribe event listener
        self.load()

    def reload(self):
        ButtonManifests.clear()
        DataStore.loadConfiguration()
        self.load()

    def expose(self, window):
        window.expose(self.reload) # expose to JS as 'pywebview.api.reload'
