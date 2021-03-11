#!/usr/local/bin/python3

class ButtonManifest:
    def __init__(self, id, title = None, isInitiallySelected = False, clickActions = [], successActions = [], failureActions = []):
        self.id = id # must be GUID so buttons may be differentiated any in python we can look up manifest when a button is clicked
        self.title = title
        self.isInitiallySelected = isInitiallySelected
        self.clickActions = clickActions
        self.successActions = successActions # executed if all 'clickAction' succeeded
        self.failureActions = failureActions # executed if any 'clickAction' failed

    def html(self):
        return f"""
            <button onclick="pywebview.api.performClickedButtonActions('{self.id}')" {'class="selected"' if self.isInitiallySelected else ''} id="{self.id}")">{self.title}</button>
        """
