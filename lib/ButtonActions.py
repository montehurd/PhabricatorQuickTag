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
        self.__window().evaluate_js('document.querySelector("div.projects_tickets").style.visibility = "hidden"')

    def showTickets(self):
        self.__window().evaluate_js('document.querySelector("div.projects_tickets").style.visibility = "visible"')

    def selectButton(self, buttonID):
        self.__window().evaluate_js(f'document.querySelector("button#{buttonID}").classList.add("selected")')

    def deselectButton(self, buttonID):
        self.__window().evaluate_js(f'document.querySelector("button#{buttonID}").classList.remove("selected")')

    def toggleButton(self, buttonID):
        # print(f'''document.querySelector("button#{buttonID}").classList.contains("selected")''')
        self.__window().evaluate_js(f'''
            if (document.querySelector("button#{buttonID}").classList.contains("selected")) {{
                document.querySelector("button#{buttonID}").classList.remove("selected")
            }} else {{
                document.querySelector("button#{buttonID}").classList.add("selected")
            }}
        ''')

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

    def addTicketToProject(self, ticketID, projectPHID):
        return self.fetcher.callEndpoint(
            path = '/api/maniphest.edit',
            key = 'projects.add',
            value = projectPHID,
            objectIdentifier = ticketID,
            comment = None,
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
        DataStore.toggleSourceProjectColumnInConfigurationJSON(columnName, indexOfColumnToToggle, projectName)
        DataStore.saveCurrentConfiguration()
        return True
