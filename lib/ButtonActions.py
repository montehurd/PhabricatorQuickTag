#!/usr/local/bin/python3

import json, urllib.parse, urllib.request, webview, re, Utilities, DataStore

class ButtonActions:
    def __init__(self, fetcher):
        self.fetcher = fetcher

    def __window(self):
        return webview.windows[0]

    def __getComment(self, ticketID):
        numericID = re.sub("[^0-9]", "", ticketID)
        comment = self.__window().evaluate_js(f'''document.querySelector("textarea#ticketID{numericID}").value;''')
        return comment if len(comment.strip()) else None

    def setComment(self, ticketID, comment):
        numericID = re.sub("[^0-9]", "", ticketID)
        returnedComment = self.__window().evaluate_js(f'''document.querySelector("textarea#ticketID{numericID}").value = "{comment}"''')
        return returnedComment == comment

    def setTicketActionMessage(self, ticketID, message):
        numericID = re.sub("[^0-9]", "", ticketID)
        self.__window().evaluate_js(f'''
            const span = document.querySelector("span#buttonActionMessage{numericID}")
            span.innerHTML = "{message}"
            setTimeout(() => {{ span.innerHTML = "" }}, 1500);
        ''')
        return True

    def showTicketFailure(self, ticketID):
        return self.setTicketActionMessage(ticketID, '💩 Failure')

    def showTicketSuccess(self, ticketID):
        return self.setTicketActionMessage(ticketID, '🎉 Success')

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

    def hideTickets(self):
        self.__window().evaluate_js("document.querySelector('div.projects_tickets').style.visibility = 'hidden';")

    def showTickets(self):
        self.__window().evaluate_js('document.querySelector("div.projects_tickets").style.visibility = "visible"')

    def selectButton(self, buttonID):
        self.__window().evaluate_js(f'document.querySelector("button#{buttonID}").classList.add("selected")')

    def deselectButton(self, buttonID):
        self.__window().evaluate_js(f'document.querySelector("button#{buttonID}").classList.remove("selected")')

    def showProjectSearch(self, mode, hideButtonHTML, title):
        self.__window().evaluate_js(f"""
            document.querySelectorAll('div.blurry_overlay, div.projects_search_centered_panel').forEach(e => {{e.style.display = 'block'}});
            document.querySelector("div.projects_search_hide_container").innerHTML = `{hideButtonHTML}`;
            document.querySelector("div.projects_search_title").innerHTML = `{title}`;
            document.querySelector("input#projects_search_mode").value = `{mode}`;
        """)
        return True

    def hideProjectSearch(self):
        self.__window().evaluate_js(f"document.querySelectorAll('div.blurry_overlay, div.projects_search_centered_panel').forEach(e => {{e.style.display = 'none'}});")
        return True

    def saveProjectSearchChoice(self, projectName, mode):
        if mode == 'destination':
            DataStore.saveDestinationProject(projectName)
        elif mode == 'source':
            DataStore.saveSourceProject(projectName)
        else:
            print(f'Unhandled mode: "{mode}"')
            return False
        return True

    def toggleButton(self, buttonID):
        # print(f'''document.querySelector("button#{buttonID}").classList.contains("selected")''')
        self.__window().evaluate_js(f'''
            if (document.querySelector("button#{buttonID}").classList.contains("selected")) {{
                document.querySelector("button#{buttonID}").classList.remove("selected")
            }} else {{
                document.querySelector("button#{buttonID}").classList.add("selected")
            }}
        ''')

    def isButtonSelected(self, buttonID):
        return self.__window().evaluate_js(f'document.querySelector("button#{buttonID}").classList.contains("selected")')

    def deselectOtherButtonsInMenu(self, buttonID):
        self.__window().evaluate_js(f'''
            var thisButton = document.querySelector("button#{buttonID}");
            var menu = thisButton.closest('buttonmenu');
            if (thisButton.parentElement != menu) {{
                alert("Closest 'buttonmenu' tag is not button tag's parent");
            }}
            menu.querySelectorAll("button").forEach(button => {{
                if (button.id == thisButton.id) return;
                button.classList.remove('selected');
            }})
        ''')

    def deleteMenu(self, buttonID):
        self.__window().evaluate_js(f'''
            var thisButton = document.querySelector("button#{buttonID}");
            var menuDiv = thisButton.closest('div.menu');
            menuDiv.remove()
        ''')

    def reload(self):
        self.__window().evaluate_js('pywebview.api.reload();')

    def reloadConfigurationUI(self):
        self.__window().evaluate_js('pywebview.api.reload(false);')

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

    def toggleSourceProjectColumnInConfigurationJSON(self, allColumnNames, indexOfColumnToToggle, projectName):
        columnName = allColumnNames[indexOfColumnToToggle]
        sourceProjects = DataStore.getConfigurationValue('sourceProjects')
        project = next(project for project in sourceProjects if project['name'] == projectName)
        if DataStore.isSourceProjectColumnPresentInConfigurationJSON(columnName, projectName):
            project['columns'].remove(columnName)
        else:
            project['columns'].insert(indexOfColumnToToggle, columnName)
        DataStore.saveCurrentConfiguration()
        return True

    def toggleDestinationProjectColumnInConfigurationJSON(self, allColumnNames, indexOfColumnToToggle):
        columnName = allColumnNames[indexOfColumnToToggle]
        project = DataStore.getConfigurationValue('destinationProject')
        if DataStore.isDestinationProjectIgnoreColumnPresentInConfigurationJSON(columnName):
            project['ignoreColumns'].remove(columnName)
        else:
            project['ignoreColumns'].insert(indexOfColumnToToggle, columnName)
        DataStore.saveCurrentConfiguration()
        return True

    def removeSourceProjectFromConfigurationJSON(self, projectName):
        sourceProjects = DataStore.getConfigurationValue('sourceProjects')
        project = next(project for project in sourceProjects if project['name'] == projectName)
        sourceProjects.remove(project)
        DataStore.saveCurrentConfiguration()
        DataStore.loadConfiguration()
        return True

    def removeDestinationProjectFromConfigurationJSON(self):
        destinationProject = DataStore.getConfigurationValue('destinationProject')
        destinationProject['name'] = None
        destinationProject['ignoreColumns'] = []
        DataStore.saveCurrentConfiguration()
        DataStore.loadConfiguration()
        return True

    def toggleTicketOnProjectColumn(self, ticketID, projectPHID, columnPHID, buttonID):
        if self.isButtonSelected(buttonID):
            if not self.removeTicketFromProject(ticketID, projectPHID):
                return False
        else:
            if not self.addTicketToProject(ticketID, projectPHID):
                return False
            if not self.addTicketToColumn(ticketID, columnPHID):
                return False
        return True
