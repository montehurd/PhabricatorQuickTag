#!/usr/local/bin/python3

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from Column import Column
from ButtonMenuFactory import ButtonMenuFactory
import json

class ProjectsHydrator:
    def __init__(self, sourceProjects, destinationProject, fetcher = None, loadingMessageSetter = None):
        self.sourceProjects = sourceProjects
        self.destinationProject = destinationProject
        self.statusesData = []
        self.prioritiesData = []
        self.fetcher = fetcher
        self.loadingMessageSetter = loadingMessageSetter

    async def hydrateProjects(self):
        with ThreadPoolExecutor(max_workers=10) as executor:
            # fetch destination project phid and columns

            self.loadingMessageSetter(f"Fetching '{self.destinationProject.name}' id")

            executor.submit(self.destinationProject.fetchPHID(), ())
            self.loadingMessageSetter(f"Fetching '{self.destinationProject.name}' columns")
            executor.submit(self.destinationProject.fetchButtonsMenuColumns(), ())

            addToDestinationColumnMenuHTMLLambdas = []
            destinationColumns = list(filter(lambda column: (column.name not in self.destinationProject.columnNamesToIgnoreForButtons), self.destinationProject.buttonsMenuColumns))
            if len(destinationColumns) > 0:
                addToDestinationColumnMenuHTMLLambdas.append(
                    lambda ticketID, ticketJSON, columns=destinationColumns :
                        ButtonMenuFactory(self.fetcher).ticketAddToColumnButtonMenuHTML(f'Add to column on destination project ( <i>{self.destinationProject.name}</i> )', ticketID, ticketJSON, columns)
                )

            statusAndPriorityMenuHTMLLambda = [
                lambda ticketID, ticketJSON :
                    f'''
                        {ButtonMenuFactory(self.fetcher).ticketStatusButtonMenuHTML('Status', ticketID, ticketJSON)}
                        {ButtonMenuFactory(self.fetcher).ticketPriorityButtonMenuHTML('Priority', ticketID, ticketJSON)}
                    '''
            ]

            for project in self.sourceProjects:
                # fetch project phids
                self.loadingMessageSetter(f"Fetching '{project.name}' id")
                executor.submit(project.fetchPHID(), ())

                # fetch source project columns
                self.loadingMessageSetter(f"Fetching '{project.name}' columns")
                executor.submit(project.fetchButtonsMenuColumns(), ())

                # make column object for each column name
                project.columns = []
                for columnName in project.columnNames:
                    project.columns.append( Column(name = columnName, project = project, phid = None, fetcher = self.fetcher) )
                # fetch column phids
                for column in project.columns:
                    self.loadingMessageSetter(f"Fetching '{project.name} > {column.name}' id")
                    executor.submit(column.fetchPHID(), ())
                # fetch column tickets
                for column in project.columns:
                    self.loadingMessageSetter(f"Fetching '{project.name} > {column.name}' tickets")
                    executor.submit(column.fetchTickets(self.destinationProject.phid), ())

                currentSourceColumnMenuHTMLLambda = [
                    lambda ticketID, ticketJSON, columns=project.buttonsMenuColumns :
                        ButtonMenuFactory(self.fetcher).ticketAddToColumnButtonMenuHTML(f'Current column on source project ( <i>{project.name}</i> )', ticketID, ticketJSON, columns)
                ]

                # safe to append all menu lambdas to column here:
                for column in project.columns:
                    column.menuHTMLLambdas = currentSourceColumnMenuHTMLLambda + column.menuHTMLLambdas + addToDestinationColumnMenuHTMLLambdas + statusAndPriorityMenuHTMLLambda

                # fetch column tickets html for their remarkup
                for column in project.columns:
                    self.loadingMessageSetter(f"Fetching '{project.name} > {column.name}' tickets html")
                    executor.submit(column.fetchTicketsHTML(self.destinationProject.name), ())

            # print(f'{len(self.sourceProjects[1].columns[0].tickets)}')

            # using 'with' so 'executor.shutdown' not needed: https://stackoverflow.com/a/63683485
            # executor.shutdown(wait=True)
