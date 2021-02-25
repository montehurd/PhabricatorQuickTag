# PhabricatorQuickTag

Quickly tag tickets from columns on various projects into any column on a destination project.

## Installation
### From a Terminal window

* clone the repo onto your machine:

      git clone https://github.com/montehurd/PhabricatorQuickTag.git

* install the 'pywebview' dependency:

      pip3 install pywebview

### With a text editor
* adjust the values in `~/PhabricatorQuickTag/configuration.json` to reflect the url, projects and columns of your Phabricator instance.

## Run it
    python3 ~/PhabricatorQuickTag/main.py
