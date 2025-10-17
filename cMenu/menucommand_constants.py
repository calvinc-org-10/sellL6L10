# this list of constants is here becxause its refd by kls_cMenu and models
# it's alone so it doesn't cause circular reference

import types


# Menu Command Constants
MENUCOMMANDS = {
    # CommandNumber: CommandText
    0: '',     #'Null Command',
    1: 'LoadMenu',
    11: 'FormBrowse',
    15: 'OpenTable',
    21: 'RunCode',
    31: 'RunSQLStatement',
    32: 'ConstructSQLStatement',
    36: 'LoadExtWebPage',
    51: 'ChangePW',
    91: 'EditMenu',
    92: 'EditParameters',
    93: 'EditGreetings',
    200: 'ExitApplication',
}
# Convert dictionary to object
COMMANDNUMBER =  types.SimpleNamespace(**{CText:CNum for CNum,CText in MENUCOMMANDS.items()})
