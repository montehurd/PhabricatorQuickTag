#!/usr/local/bin/python3

class Project:
    def __init__(self, phid, columnPHIDs=[]):
        self.name = None
        self.columnPHIDs = columnPHIDs
        self.phid = phid
        self.columns = []
        self.buttonsMenuColumns = []
        self.status = None
        self.icon = None

    def html(self, destinationProjectsCount):
        return f'''
            <div class="project_columns" id="_{self.phid}">
                {''.join(map(lambda column: column.html(destinationProjectsCount), self.columns))}
            </div>
        '''