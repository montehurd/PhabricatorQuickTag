#!/usr/local/bin/python3

from Column import Column
from ButtonFactory import ButtonFactory

class ProjectsHydrator:
    def __init__(self, sourceProjects, destinationProject, fetcher = None, loadingMessageSetter = None):
        self.sourceProjects = sourceProjects
        self.destinationProject = destinationProject
        self.statusesData = []
        self.prioritiesData = []
        self.fetcher = fetcher
        self.loadingMessageSetter = loadingMessageSetter

    def fetchColumns(self, project):
        columnsData = self.fetcher.fetchColumnsData(project)
        return list(map(lambda x: Column(x['fields']['name'], project, x['phid']), columnsData))

    def hydrateProjects(self, hydrateTickets = True):
        # fetch destination project phid and columns

        self.loadingMessageSetter(f"Fetching '{self.destinationProject.name}' id")
        self.destinationProject.phid = self.fetcher.fetchProjectPHID(self.destinationProject.name)

        self.loadingMessageSetter(f"Fetching '{self.destinationProject.name}' columns")
        self.destinationProject.buttonsMenuColumns = self.fetchColumns(self.destinationProject)
        self.destinationProject.buttonsMenuColumnNames = list(map(lambda column: column.name, self.destinationProject.buttonsMenuColumns))

        addToDestinationColumnMenuHTMLLambdas = []
        destinationColumns = list(filter(lambda column: (column.name not in self.destinationProject.columnNamesToIgnoreForButtons), self.destinationProject.buttonsMenuColumns))
        if len(destinationColumns) > 0:
            addToDestinationColumnMenuHTMLLambdas.append(
                lambda ticketID, ticketJSON, columns=destinationColumns :
                    ButtonFactory(self.fetcher).ticketAddToColumnButtonMenuHTML(f'Add to column on destination project ( <i>{self.destinationProject.name}</i> )', ticketID, ticketJSON, columns)
            )

        statusAndPriorityMenuHTMLLambda = [
            lambda ticketID, ticketJSON :
                f'''
                    {ButtonFactory(self.fetcher).ticketStatusButtonMenuHTML('Status', ticketID, ticketJSON)}
                    {ButtonFactory(self.fetcher).ticketPriorityButtonMenuHTML('Priority', ticketID, ticketJSON)}
                '''
        ]

        for project in self.sourceProjects:
            # fetch project phids
            self.loadingMessageSetter(f"Fetching '{project.name}' id")
            project.phid = self.fetcher.fetchProjectPHID(project.name)

            # fetch source project columns
            self.loadingMessageSetter(f"Fetching '{project.name}' columns")
            project.buttonsMenuColumns = self.fetchColumns(project)
            project.buttonsMenuColumnNames = list(map(lambda column: column.name, project.buttonsMenuColumns))

            currentSourceColumnMenuHTMLLambda = [
                lambda ticketID, ticketJSON, columns=project.buttonsMenuColumns :
                    ButtonFactory(self.fetcher).ticketAddToColumnButtonMenuHTML(f'Current column on source project ( <i>{project.name}</i> )', ticketID, ticketJSON, columns)
            ]

            # make column object for each column name
            project.columns = list(map(lambda columnName: Column(name = columnName, project = project, phid = None, fetcher = self.fetcher), project.columnNames))

            for column in project.columns:
                self.loadingMessageSetter(f"Fetching '{project.name} > {column.name}' id")
                column.phid = self.fetcher.fetchColumnPHID(column.name, column.project.phid)
                self.loadingMessageSetter(f"Fetching '{project.name} > {column.name}' tickets")
                if not hydrateTickets: # if only reloading the configuration UI the ticket hydration below is not needed
                    continue
                tickets = list(self.fetcher.fetchColumnTickets(column.phid))
                # dict with ticketID as key and ticketJSON as value (excluding tickets already tagged with destinationProjectPHID)
                ticketsByID = dict((x['id'], x) for x in tickets if not self.destinationProject.phid in x['attachments']['projects']['projectPHIDs'])
                column.ticketsByID = ticketsByID
                # print(json.dumps(self.ticketsByID, indent=4))
                column.tickets = column.ticketsByID.values()
                column.menuHTMLLambdas = currentSourceColumnMenuHTMLLambda + column.menuHTMLLambdas + addToDestinationColumnMenuHTMLLambdas + statusAndPriorityMenuHTMLLambda
                # fetch column tickets html for their remarkup
                self.loadingMessageSetter(f"Fetching '{project.name} > {column.name}' tickets html")
                column.fetchTicketsHTML(self.destinationProject.name)
