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


# --- Definitions
def internal_to_cm(value):
    return UnitUtils.ConvertFromInternalUnits(value, UnitTypeId.Centimeters)


def cm_to_internal(value):
    return UnitUtils.ConvertToInternalUnits(value, UnitTypeId.Centimeters)


def sort_levels_by_elevation(all_levels_list):
    levels_and_parameters_lst = []
    for level in all_levels_list:
        level_elevation = internal_to_cm(level.Elevation)
        level_and_parameters = (level, level_elevation)
        levels_and_parameters_lst.append(level_and_parameters)
    # Sort Levels list and Levels Parameters list by Elevation
    levels_and_parameters_lst = sorted(levels_and_parameters_lst, key=lambda x: x[1], reverse=False)
    # Get Levels list
    levels_lst = zip(*levels_and_parameters_lst)[0]
    return levels_lst


def create_views_by_levels_and_view_template(phase, view_family_types_name_contains_str):
    doc = DocumentManager.Instance.CurrentDBDocument
    # Collect all Levels
    all_levels_list = FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType().ToElements()
    levels_list = sort_levels_by_elevation(all_levels_list)

    output = []
    view_family_types_id = []
    levels_id_list = []

    if toggle:
        # Filter View Family Types Ids By Phase
        view_family_types = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
        for view in view_family_types:
            view_name = view.LookupParameter("Type Name").AsString()
            boolmask = bool([ele for ele in phase if (ele in view_name)])
            if boolmask:
                if view_family_types_name_contains_str in view_name:
                    view_family_types_id.append(view.Id)

        # Get Levels Ids
        for level in levels_list:
            levels_id_list.append(level.Id)

        # Create Views
        for level_id in levels_id_list:
            for view_type_id in view_family_types_id:
                # Start Transaction Manager
                TransactionManager.Instance.EnsureInTransaction(doc)
                # Create Views
                new_view = ViewPlan.Create(doc, view_type_id, level_id)
                # Create Name for New View
                new_view_phase = doc.GetElement(doc.GetElement(view_type_id).DefaultTemplateId).LookupParameter(
                    "BIMPL_FAZA").AsString()
                new_view_level_name = str(doc.GetElement(level_id).Name)
                new_view_role = doc.GetElement(doc.GetElement(view_type_id).DefaultTemplateId).LookupParameter(
                    "BIMPL_ROLA").AsString()
                new_view_name_str = ''.join([new_view_phase, "-", new_view_level_name, "-", new_view_role])
                new_view.Name = new_view_name_str
                # To DST Type
                output.append(new_view.ToDSType(True))
                # End Transaction Menager
                TransactionManager.Instance.TransactionTaskDone()
    else:
        output.append("Set to True")
    return output

# --- Inputs
# Abbr. of phase,  ex. "PT" or "PK"
phase = [IN[0].upper() + "-"]
# View Family Type name contains string, ex. "-100-01-RZUT OGÓLNY"
view_family_types_name_contains_str_lst = IN[1]
# True or false boolean
toggle = IN[2]

# --- CODE
output = []

for vt_str in view_family_types_name_contains_str_lst:
    views_lst = create_views_by_levels_and_view_template(phase, vt_str)
    output.append(views_lst)

# --- OUT
OUT = output
