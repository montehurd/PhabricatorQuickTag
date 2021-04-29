#!/usr/local/bin/python3

import json, urllib.parse, urllib.request

class Fetcher:
    def __init__(self, baseURL, apiToken):
        self.baseURL = baseURL
        self.apiToken = apiToken

    def fetchJSON(self, filePath, values):
        data = urllib.parse.urlencode(values)
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
        }
        request = urllib.request.Request(url = f'{self.baseURL}{filePath}', headers = headers, data = data.encode('utf-8'), method='POST')
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.URLError as e:
            print(e)

        pageJSON = json.loads(response.read().decode('utf-8'))

        if pageJSON.get('error_code') != None:
            print(f'\nfetchJSON Error:\n\t{pageJSON}\n')

        return pageJSON

    def fetchNamesForStatusOpenPHIDs(self, phids):
        namesAndStatusesByPHID = self.fetchNamesAndStatusesForPHIDs(phids)
        if len(namesAndStatusesByPHID) == 0:
            return {}
        return {key: value['name'] for key, value in namesAndStatusesByPHID.items() if value['status'] == 'open'}

    # project.search does not currently return status, so have to do separate fetch, unfortunately, to see if projects are still open.
    # same is true for columns. 'phid.query' is also needed to get the full project name from the phid unfortunately.
    def fetchNamesAndStatusesForPHIDs(self, phids):
        if len(phids) == 0:
            return []
        values = {
            'api.token' : self.apiToken
        }
        for index, phid in enumerate(phids):
            values[f'phids[{index}]'] = phid
        result = self.fetchJSON('/api/phid.query', values)['result']
        output = {}
        for item in result.values():
            output[item['phid']] = {'name': item['name'], 'status': item['status']}
        return output

    def fetchProjectsMatchingSearchTerm(self, searchTerm):
        result = self.fetchJSON('/api/project.search', {
            'api.token' : self.apiToken,
            'constraints[query]' : f'title:"{searchTerm}"'
        })
        if result['result'] == None:
            return []
        projectPHIDs = list(map(lambda projectJSON: projectJSON['phid'], result['result']['data']))
        openProjects = self.fetchNamesForStatusOpenPHIDs(projectPHIDs)
        return openProjects

    def fetchProjectsIcons(self, projectPHIDs):
        if len(projectPHIDs) == 0:
            return []
        values = {
            'api.token' : self.apiToken
        }
        for index, phid in enumerate(projectPHIDs):
            values[f'constraints[phids][{index}]'] = phid
        result = self.fetchJSON('/api/project.search', values)
        if result['result'] == None or result['result']['data'] == None:
            return {}
        return { project['phid']:project['fields']['icon'] for project in result['result']['data'] }

    def fetchColumnTickets(self, columnPHID):
        result = self.fetchJSON('/api/maniphest.search', {
            'api.token' : self.apiToken,
            'constraints[columnPHIDs][0]' : columnPHID,
            'constraints[statuses][0]' : 'open',
            'attachments[projects]' : 'true',
            'attachments[columns]' : 'true'
        })
        return filter(lambda x: x['type'] == 'TASK', result['result']['data'])

    def fetchProjectTickets(self, projectPHID):
        result = self.fetchJSON('/api/maniphest.search', {
            'api.token' : self.apiToken,
            'constraints[projects][0]' : projectPHID,
            'constraints[statuses][0]' : 'open',
            'attachments[projects]' : 'true',
            'attachments[columns]' : 'true'
        })
        return filter(lambda x: x['type'] == 'TASK', result['result']['data'])

    def __fetchHTMLFromColumnTicketsRemarkup(self, ticketsRemarkup):
        if len(ticketsRemarkup) == 0:
            return []
        values = {
            'api.token' : self.apiToken,
            'context' : 'phriction' # use 'maniphest' ???
        }
        for index, remarkup in enumerate(ticketsRemarkup):
            values[f'contents[{index}]'] = remarkup
        result = self.fetchJSON('/api/remarkup.process', values)['result']
        htmlArray = list(map(lambda item: item['content'].strip(), result))
        return htmlArray

    def fetchColumnsData(self, projectPHID):
        result = self.fetchJSON('/api/project.column.search', {
            'api.token' : self.apiToken,
            'order[0]': '-id',
            'constraints[projects][0]' : projectPHID
            })
        columnsData = list(filter(lambda x: x['type'] == 'PCOL', result['result']['data']))
        columnPHIDs = list(map(lambda column: column['phid'], columnsData))
        if len(columnPHIDs) == 0:
            return []
        openColumnPHIDs = self.fetchNamesForStatusOpenPHIDs(columnPHIDs)
        openColumnsData = filter(lambda column: column['phid'] in openColumnPHIDs, columnsData)
        return openColumnsData

    def fetchPriorities(self):
        result = self.fetchJSON('/api/maniphest.priority.search', {
            'api.token' : self.apiToken
        })
        return result['result']['data']

    def fetchStatuses(self):
        result = self.fetchJSON('/api/maniphest.status.search', {
            'api.token' : self.apiToken
        })
        return result['result']['data']

    def fetchHTML(self, fileName):
        headers = {
            'Content-Type': 'text/html; charset=utf-8',
            'Accept': 'text/html',
        }
        request = urllib.request.Request(url = f'{self.baseURL}{fileName}', headers = headers, method='GET')
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.URLError as e:
            print(e)
        page = response.read()
        return page.decode('utf-8')

    # hit endpoint returning boolean result
    def __callEndpoint(self, path, key, value, objectIdentifier, comment = None, needsValueArgumentInArray = False):
        values = {
            'api.token': self.apiToken,
            'transactions[0][type]': key,
            f'''transactions[0][value]{'[0]' if needsValueArgumentInArray else ''}''': value,
            'objectIdentifier': objectIdentifier,
            'output': 'json'
        }
        if comment != None:
            values['transactions[1][type]'] = 'comment'
            values['transactions[1][value]'] = comment

        data = urllib.parse.urlencode(values)
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
        }
        request = urllib.request.Request(url = f'{self.baseURL}{path}', headers = headers, data = data.encode('utf-8'), method='POST')

        try:
            response = urllib.request.urlopen(request)
        except urllib.error.URLError as e:
            return False
        else:
            pageJSON = json.loads(response.read().decode('utf-8'))
            if pageJSON.get('error_code') != None:
                print(f'\ncallEndpoint Error:\n\t{pageJSON}\n')
                return False
            return True

        # try:
        #     response = urllib.request.urlopen(request)
        # except urllib.error.URLError as e:
        #     print(e)
        #
        # pageJSON = json.loads(response.read().decode('utf-8'))
        #
        # if pageJSON.get('error_code') != None:
        #     raise Exception(f'\nfetchJSON Error:\n\t{pageJSON}\n')
        #
        # return pageJSON

    def __ticketRemarkupForTicketJSON(self, ticket):
        return f'''
= T{ticket['id']} =
== {ticket['fields']['name']} ==

{ticket['fields']['description']['raw']}
'''

    def fetchTicketsHTMLByID(self, tickets):
        ticketsRemarkupArray = list(map(lambda ticket: self.__ticketRemarkupForTicketJSON(ticket), tickets))
        ticketsHTMLArray = self.__fetchHTMLFromColumnTicketsRemarkup(ticketsRemarkupArray)
        ticketIDs = list(map(lambda ticket: ticket['id'], tickets))
        if len(ticketIDs) != len(ticketsHTMLArray):
            print('Did not receive expected number of ticket html values')
            return {}
        ticketsHTMLByID = {}
        for i, ticketID in enumerate(ticketIDs):
            ticketsHTMLByID[f'{ticketID}'] = ticketsHTMLArray[i]
        return ticketsHTMLByID

    def fetchUserNamesForUserPHIDs(self, userPHIDs):
        if len(userPHIDs) == 0:
            return []
        values = {
            'api.token' : self.apiToken
        }
        for index, phid in enumerate(userPHIDs):
            values[f'constraints[phids][{index}]'] = phid
        results = self.fetchJSON('/api/user.search', values)['result']['data']
        output = {}
        for item in results:
            output[item['phid']] = item['fields']['username']
        return output
    
    def addTicketToProject(self, ticketID, projectPHID):
        return self.__callEndpoint(
            path = '/api/maniphest.edit',
            key = 'projects.add',
            value = projectPHID,
            objectIdentifier = ticketID,
            comment = None,
            needsValueArgumentInArray = True
        )

    def removeTicketFromProject(self, ticketID, projectPHID, comment):
        return self.__callEndpoint(
            path = '/api/maniphest.edit',
            key = 'projects.remove',
            value = projectPHID,
            objectIdentifier = ticketID,
            comment = comment,
            needsValueArgumentInArray = True
        )

    def addTicketToColumn(self, ticketID, columnPHID, comment):
        return self.__callEndpoint(
            path = '/api/maniphest.edit',
            key = 'column',
            value = columnPHID,
            objectIdentifier = ticketID,
            comment = comment,
            needsValueArgumentInArray = True
        )

    def updateTicketStatus(self, ticketID, value, comment):
        return self.__callEndpoint(
            path = '/api/maniphest.edit',
            key = 'status',
            value = value,
            objectIdentifier = ticketID,
            comment = comment
        )

    def updateTicketPriority(self, ticketID, value, comment):
        return self.__callEndpoint(
            path = '/api/maniphest.edit',
            key = 'priority',
            value = value,
            objectIdentifier = ticketID,
            comment = comment
        )
