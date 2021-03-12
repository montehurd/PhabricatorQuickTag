#!/usr/local/bin/python3

import Utilities, time, re, json
from string import Template
from ProjectsHydrator import ProjectsHydrator
import webview, ButtonManifests
from ButtonMenuFactory import ButtonMenuFactory

class WebviewController:
    def __init__(self, webview, sourceProjects, destinationProject, fetcher):
        self.webview = webview
        self.fetcher = fetcher
        self.sourceProjects = sourceProjects
        self.destinationProject = destinationProject
        self.window = self.webview.create_window('PHABRICATOR QUICK TAG : Quickly tag tickets from columns on various projects into any column on a destination project', html='Loading...', resizable=True, width=1280, height=1024, fullscreen=False)
        self.window.loaded += self.onDOMLoaded
        self.webview.start(self.expose, self.window, debug=True)

    # Actions can hit endpoints, update button states, hide/show tickets, etc.
    def performClickedButtonActions(self, buttonID):
        clickedButtonManifest = ButtonManifests.allButtonManifests[buttonID]
        for action in clickedButtonManifest.clickActions:
            # if any action result is False execute the failure options and bail
            if action() == False:
                for failureAction in clickedButtonManifest.failureActions:
                    failureAction()
                return
        # if here all actions succeeded, so execute success actions
        for successAction in clickedButtonManifest.successActions:
            successAction()

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
        return f'''
                <div class=projects_summary_header>
                    <div class=projects_summary_title>
                        <b>⚙️&nbsp;&nbsp;Current Configuration</b>
                    </div>
                </div>
                <div class=projects_summary_body>
                    <div class=projects_summary_body_buttons>
                        <button onclick="pywebview.api.reload()">Reload</button>
                    </div>
                    <div><b>Ticket Sources:</b></div>
                    {sourcesHTML}
                    <div><b>Destination Columns:</b></div>
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

    def load(self):
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
        self.load()

    def expose(self, window):
        window.expose(self.reload) # expose to JS as 'pywebview.api.reload'
        window.expose(self.performClickedButtonActions) # expose to JS as 'pywebview.api.performClickedButtonActions'
