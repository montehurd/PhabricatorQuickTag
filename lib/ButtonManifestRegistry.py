#!/usr/local/bin/python3

# Every button needs to be added to 'allButtonManifestRegistry' - when a click happens it is checked for that button's id and the manifest for that button is then checked to know what actions to perform.
__buttonManifestRegistry = {}

def add(buttonManifests):
    buttonManifestsDictionaryByID = {manifest.id : manifest for manifest in buttonManifests}

    global __buttonManifestRegistry
    __buttonManifestRegistry = dict(
        # Merge two dictionaries: https://stackoverflow.com/a/26853961
        **__buttonManifestRegistry, **buttonManifestsDictionaryByID
    )

def clear():
    global __buttonManifestRegistry
    __buttonManifestRegistry = {}

# Actions can hit endpoints, update button states, hide/show tickets, etc.
def performClickActions(buttonID):
    clickedButtonManifest = __buttonManifestRegistry[buttonID]
    for action in clickedButtonManifest.clickActions:
        # if any action result is False execute the failure options and bail
        if action() == False:
            for failureAction in clickedButtonManifest.failureActions:
                failureAction()
            return
    # if here all actions succeeded, so execute success actions
    for successAction in clickedButtonManifest.successActions:
        successAction()
