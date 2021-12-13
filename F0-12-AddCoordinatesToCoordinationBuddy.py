# P.DREIER ©  github.com/dreierpawel
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


# Definitions
def internal_to_cm(value):
    return UnitUtils.ConvertFromInternalUnits(value, UnitTypeId.Centimeters)


def cm_to_internal(value):
    return UnitUtils.ConvertToInternalUnits(value, UnitTypeId.Centimeters)


# Inputs
coordination_buddy = UnwrapElement(IN[0])
# CODE
doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application
uidoc = uiapp.ActiveUIDocument
# Collect View Family Types
points = FilteredElementCollector(doc).OfClass(BasePoint).ToElements()
survey_point = None
for p in points:
    if p.Category.Name.ToString() == "Survey Point":
        survey_point = p
#
survey_point_ns = str(internal_to_cm(survey_point.LookupParameter("N/S").AsDouble())/100) + " m"
survey_point_ew = str(internal_to_cm(survey_point.LookupParameter("E/W").AsDouble())/100) + " m"
#
TransactionManager.Instance.EnsureInTransaction(doc)
coordination_buddy_ns = coordination_buddy.LookupParameter("N/S")
coordination_buddy_ns.Set(survey_point_ns)
coordination_buddy_ew = coordination_buddy.LookupParameter("E/W")
coordination_buddy_ew.Set(survey_point_ew)
TransactionManager.Instance.TransactionTaskDone()
# OUT
OUT = survey_point
