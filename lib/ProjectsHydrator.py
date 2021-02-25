#!/usr/local/bin/python3

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from Button import Button
from Menu import Menu
from ClickEndpoint import ClickEndpoint
from Column import Column

def statusButtonStateChecker(endpoint, ticketJSON, value):
    return ticketJSON['fields']['status']['name'] == value

def priorityButtonStateChecker(endpoint, ticketJSON, value):
    return ticketJSON['fields']['priority']['name'] == value

def currentColumnButtonStateChecker(endpoint, ticketJSON, value):
    boards = ticketJSON['attachments']['columns']['boards']
    arrayOfColumnPHIDArrays = map(lambda board:
        map(lambda column: column['phid'], board['columns']),
        boards.values()
    )
    arrayOfColumnPHIDs = [item for sublist in arrayOfColumnPHIDArrays for item in sublist]
    buttonColumnPHID = endpoint.value[0]
    return buttonColumnPHID in arrayOfColumnPHIDs

class ProjectsHydrator:
    def __init__(self, sourceProjects, destinationProject, fetcher = None, loadingMessageSetter = None):
        self.sourceProjects = sourceProjects
        self.destinationProject = destinationProject
        self.statusesData = []
        self.prioritiesData = []
        self.fetcher = fetcher
        self.loadingMessageSetter = loadingMessageSetter

    def addToDestinationProjectColumnMenu(self):
        # every column button will need to first call 'projects.add'
        addProjectEndpoint = ClickEndpoint(
            name = 'maniphest.edit',
            key = 'projects.add',
            value = [self.destinationProject.phid],
            stateCheckerLambda = None
        )
        addColumnButtons = list(map(lambda column: Button(title = column.name, clickEndpoints = [addProjectEndpoint, ClickEndpoint(name = 'maniphest.edit', key = 'column', value = [column.phid], stateCheckerLambda = None)], stateEndpointIndex = 1), self.destinationProject.buttonsMenuColumns))
        return Menu(
            id = 'destination',
            title = f'Add to column on destination project ( <i>{self.destinationProject.name}</i> )',
            buttons = addColumnButtons
        )

    def fetchPriorities(self):
        self.prioritiesData = self.fetcher.fetchPriorities()

    def fetchStatuses(self):
        self.statusesData = self.fetcher.fetchStatuses()

    def moveToSourceProjectColumnMenu(self, project):
        moveToColumnButtons = list(map(lambda column: Button(title = column.name, clickEndpoints = [ClickEndpoint(name = 'maniphest.edit', key = 'column', value = [column.phid], stateCheckerLambda = currentColumnButtonStateChecker)], stateEndpointIndex = 0), project.buttonsMenuColumns))
        return Menu(
            id = 'source',
            title = f'Current column on source project ( <i>{project.name}</i> )',
            buttons = moveToColumnButtons
        )

    async def hydrateProjects(self):
        with ThreadPoolExecutor(max_workers=10) as executor:
            # fetch destination project phid and columns

            self.loadingMessageSetter(f"Fetching '{self.destinationProject.name}' id")

            executor.submit(self.fetchPriorities(), ())
            prioritiesMenu = Menu(
                id = 'priority',
                title = 'Priority',
                buttons = list(map(lambda priority: Button(title = priority['name'], clickEndpoints = [ClickEndpoint(name = 'maniphest.edit', key = 'priority', value = priority['keywords'][0], stateCheckerLambda = priorityButtonStateChecker)]), self.prioritiesData))
            )
            executor.submit(self.fetchStatuses(), ())
            statusesMenu = Menu(
                id = 'status',
                title = 'Status',
                buttons = list(map(lambda priority: Button(title = priority['name'], clickEndpoints = [ClickEndpoint(name = 'maniphest.edit', key = 'status', value = priority['value'], stateCheckerLambda = statusButtonStateChecker)]), self.statusesData))
            )

            executor.submit(self.destinationProject.fetchPHID(), ())
            self.loadingMessageSetter(f"Fetching '{self.destinationProject.name}' columns")
            executor.submit(self.destinationProject.fetchButtonsMenuColumns(), ())

            addToDestinationProjectColumnMenu = self.addToDestinationProjectColumnMenu()

            for project in self.sourceProjects:
                # fetch project phids
                self.loadingMessageSetter(f"Fetching '{project.name}' id")
                executor.submit(project.fetchPHID(), ())

                # fetch source project columns
                self.loadingMessageSetter(f"Fetching '{project.name}' columns")
                executor.submit(project.fetchButtonsMenuColumns(), ())

                # determine menus
                menus = []
                if len(project.buttonsMenuColumns) > 0:
                    menus.append(self.moveToSourceProjectColumnMenu(project))
                if len(self.destinationProject.buttonsMenuColumns) > 0:
                    menus.append(addToDestinationProjectColumnMenu)
                menus.append(statusesMenu)
                menus.append(prioritiesMenu)

                # make column object for each column name
                project.columns = []
                for columnName in project.columnNames:
                    # def __init__(self, name, project, phid=None, menus=[]):
                    project.columns.append( Column(name = columnName, project = project, phid = None, menus = menus, fetcher = self.fetcher) )
                # fetch column phids
                for column in project.columns:
                    self.loadingMessageSetter(f"Fetching '{project.name} > {column.name}' id")
                    executor.submit(column.fetchPHID(), ())
                # fetch column tickets
                for column in project.columns:
                    self.loadingMessageSetter(f"Fetching '{project.name} > {column.name}' tickets")
                    executor.submit(column.fetchTickets(self.destinationProject.phid), ())
                    # fetch column tickets remarkup
                    self.loadingMessageSetter(f"Fetching '{project.name} > {column.name}' tickets html")
                    executor.submit(column.fetchTicketsHTML(self.destinationProject.name), ())

            # print(f'{len(self.sourceProjects[1].columns[0].tickets)}')

            # using 'with' so 'executor.shutdown' not needed: https://stackoverflow.com/a/63683485
            # executor.shutdown(wait=True)
