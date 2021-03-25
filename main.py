#!/usr/local/bin/python3

import sys, webview
sys.path.insert(0, './lib')
from WebviewController import WebviewController
import ButtonManifestRegistry

if __name__ == '__main__':
    window = webview.create_window('', html='', resizable=True, width=1280, height=1024, fullscreen=False)
    webviewController = WebviewController(window = window)
    window.expose(ButtonManifestRegistry.performClickActions) # expose to JS as 'pywebview.api.performClickActions'
    webview.start(webviewController.expose, window, debug=True)
