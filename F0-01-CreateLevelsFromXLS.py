import clr
import sys

sys.path.append('C:\Program Files (x86)\IronPython 2.7\Lib')
import System
from System import Array
from System.Collections.Generic import *

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)
clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *


# --- Definitions
def internal_to_cm(value):
    return UnitUtils.ConvertFromInternalUnits(value, UnitTypeId.Centimeters)


def cm_to_internal(value):
    return UnitUtils.ConvertToInternalUnits(value, UnitTypeId.Centimeters)


# --- Inputs

# List of level names
level_names_lst = IN[0]
# List of elevations values
elevation_values_lst = IN[1]

# --- CODE
doc = DocumentManager.Instance.CurrentDBDocument

# Create a unified name length
str_level_names_lst = []

for level_name in level_names_lst:
    level_name = str(level_name)
    if len(level_name) == 1:
        level_name = "0" + level_name
    str_level_names_lst.append(level_name)

# Create Levels from elevation list
output = []

for level_name, level_elevation in zip(str_level_names_lst, elevation_values_lst):
    TransactionManager.Instance.EnsureInTransaction(doc)
    new_level = Level.Create(doc, cm_to_internal(int(level_elevation)))
    new_level.Name = level_name
    TransactionManager.Instance.TransactionTaskDone()
    output.append(new_level)

# --- OUT
OUT = output
