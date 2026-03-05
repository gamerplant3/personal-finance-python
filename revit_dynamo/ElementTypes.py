# Python version of the Element Types node 
# Removing need for user input

import sys
import clr
import System
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *
import Autodesk.Revit.DB as DB

DBtypes = []
dictDBtypes = {}
for a in System.AppDomain.CurrentDomain.GetAssemblies():
    if a.GetName().Name == 'RevitAPI':
    	types = a.GetTypes()
    	for spce in types:
    		if spce.IsSubclassOf(DB.Element):
    			DBtypes.append(spce)
    			dictDBtypes[spce.Name] = spce
    	break

DBtypes = sorted(DBtypes, key = lambda x : str(x.FullName))

# ------------ INPUT THE TYPE YOU'RE LOOKING FOR HERE!!! ---------------
# Use the Element Types node or Watch output to see what the options are

search_str = "ViewSheet"  # The type you want

for index, item in enumerate(DBtypes):
    if search_str.lower() in item.FullName.lower():  # case-insensitive 
        matched_item = item
        break

OUT = matched_item
