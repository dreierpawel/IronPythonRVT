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

from System.Collections.Generic import List
import collections
from collections import defaultdict

# Definitions


def get_sh_parameter_value_by_name(element, parameter_name):
    try:
        parameter_value = element.LookupParameter(parameter_name)
        parameter_type = parameter_value.StorageType
        if parameter_type == StorageType.String:
            parameter_value = parameter_value.AsString()
        if parameter_type == StorageType.Integer:
            parameter_value = parameter_value.AsInteger()
        if parameter_type == StorageType.Double:
            parameter_value = parameter_value.AsDouble()
        if parameter_type == StorageType.ElementId:
            parameter_value = parameter_value.AsElementId()
        if element.LookupParameter(parameter_name).HasValue is False:
            parameter_value = False
    except TypeError:
        parameter_value = False
    return parameter_value


def set_sh_parameter_value_by_value(element, parameter_name, parameter_value):
    global doc
    try:
        TransactionManager.Instance.EnsureInTransaction(doc)
        element.LookupParameter(parameter_name).Set(parameter_value)
        TransactionManager.Instance.TransactionTaskDone()
    except Exception:
        element = False
    return element


def view_types_list():
    view_types_lst = [
        "Elevation",
        "Section",
        "FloorPlan",
        "CeilingPlan",
        "AreaPlan",
        "EngineeringPlan",
    ]
    return view_types_lst


def bool_mask_by_list(elements, element):
    bool1 = bool([ele for ele in elements if (ele in str(element.ViewType))])
    return bool1


def collect_views_by_type(type_list):
    global doc
    views = []
    all_views = FilteredElementCollector(doc).OfClass(View).ToElements()
    for i in all_views:
        # Create List of Views to collect
        views.append(i) if i.IsTemplate is False and bool_mask_by_list(type_list, i) else None
    return views


def filter_view_by_phase(parameter_value):
    # Collect Views by project phase
    views_list = collect_views_by_type(view_types_list())
    filter_views_lst = []
    # Filter by Phase
    for i in views_list:
        param = i.LookupParameter("BIMPL_FAZA").AsString()
        if param == parameter_value:
            filter_views_lst.append(i)
    return filter_views_lst


def add_scope_box_to_elements(elements, scope_box):
    # Get scope box id
    scope_box_id = scope_box.Id
    output_confirm = []
    # Filter by Phase
    for e in elements:
        try:
            TransactionManager.Instance.EnsureInTransaction(doc)
            p = e.get_Parameter(BuiltInParameter.DATUM_VOLUME_OF_INTEREST)
            p.Set(scope_box_id)
            TransactionManager.Instance.TransactionTaskDone()
            output_confirm.append(e)
        except:
            TransactionManager.Instance.EnsureInTransaction(doc)
            p = e.get_Parameter(BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP)
            p.Set(scope_box_id)
            TransactionManager.Instance.TransactionTaskDone()
            output_confirm.append(e)
    return output_confirm


# CODE
doc = DocumentManager.Instance.CurrentDBDocument
# INPUTS
# Project phase abbrev. - for ex. "PK"
project_phase_abbrev = IN[0]
# Select Model Element - Scope Box
scope_box_views = UnwrapElement(IN[1])
# Select Model Element - Scope Box
scope_box_grids_and_levels = UnwrapElement(IN[2])
# Code
views_list = filter_view_by_phase(project_phase_abbrev)
levels_list = FilteredElementCollector(doc).OfClass(Level).ToElements()
grids_list = FilteredElementCollector(doc).OfClass(Grid).ToElements()
# Add Scope Boxes
add_scope_box_to_elements(views_list, scope_box_views)
add_scope_box_to_elements(levels_list, scope_box_grids_and_levels)
add_scope_box_to_elements(grids_list, scope_box_grids_and_levels)
# OUT
OUT = views_list, levels_list, grids_list
