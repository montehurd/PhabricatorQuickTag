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

    def fetchColumnPHID(self, name, projectPHID):
        result = self.fetchJSON('/api/project.column.search', {
            'api.token' : self.apiToken,
            'constraints[projects][0]' : projectPHID
        })
        column = next(x for x in result['result']['data'] if x['fields']['name'] == name )
        return column['phid']

    # project.search does not currently return status, so have to do separate fetch, unfortunately, to see if projects are still open.
    # 'phid.query' is also needed to get the full project name from the phid unfortunately.
    def __fetchOpenProjectsFromProjectPHIDs(self, projectPHIDs):
        if len(projectPHIDs) == 0:
            return []
        values = {
            'api.token' : self.apiToken
        }
        for index, phid in enumerate(projectPHIDs):
            values[f'phids[{index}]'] = phid
        result = self.fetchJSON('/api/phid.query', values)['result']
        output = []
        for i, (projectPHID, project) in enumerate(result.items()):
            if project['status'] == 'open':
                output.append({'phid': projectPHID, 'name': project['name']})
        return output

    # can this be made to work for both projects and colunms?
    # combine with func above? (depends on if project search use case - where order matters so best matching appear at top)
    def fetchNamesForPHIDs(self, phids):
        print(phids)
        output = {}
        for item in self.__fetchOpenProjectsFromProjectPHIDs(phids):
            output[item['phid']] = item['name']
        return output

    def fetchProjectsMatchingSearchTerm(self, searchTerm):
        result = self.fetchJSON('/api/project.search', {
            'api.token' : self.apiToken,
            'constraints[query]' : f'title:"{searchTerm}"'
        })
        projectPHIDs = list(map(lambda projectJSON: projectJSON['phid'], result['result']['data']))
        # print(json.dumps(result['result']['data'], indent=4))
        openProjects = self.__fetchOpenProjectsFromProjectPHIDs(projectPHIDs)
        print(json.dumps(openProjects, indent=4))
        return openProjects

    # Prefix 'name' with:
    #   '@' for User
    #   '#' for Project
    #   'T' for Ticket
    # See: https://stackoverflow.com/a/52923649/135557 and https://secure.phabricator.com/w/object_name_prefixes/
    def fetchPHID(self, name):
        result = self.fetchJSON('/api/phid.lookup', {
            'api.token' : self.apiToken,
            'names[0]' : name
        })
        # print(json.dumps(result, indent=4))
        return result['result'][name]['phid']

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

    def fetchHTMLFromColumnTicketsRemarkup(self, remarkup):
        # Hit "remarkup.process" to convert our remixed remarkup to HTML:
        return self.fetchJSON('/api/remarkup.process', {
          'api.token' : self.apiToken,
          'context' : 'phriction',
          'contents[0]' : remarkup
        })['result'][0]['content']

    def fetchColumnsData(self, projectPHID, columnNamesToIgnore = []):
        result = self.fetchJSON('/api/project.column.search', {
            'api.token' : self.apiToken,
            'order[0]': '-id',
            'constraints[projects][0]' : projectPHID
            })
        columnsData = list(filter(lambda x: x['type'] == 'PCOL' and x['fields']['name'] not in columnNamesToIgnore, result['result']['data']))
        columnPHIDs = list(map(lambda column: column['phid'], columnsData))
        openColumnPHIDs = self.__fetchOpenColumnPHIDsInColumnPHIDs(columnPHIDs)
        openColumnsData = filter(lambda column: column['phid'] in openColumnPHIDs, columnsData)
        return openColumnsData

    def __fetchOpenColumnPHIDsInColumnPHIDs(self, columnPHIDs):
        values = {
            'api.token' : self.apiToken
        }
        for index, phid in enumerate(columnPHIDs):
            values[f'phids[{index}]'] = phid
        result = self.fetchJSON('/api/phid.query', values)['result']
        output = []
        for i, (phid, column) in enumerate(result.items()):
            if column['status'] == 'open':
                output.append(phid)
        return output

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
        ticketsHTML = self.fetchHTMLFromColumnTicketsRemarkup(ticketsRemarkup)
        allTicketsHTML = re.split(pattern=r'(<p>)?TICKET_START:(.*?):(</p>)?(.*?)(<p>)?TICKET_END(</p>)?', string=ticketsHTML, flags=re.DOTALL)
        ticketsHTMLByID = {}
        if len(allTicketsHTML) < 7:
            return ticketsHTMLByID
        for i in range(0, len(allTicketsHTML) - 1, 7):
            ticketID = allTicketsHTML[i + 2]
            ticketHTML = allTicketsHTML[i + 4]
            ticketsHTMLByID[ticketID] = ticketHTML.strip()
        return ticketsHTMLByID
