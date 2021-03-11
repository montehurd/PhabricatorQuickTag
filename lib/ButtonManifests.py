#!/usr/local/bin/python3

# Every button needs to be added to 'allButtonManifests' - when a click happens it is checked for that button's id and the manifest for that button is then checked to know what actions to perform.
allButtonManifests = {}

def add(buttonManifests):
    buttonManifestsDictionaryByID = {manifest.id : manifest for manifest in buttonManifests}

    global allButtonManifests
    allButtonManifests = dict(
        # Merge two dictionaries: https://stackoverflow.com/a/26853961
        **allButtonManifests, **buttonManifestsDictionaryByID
    )

def clear():
    global allButtonManifests
    allButtonManifests = {}
