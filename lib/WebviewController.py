#!/usr/local/bin/python3

import Utilities, time, re
from string import Template
from ProjectsHydrator import ProjectsHydrator

class WebviewController:
    def __init__(self, webview, sourceProjects, destinationProject, fetcher):
        self.webview = webview
        self.fetcher = fetcher
        self.sourceProjects = sourceProjects
        self.destinationProject = destinationProject
        self.window = self.webview.create_window('Phabricator Quick Tag', html='Loading...', resizable=True, width=1280, height=1024, fullscreen=False)
        self.window.loaded += self.onDOMLoaded
        self.webview.start(self.expose, self.window, debug=True)

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

    def headerHTML(self):
        return f'''
            <div class=main_title>🏷 Quick Tag 🏷</div>
            <div class=main_subtitle>Quickly tag tickets from columns on various projects into any column on a destination project.</div>
        '''

    def projectSummaryHTML(self, name, columns):
        return f'''
            <div class=project_summary>
                <span class=project_summary_project>{name}</span> >
                {', '.join(list(map(lambda column: f'<span class=project_summary_column>{column.name}</span>', columns)))}
            </div>
        '''

    def summaryHTML(self):
        sourcesSummaryHTML = ''.join(map(lambda project: self.projectSummaryHTML(project.name, project.columns), self.sourceProjects))

        return f'''
            <div class=projects_summary>
                <div class=projects_summary_header>
                    <div class=projects_summary_title>
                        <b>⚙️ Current Configuration ⚙️</b>
                        <br>( adjust by editing 'configuration.json' file )
                    </div>
                </div>
                <div class=projects_summary_body>
                    <div class=projects_summary_body_buttons>
                        <button onclick="pywebview.api.reload()">Reload</button>
                    </div>
                    <div><b>Ticket Sources:</b></div>
                    {sourcesSummaryHTML}
                    <div><b>Destination Columns:</b></div>
                    {self.projectSummaryHTML(self.destinationProject.name, self.destinationProject.buttonsMenuColumns)}
                </div>
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
            {self.headerHTML()}
            {self.summaryHTML()}
            {self.projectsHTML()}
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
        self.load()

    def expose(self, window):
        window.expose(self.fetcher.fetchJSON) # expose to JS as 'pywebview.api.fetchJSON'
        window.expose(self.reload) # expose to JS as 'pywebview.api.reload'
