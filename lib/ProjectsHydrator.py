#!/usr/local/bin/python3

from Column import Column

class ProjectsHydrator:
    def __init__(self, sourceProjects, destinationProject = None, fetcher = None, loadingMessageSetter = None, ticketAddToColumnButtonMenuHTMLFunction = None, ticketStatusButtonMenuHTMLFunction = None, ticketPriorityButtonMenuHTMLFunction = None):
        self.sourceProjects = sourceProjects
        self.destinationProject = destinationProject
        self.fetcher = fetcher
        self.loadingMessageSetter = loadingMessageSetter
        self.ticketAddToColumnButtonMenuHTMLFunction = ticketAddToColumnButtonMenuHTMLFunction
        self.ticketStatusButtonMenuHTMLFunction = ticketStatusButtonMenuHTMLFunction
        self.ticketPriorityButtonMenuHTMLFunction = ticketPriorityButtonMenuHTMLFunction

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

    def hydrateProjects(self, hydrateTickets = True):
        # fetch destination project names and columns

        # hydrate source and destination project and column names from configuration.json phids
        self.loadingMessageSetter('Fetching project and column names')
        openItemNamesByPHID = self.fetcher.fetchNamesForStatusOpenPHIDs(self.__allProjectPHIDs() + self.__allColumnPHIDs())

        for sourceProject in self.sourceProjects:
            sourceProject.name = openItemNamesByPHID[sourceProject.phid]
        if self.destinationProject != None:
            self.destinationProject.name = openItemNamesByPHID[self.destinationProject.phid]

        addToDestinationColumnMenuHTMLLambdas = []

        if self.destinationProject != None:
            self.loadingMessageSetter(f"Fetching '{self.destinationProject.name}' columns")
            self.destinationProject.buttonsMenuColumns = self.__fetchColumns(self.destinationProject)

            destinationColumns = list(filter(lambda column: (column.phid not in self.destinationProject.columnPHIDsToIgnoreForButtons), self.destinationProject.buttonsMenuColumns))
            if len(destinationColumns) > 0:
                addToDestinationColumnMenuHTMLLambdas.append(
                    lambda ticketID, ticketJSON, columns=destinationColumns :
                        self.ticketAddToColumnButtonMenuHTMLFunction(f'Add to column on destination project ( <i>{self.destinationProject.name}</i> )', ticketID, ticketJSON, columns)
                )

        statusAndPriorityMenuHTMLLambda = [
            lambda ticketID, ticketJSON :
                f'''
                    {self.ticketStatusButtonMenuHTMLFunction('Status', ticketID, ticketJSON)}
                    {self.ticketPriorityButtonMenuHTMLFunction('Priority', ticketID, ticketJSON)}
                '''
        ]

        for project in self.sourceProjects:
            # fetch source project columns
            self.loadingMessageSetter(f"Fetching '{project.name}' columns")
            project.buttonsMenuColumns = self.__fetchColumns(project)

            currentSourceColumnMenuHTMLLambda = [
                lambda ticketID, ticketJSON, columns=project.buttonsMenuColumns :
                    self.ticketAddToColumnButtonMenuHTMLFunction(f'Current column on source project ( <i>{project.name}</i> )', ticketID, ticketJSON, columns)
            ]

            # make column object for each column name
            project.columns = list(map(lambda columnPHID: Column(name = openItemNamesByPHID[columnPHID], project = project, phid = columnPHID), project.columnPHIDs))

            for column in project.columns:
                self.loadingMessageSetter(f"Fetching '{project.name} > {column.name}' tickets")
                if not hydrateTickets: # if only reloading the configuration UI the ticket hydration below is not needed
                    continue
                tickets = list(self.fetcher.fetchColumnTickets(column.phid))
                # dict with ticketID as key and ticketJSON as value (excluding tickets already tagged with destinationProjectPHID)
                ticketsByID = dict((x['id'], x) for x in tickets if self.destinationProject == None or not self.destinationProject.phid in x['attachments']['projects']['projectPHIDs'])
                column.ticketsByID = ticketsByID
                # print(json.dumps(self.ticketsByID, indent=4))
                column.tickets = column.ticketsByID.values()
                column.menuHTMLLambdas = currentSourceColumnMenuHTMLLambda + column.menuHTMLLambdas + addToDestinationColumnMenuHTMLLambdas + statusAndPriorityMenuHTMLLambda
                # fetch column tickets html for their remarkup
                self.loadingMessageSetter(f"Fetching '{project.name} > {column.name}' tickets html")
                column.ticketsHTMLByID = self.fetcher.fetchTicketsHTMLByID(column.tickets)
