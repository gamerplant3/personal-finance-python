# Returns the file path for the dynamo script
import clr

clr.AddReference('DynamoServices')

from Dynamo.Events import *

fullPath = ExecutionEvents.ActiveSession.CurrentWorkspacePath

OUT = "\\".join(fullPath.split("\\")[:-1]) + "\\"
