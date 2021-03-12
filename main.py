#!/usr/local/bin/python3

import sys, webview
sys.path.insert(0, './lib')
from Fetcher import Fetcher
from WebviewController import WebviewController
import DataStore, ButtonManifests

if __name__ == '__main__':
    DataStore.loadConfiguration()
    fetcher = Fetcher(DataStore.getConfigurationValue('url'), DataStore.getConfigurationValue('token'))
    window = webview.create_window('PHABRICATOR QUICK TAG : Quickly tag tickets from columns on various projects into any column on a destination project', html='Loading...', resizable=True, width=1280, height=1024, fullscreen=False)
    webviewController = WebviewController(
        window = window,
        fetcher = fetcher
    )
    window.expose(ButtonManifests.performClickActions) # expose to JS as 'pywebview.api.performClickActions'
    webview.start(webviewController.expose, window, debug=True)
