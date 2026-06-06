# Get the Revit version number for the open document

import clr
clr.AddReference("RevitServices")

import RevitServices 

from RevitServices.Persistence import DocumentManager

uiapp = DocumentManager.Instance.CurrentUIApplication

app = uiapp.Application

version=int(app.VersionNumber)

OUT = version
