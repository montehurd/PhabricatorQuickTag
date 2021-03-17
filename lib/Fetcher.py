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

    def fetchColumnPHID(self, name, projectPHID):
        result = self.fetchJSON('/api/project.column.search', {
            'api.token' : self.apiToken,
            'constraints[projects][0]' : projectPHID
        })
        column = next(x for x in result['result']['data'] if x['fields']['name'] == name )
        return column['phid']

    # For some reason the commented out version above won't match if the project name is for a sub-project... hence the 'project.search' approach below:
    def fetchProjectPHID(self, name):
        result = self.fetchJSON('/api/project.search', {
            'api.token' : self.apiToken,
            'constraints[query]' : f'title:"{name}"'
        })
        projects = list(filter(lambda x: x['type'] == 'PROJ', result['result']['data']))
        # todo: add console print message here if 'projects' doesn't contain one element - output the 'name' in the message so the user knows which project can't be found
        return projects[0]['phid']

    def fetchProjectNamesMatchingSearchTerm(self, searchTerm):
        result = self.fetchJSON('/api/project.search', {
            'api.token' : self.apiToken,
            'constraints[query]' : searchTerm
        })
        return list(map(lambda x: x['fields']['name'], result['result']['data']))

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

    def fetchColumnsData(self, project, columnNamesToIgnore = []):
        result = self.fetchJSON('/api/project.column.search', {
            'api.token' : self.apiToken,
            'order[0]': '-id',
            'constraints[projects][0]' : project.phid
            })
        return list(filter(lambda x: x['type'] == 'PCOL' and x['fields']['name'] not in columnNamesToIgnore, result['result']['data']))

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
