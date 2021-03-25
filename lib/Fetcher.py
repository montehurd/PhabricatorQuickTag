#!/usr/local/bin/python3

import json, urllib.parse, urllib.request, re

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

    # project.search does not currently return status, so have to do separate fetch, unfortunately, to see if projects are still open.
    # same is true for columns. 'phid.query' is also needed to get the full project name from the phid unfortunately.
    def fetchNamesForStatusOpenPHIDs(self, phids):
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
            if item['status'] == 'open':
                output[item['phid']] = item['name']
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

    def fetchColumnTickets(self, columnPHID):
        result = self.fetchJSON('/api/maniphest.search', {
            'api.token' : self.apiToken,
            'constraints[columnPHIDs][0]' : columnPHID,
            'constraints[statuses][0]' : 'open',
            'attachments[projects]' : 'true',
            'attachments[columns]' : 'true'
        })
        # print(json.dumps(result['result']['data'], indent=4))
        return filter(lambda x: x['type'] == 'TASK', result['result']['data'])

    def __fetchHTMLFromColumnTicketsRemarkup(self, remarkup):
        # Hit "remarkup.process" to convert our remixed remarkup to HTML:
        return self.fetchJSON('/api/remarkup.process', {
          'api.token' : self.apiToken,
          'context' : 'phriction',
          'contents[0]' : remarkup
        })['result'][0]['content']

    def fetchColumnsData(self, projectPHID):
        result = self.fetchJSON('/api/project.column.search', {
            'api.token' : self.apiToken,
            'order[0]': '-id',
            'constraints[projects][0]' : projectPHID
            })
        columnsData = list(filter(lambda x: x['type'] == 'PCOL', result['result']['data']))
        columnPHIDs = list(map(lambda column: column['phid'], columnsData))
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
    def callEndpoint(self, path, key, value, objectIdentifier, comment = None, needsValueArgumentInArray = False):
        values = {
            'api.token': self.apiToken,
            'transactions[0][type]': key,
            f'''transactions[0][value]{'[0]' if needsValueArgumentInArray else ''}''': value,
            'objectIdentifier': objectIdentifier,
            'output': 'json'
        }
        # print(values)
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

    def __ticketsRemarkupForTicketsJSON(self, tickets):
        return ''.join(map(lambda item:
f''' TICKET_START:{item['id']}:
= T{item['id']} =
== {item['fields']['name']} ==

{item['fields']['description']['raw']}

TICKET_END '''
        , tickets))

    def fetchTicketsHTMLByID(self, tickets):
        ticketsRemarkup = self.__ticketsRemarkupForTicketsJSON(tickets)
        ticketsHTML = self.__fetchHTMLFromColumnTicketsRemarkup(ticketsRemarkup)
        allTicketsHTML = re.split(pattern=r'(<p>)?TICKET_START:(.*?):(</p>)?(.*?)(<p>)?TICKET_END(</p>)?', string=ticketsHTML, flags=re.DOTALL)
        ticketsHTMLByID = {}
        if len(allTicketsHTML) < 7:
            return ticketsHTMLByID
        for i in range(0, len(allTicketsHTML) - 1, 7):
            ticketID = allTicketsHTML[i + 2]
            ticketHTML = allTicketsHTML[i + 4]
            ticketsHTMLByID[ticketID] = ticketHTML.strip()
        return ticketsHTMLByID
