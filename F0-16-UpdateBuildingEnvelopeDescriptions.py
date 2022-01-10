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
apartment_card_vt = UnwrapElement(IN[0])
apartment_card_scheme_vt = UnwrapElement(IN[0])
input_b_code = IN[2]
# Inputs

doc = DocumentManager.Instance.CurrentDBDocument
all_views = FilteredElementCollector(doc).OfCategory(
    BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()

filtred_views = []
for i, view in enumerate(all_views):
    view_p_num = view.LookupParameter("OBIEKT PAKIET").AsString()
    view_phase = view.LookupParameter("PROJEKT FAZA").AsString()
    view_role = view.LookupParameter("PROJEKT BRANŻA").AsString()
    view_building_phase = view.LookupParameter("BUDYNEK ETAP").AsString()
    view_building_num = view.LookupParameter("BUDYNEK NUMER").AsString()
    try:
        view_building_complete_code = view_building_phase + view_building_num
    except:
        view_building_complete_code = "00"
    if view_p_num == "100" and view_phase == "PB" and view_role == "AR" and view_building_complete_code == input_b_code:
        filtred_views.append((view, view.get_Parameter(BuiltInParameter.PLAN_VIEW_LEVEL).AsString()))

for i, view in enumerate(filtred_views):
    view_level_parameter = view[1]
    if view_level_parameter == "P1" or view_level_parameter == "DA":
        del filtred_views[i]

filtred_views = sorted(filtred_views, key=lambda x: x[1], reverse=False)
filtred_views  = zip(*filtred_views )[0]

# OUT
OUT = filtred_views