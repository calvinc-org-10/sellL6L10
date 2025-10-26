
# import testforms
from app import forms
from app import forms_testing
# import incShip.load_init_data.load_HBL as load_HBL
# import incShip.load_init_data.load_Invoices as load_Invoices 

# def LoadAdmin(parent):
def LoadAdmin():
    # return redirect('/admin/')
    return



#########################################################################
#########################################################################


FormNameToURL_Map = {}
# FormNameToURL_Map['menu Argument'.lower()] = (url, view)
# FormNameToURL_Map['l10-wics-uadmin'.lower()] = (None, fnWICSuserForm)
# FormNameToURL_Map['l6-wics-uadmin'.lower()] = FormNameToURL_Map['l10-wics-uadmin']

# FormNameToURL_Map['django-admin'.lower()] = (None, LoadAdmin)

FormNameToURL_Map['WOTbl'.lower()] = (None, forms.WOTable)
FormNameToURL_Map['ProjTbl'.lower()] = (None, forms.ProjectsTable)
FormNameToURL_Map['PartsTbl'.lower()] = (None, forms.PartsTable)

FormNameToURL_Map['WOPartsNeeded'.lower()] = (None, forms.WOPartsNeededForm)

FormNameToURL_Map['PickList'.lower()] = (None, forms_testing.PickListReport)

FormNameToURL_Map['WORecord'.lower()] = (None, forms.WorkOrdersRecord)
FormNameToURL_Map['WORecord_MP'.lower()] = (None, forms.WorkOrdersRecord_multipage)

