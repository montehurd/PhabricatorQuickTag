#!/usr/local/bin/python3

import json, uuid, re
from datetime import datetime, timezone

def stringFromFile(fileName):
    with open(fileName, 'r') as f:
        return f.read()
    return None

def jsonFromFile(fileName):
    with open(fileName, 'r') as f:
        return json.load(f)
    return None

def jsonToFile(fileName, data):
    with open(fileName, 'w') as outfile:
        json.dump(data, outfile, indent=4)

def escapeBackticks(string):
    return string.replace('`', r'\`')

def cssSafeGUID():
    return f'_{uuid.uuid4().hex}'

def getNumericIDFromTicketID(ticketID):
    return re.sub("[^0-9]", '', ticketID)

def localTimezoneDateStringFromTimeStamp(ts):
    local_now = datetime.now().astimezone()
    local_tz = local_now.tzinfo
    return datetime.fromtimestamp(ts, tz=local_tz).strftime('%a, %b %e, %r')

# import subprocess
# def sendToBrowser(string, extension):
#     filePath = f'/tmp/browser.tmp.{extension}'
#     f = open(filePath, 'wt', encoding='utf-8')
#     f.write(string)
#     # subprocess.run(f'open -a "Google Chrome" {filePath} --args --disable-web-security --user-data-dir=/tmp/chrome_dev_test', shell=True, check=True, text=True)
#     subprocess.run(f'open -a "Safari" {filePath}', shell=True, check=True, text=True)
