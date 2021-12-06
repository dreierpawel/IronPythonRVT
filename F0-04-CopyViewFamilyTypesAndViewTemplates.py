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


def collect_view_family_types():
    global doc
    # Collect View Family Types
    return FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()


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


def filter_list_by_name_contains(element_list, parameter_value):
    output_list = []
    for element in element_list:
        # Filter by Element Type Name Contains parameter_value
        element_name = Autodesk.Revit.DB.Element.Name.__get__(element)
        if parameter_value in element_name:
            output_list.append(element)
    return output_list


def copy_view_template_by_view_family_type(view_family_type, old_phase, new_phase):
    # Get Default View Template Id
    view_template_id = view_family_type.get_Parameter(BuiltInParameter.DEFAULT_VIEW_TEMPLATE).AsElementId()
    # Get Default View Template
    view_template = doc.GetElement(view_template_id)
    # Get Default View Template Name
    view_template_name = Autodesk.Revit.DB.Element.Name.__get__(view_template)
    # Create New View Template Name
    new_view_template_name = view_template_name.replace(old_phase, new_phase)
    # Create ICollection[ElementId]
    vt_ids_list = []
    vt_ids_list.append(view_template.Id)
    vt_ids_collection = List[ElementId](vt_ids_list)
    TransactionManager.Instance.EnsureInTransaction(doc)
    # Copy Element
    new_view_ids_list = ElementTransformUtils.CopyElements(doc, vt_ids_collection, doc, Transform.Identity, CopyPasteOptions())
    new_view = doc.GetElement(new_view_ids_list[0])
    # Set New Name
    new_view.Name = new_view_template_name
    # Set New Phase
    set_sh_parameter_value_by_value(new_view, "BIMPL_FAZA", new_phase)
    TransactionManager.Instance.TransactionTaskDone()
    return new_view


def copy_view_family_types(elements_list_to_copy, old_phase, new_phase):
    new_view_family_types_list = []
    for view_family_type in elements_list_to_copy:
        # Get Actual View Family Type Name
        view_family_type_name = Autodesk.Revit.DB.Element.Name.__get__(view_family_type)
        # Create New Family Type Name
        new_view_family_type_name = view_family_type_name.replace(old_phase, new_phase)
        # Create ICollection[ElementId]
        ids_list = []
        ids_list.append(view_family_type.Id)
        ids_collection = List[ElementId](ids_list)
        # Start New Transaction
        TransactionManager.Instance.EnsureInTransaction(doc)
        # Copy Element
        new_view_family_type_ids_list = ElementTransformUtils.CopyElements(doc, ids_collection, doc, Transform.Identity, CopyPasteOptions())
        # Get Element by Element Id
        new_view_family_type = doc.GetElement(new_view_family_type_ids_list[0])
        # Set New Name
        new_view_family_type.Name = new_view_family_type_name
        TransactionManager.Instance.TransactionTaskDone()
        # Get View Family Type default View Template and Create New View Template if Old View Template Exist
        # Check Actual View Template
        vt_test = view_family_type.get_Parameter(BuiltInParameter.DEFAULT_VIEW_TEMPLATE).AsElementId().IntegerValue != -1
        if vt_test is True:
            new_view_template = copy_view_template_by_view_family_type(view_family_type, old_phase, new_phase)
            # Set New View Template
            TransactionManager.Instance.EnsureInTransaction(doc)
            new_view_family_type_view_template = new_view_family_type.get_Parameter(BuiltInParameter.DEFAULT_VIEW_TEMPLATE)
            new_view_family_type_view_template.Set(new_view_template.Id)
            TransactionManager.Instance.TransactionTaskDone()
        # Create List of new View Family Types
        new_view_family_types_list.append(new_view_family_type)
    return new_view_family_types_list


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
# Collect View Family Types
view_family_types_list = collect_view_family_types()
# Filter View Family Types by Phase
view_family_types_list = filter_list_by_name_contains(view_family_types_list, old_phase)
# Copy Views Family Types and Create New view Templates
new_view_family_types_list = copy_view_family_types(view_family_types_list, old_phase, new_phase)
# OUT
OUT = new_view_family_types_list
