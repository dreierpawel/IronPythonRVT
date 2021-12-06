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
        if element.LookupParameter(parameter_name).HasValue == False:
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


def collect_view_templates():
    # Collect Views
    all_views_list = FilteredElementCollector(doc).OfClass(View).ToElements()
    view_templates_list = []
    # Filter View Templates
    for view in all_views_list:
        if view.IsTemplate is True:
            view_templates_list.append(view)
        else:
            pass
    return view_templates_list


def filter_list_by_sh_parameter_and_value(element_list, parameter_name, parameter_value):
    output_list = []
    for element in element_list:
        # Create Boolean Filter by SH Parameter Value
        bool_filter = get_sh_parameter_value_by_name(element, parameter_name) == parameter_value
        if bool_filter is True:
            output_list.append(element)
    return output_list


# Inputs
# Input - Existing Phase abrev. to copy ex. "PK"
old_phase = IN[0]
# Input - New Phase abrev. ex. "PAB"
new_phase = IN[1]
# CODE
doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application
uidoc = uiapp.ActiveUIDocument
# Collect View Templates
view_templates_list = collect_view_templates()
# Filter View Templates to Copy by Phase
view_templates_list = filter_list_by_sh_parameter_and_value(view_templates_list, "BIMPL_FAZA", old_phase)
# Copy Views Templates
new_view_templates_list = []
for view_template in view_templates_list:
    view_template_name = view_template.Name
    new_view_template_name = view_template_name.replace(old_phase, new_phase)
    #Create ICollection[ElementId]
    ids_list = []
    ids_list.append(view_template.Id)
    ids_collection = List[ElementId](ids_list)
    TransactionManager.Instance.EnsureInTransaction(doc)
    # Copy Element
    new_view_ids_list = ElementTransformUtils.CopyElements(doc, ids_collection, doc, Transform.Identity, CopyPasteOptions())
    new_view = doc.GetElement(new_view_ids_list[0])
    # Set New Name
    new_view.Name = new_view_template_name
    # Set New Phase
    set_sh_parameter_value_by_value(new_view, "BIMPL_FAZA", new_phase)
    TransactionManager.Instance.TransactionTaskDone()
    new_view_templates_list.append(new_view)
# OUT
OUT = new_view_templates_list
