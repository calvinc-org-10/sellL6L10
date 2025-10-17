from typing import Any, Dict, List

# self, menuID: str, menuName: str, menuItems:Dict[int,Dict]):
# {'keys': {'MenuGroup': 1, 'MenuID': 0, 'OptionNumber': 0}, 
#     'values': {etc}}
test_menulist = [
{'keys': {'MenuGroup': 1, 'MenuID': 0, 'OptionNumber': 0},
    'values': {'OptionText': 'Admin Menu', 'Command': None, 'Argument': '', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 0, 'OptionNumber': 1},
    'values': {'OptionText': 'User Admin', 'Command': 11, 'Argument': 'L10-WICS-UAdmin', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 0, 'OptionNumber': 2},
    'values': {'OptionText': 'Edit Menu', 'Command': 91, 'Argument': '', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 0, 'OptionNumber': 3},
    'values': {'OptionText': 'Django Admin', 'Command': 11, 'Argument': 'django-admin', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 0, 'OptionNumber': 11},
    'values': {'OptionText': 'IncShip', 'Command': 1, 'Argument': '5', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 0, 'OptionNumber': 19},
    'values': {'OptionText': 'Change Password', 'Command': 51, 'Argument': '', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 0, 'OptionNumber': 20},
    'values': {'OptionText': 'Go Away!', 'Command': 200, 'Argument': '', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 3, 'OptionNumber': 0},
    'values': {'OptionText': 'Calvin\'s Menu', 'Command': None, 'Argument': '', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, }},
{'keys': {'MenuGroup': 1, 'MenuID': 3, 'OptionNumber': 4},
    'values': {'OptionText': 'new reference', 'Command': 11, 'Argument': 'newref', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 3, 'OptionNumber': 1},
    'values': {'OptionText': 'HBL', 'Command': 11, 'Argument': 'HBLForm', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 3, 'OptionNumber': 3},
    'values': {'OptionText': 'references', 'Command': 11, 'Argument': 'refsForm', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 3, 'OptionNumber': 6},
    'values': {'OptionText': 'Invoices', 'Command': 11, 'Argument': 'InvoiceForm', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 3, 'OptionNumber': 8},
    'values': {'OptionText': 'Invoices to Enter', 'Command': 11, 'Argument': 'InvoicesNotsubmitted', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 3, 'OptionNumber': 11},
    'values': {'OptionText': 'Test 1', 'Command': 11, 'Argument': 'test01', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, }},
{'keys': {'MenuGroup': 1, 'MenuID': 3, 'OptionNumber': 12},
    'values': {'OptionText': 'Test 2', 'Command': 11, 'Argument': 'test02', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, }},
{'keys': {'MenuGroup': 1, 'MenuID': 3, 'OptionNumber': 14},
    'values': {'OptionText': 'Initial Loads', 'Command': 1, 'Argument': '6', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 3, 'OptionNumber': 15},
    'values': {'OptionText': 'Spreadsheet Interface', 'Command': 1, 'Argument': '6', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 3, 'OptionNumber': 19},
    'values': {'OptionText': 'Run SQL', 'Command': 31, 'Argument': '', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 3, 'OptionNumber': 20},
    'values': {'OptionText': 'Return to Main Menu', 'Command': 1, 'Argument': '5', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, }},
{'keys': {'MenuGroup': 1, 'MenuID': 5, 'OptionNumber': 0},
    'values': {'OptionText': 'Main Menu', 'Command': None, 'Argument': 'Default', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, }},
{'keys': {'MenuGroup': 1, 'MenuID': 5, 'OptionNumber': 1},
    'values': {'OptionText': 'Calvin', 'Command': 1, 'Argument': '3', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 5, 'OptionNumber': 2},
    'values': {'OptionText': 'Frequently Used Menu', 'Command': 1, 'Argument': '1', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 5, 'OptionNumber': 17},
    'values': {'OptionText': 'Test', 'Command': 1, 'Argument': '4', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 5, 'OptionNumber': 18},
    'values': {'OptionText': 'System Menu', 'Command': 1, 'Argument': '99', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, }},
{'keys': {'MenuGroup': 1, 'MenuID': 5, 'OptionNumber': 19},
    'values': {'OptionText': 'Admin Menu', 'Command': 1, 'Argument': '0', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 5, 'OptionNumber': 20},
    'values': {'OptionText': 'Go Away!', 'Command': 200, 'Argument': '', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, }},
{'keys': {'MenuGroup': 1, 'MenuID': 99, 'OptionNumber': 0},
    'values': {'OptionText': 'System Menu', 'Command': None, 'Argument': '', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, }},
{'keys': {'MenuGroup': 1, 'MenuID': 99, 'OptionNumber': 1},
    'values': {'OptionText': 'Edit Parameters', 'Command': 92, 'Argument': '', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, }},
{'keys': {'MenuGroup': 1, 'MenuID': 99, 'OptionNumber': 2},
    'values': {'OptionText': 'Edit Greetings', 'Command': 93, 'Argument': '', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, }},
{'keys': {'MenuGroup': 1, 'MenuID': 99, 'OptionNumber': 4},
    'values': {'OptionText': 'Edit Menu', 'Command': 91, 'Argument': '', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, }},
{'keys': {'MenuGroup': 1, 'MenuID': 99, 'OptionNumber': 20},
    'values': {'OptionText': 'Main menu', 'Command': 1, 'Argument': '5', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, }},
{'keys': {'MenuGroup': 1, 'MenuID': 6, 'OptionNumber': 0},
    'values': {'OptionText': 'Initial Loads', 'Command': None, 'Argument': '', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 6, 'OptionNumber': 20},
    'values': {'OptionText': 'Return to Main Menu', 'Command': 1, 'Argument': '5', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 6, 'OptionNumber': 2},
    'values': {'OptionText': 'init-load-HBL-00', 'Command': 11, 'Argument': 'init-load-HBL-00', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
{'keys': {'MenuGroup': 1, 'MenuID': 6, 'OptionNumber': 3},
    'values': {'OptionText': 'load Invoices', 'Command': 11, 'Argument': 'init-load-Inv-00', 'PWord': '', 'TopLine': None, 'BottomLine': None, }},
]

class MenuRecords(object):
    mSource = test_menulist
    
    def menuAttr(self, mGroup:int, mID:int, Opt:int, AttrName:str) -> Any:
        return list(menuRec['values'][AttrName] \
                        for menuRec in self.mSource \
                        if menuRec['keys']['MenuGroup']==mGroup \
                            and menuRec['keys']['MenuID']==mID \
                            and menuRec['keys']['OptionNumber']==Opt \
            )[0]

    def dfltMenuID_forGroup(self, mGroup:int) -> int:
        return list(menuRec['keys']['MenuID'] \
                        for menuRec in self.mSource \
                        if menuRec['keys']['MenuGroup']==mGroup \
                            and menuRec['keys']['OptionNumber']==0 \
                            and menuRec['values']['Argument'].lower() == 'default'\
            )[0]
    
    def menuDict(self, mGroup:int, mID:int) ->  Dict[int,Dict]:
       return { mRec['keys']['OptionNumber']: mRec['values'] \
                    for mRec in self.mSource \
                    if mRec['keys']['MenuGroup']==mGroup \
                        and mRec['keys']['MenuID']==mID 
            }
    
    def menuExist(self, mGroup:int, mID:int) ->  bool:
        return any(list(True \
                    for mRec in self.mSource \
                    if mRec['keys']['MenuGroup']==mGroup \
                        and mRec['keys']['MenuID']==mID \
                        and mRec['keys']['OptionNumber']==0 \
            ))
