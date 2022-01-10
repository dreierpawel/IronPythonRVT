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

# Add List Object
from System.Collections.Generic import List
import collections
from collections import defaultdict
import System.Reflection
import math

# Definitions


def internal_to_cm(value):
    return UnitUtils.ConvertFromInternalUnits(value, UnitTypeId.Centimeters)


def cm_to_internal(value):
    return UnitUtils.ConvertToInternalUnits(value, UnitTypeId.Centimeters)


def create_parameters_list(parameter_string):
    parameter_string = parameter_string.upper()
    parameter_string = parameter_string.split(",")
    return parameter_string


def get_sh_parameter_value_by_name(element, parameter_name, default_empty_value=""):
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
            if parameter_type == StorageType.String:
                parameter_value = default_empty_value
    except Exception:
        parameter_value = False
    return parameter_value


def set_parameter_by_name(element, parameter_name, value):
    if element.LookupParameter(parameter_name).IsReadOnly is False:
        p = element.LookupParameter(parameter_name)
        p.Set(value)
        return element
    else:
        return element


def group_by_sub_index_value(list_of_lists, index_value=0):
    all_values = [lst[index_value] for lst in list_of_lists]
    unique_values = set(all_values)
    unique_values = sorted(unique_values)
    group_list = []
    for value in unique_values:
        this_group = []
        for lst in list_of_lists:
            if lst[index_value] == value:
                this_group.append(lst)
        group_list.append(this_group)
    return group_list


def extract(lst, index_val=0):
    return list(list(zip(*lst))[index_val])


def flatten(t):
    return [item for sublist in t for item in sublist]


def filter_elements_by_type(elements_list, type_name):
    filtered_list =[]
    for element in elements_list:
        if element.GetType() == type_name:
            filtered_list.append(element)
    return filtered_list


def sheet_type_list():
    sheet_type_list = ["DrawingSheet"]
    return sheet_type_list


def bool_mask_by_list(elements, element):
    bool1 = bool([ele for ele in elements if (ele in str(element.ViewType))])
    return bool1


def filtered_views_by_type(doc, type_list):
    views = []
    all_views = FilteredElementCollector(doc).OfClass(View).ToElements()
    for i in all_views:
        # Create List of Views to collect
        views.append(i) if i.IsTemplate is False and bool_mask_by_list(type_list, i) else None
    return views


def set_location(sheet, element, set_x_value=0, set_y_value=0, set_z_value=0):
    global doc
    # Get Bounding Box with Actual Coordinaters of Element
    element_bounding_box = element.get_BoundingBox(sheet)
    # Get Bounding Box Actual centre point location
    element_bounding_box_centre_point = (element_bounding_box.Max + element_bounding_box.Min) / 2.0
    bb_x = element_bounding_box_centre_point.X
    bb_y = element_bounding_box_centre_point.Y
    bb_z = element_bounding_box_centre_point.Z
    # New Location Coordinates To Internal Units
    set_x_value = cm_to_internal(set_x_value)
    set_y_value = cm_to_internal(set_y_value)
    set_z_value = cm_to_internal(set_z_value)
    # Calculate Element Move
    move_x = set_x_value - bb_x
    move_y = set_y_value - bb_y
    move_z = set_z_value - bb_z
    # Move Element
    new_location = XYZ(move_x, move_y, move_z)
    TransactionManager.Instance.EnsureInTransaction(doc)
    ElementTransformUtils.MoveElement(doc, element.Id, new_location)
    TransactionManager.Instance.TransactionTaskDone()
    return element


def viewport_edge_lengths(sheet, element):
    global doc
    # Get Bounding Box with Actual Coordinaters of Element
    element_bounding_box = element.get_BoundingBox(sheet)
    # Get Bounding Box Edge lengths
    bb_max = element_bounding_box.Max
    bb_max_x = bb_max.X
    bb_max_y = bb_max.Y
    bb_min = element_bounding_box.Min
    bb_min_x = bb_min.X
    bb_min_y = bb_min.Y
    bb_edge_x_len = bb_max_x - bb_min_x
    bb_edge_y_len = bb_max_y - bb_min_y
    return (bb_edge_x_len, bb_edge_y_len)


def rotate_viewport_l(sheet, viewport):
    # Get Dimensions of Viewport
    x_length = viewport_edge_lengths(sheet, viewport)[0]
    y_length = viewport_edge_lengths(sheet, viewport)[1]
    len_bool_test = x_length < y_length
    if len_bool_test:
        p = viewport.get_Parameter(BuiltInParameter.VIEWPORT_ATTR_ORIENTATION_ON_SHEET)
        TransactionManager.Instance.EnsureInTransaction(doc)
        p.Set(1)
        TransactionManager.Instance.TransactionTaskDone()
    return viewport


def rotate_viewport_h(sheet, viewport):
    # Get Dimensions of Viewport
    x_length = viewport_edge_lengths(sheet, viewport)[0]
    y_length = viewport_edge_lengths(sheet, viewport)[1]
    len_bool_test = x_length < y_length
    if not len_bool_test:
        p = viewport.get_Parameter(BuiltInParameter.VIEWPORT_ATTR_ORIENTATION_ON_SHEET)
        TransactionManager.Instance.EnsureInTransaction(doc)
        p.Set(1)
        TransactionManager.Instance.TransactionTaskDone()
    return viewport


def set_new_scale(sheet, viewport, window_l=19.00, window_h=10.36):
    global doc
    # Scale Viewport
    view_in_viewport = doc.GetElement(viewport.ViewId)
    view_in_viewport_scale = view_in_viewport.Scale
    x_length_cm = internal_to_cm(viewport_edge_lengths(sheet, viewport)[0])
    y_length_cm = internal_to_cm(viewport_edge_lengths(sheet, viewport)[1])
    # Calculate New Scale
    pref_x_scale = math.ceil((x_length_cm * view_in_viewport_scale) / window_l)
    pref_y_scale = math.ceil((y_length_cm * view_in_viewport_scale) / window_h)
    new_scale = max([pref_x_scale, pref_y_scale])
    TransactionManager.Instance.EnsureInTransaction(doc)
    # Set New Scale
    view_in_viewport.Scale = new_scale
    TransactionManager.Instance.TransactionTaskDone()
    return viewport


def viewports_location_on_sheets(filtered_sheets_list):
    global doc
    global view_name_prefix_string
    global view_scheme_name_prefix_string
    for sheet in filtered_sheets_list:
        # Collect Viewports on each Sheet View
        viewports_list = FilteredElementCollector(doc, sheet.Id).OfClass(Viewport).ToElements()
        for viewport in viewports_list:
            # Get Names of Viewports
            viewport_name = viewport.get_Parameter(BuiltInParameter.VIEWPORT_VIEW_NAME).AsString()
            if view_name_prefix_string in viewport_name:
                # Rotate Viewport
                viewport = rotate_viewport_l(sheet, viewport)
                # Set New Scale
                viewport = set_new_scale(sheet, viewport, window_l=19.00, window_h=10.36)
                # Set Location of Apartment Viewport
                set_location(sheet, viewport, 10.5, 17.64, 0)
            if view_scheme_name_prefix_string in viewport_name:
                # Rotate Viewport
                viewport = rotate_viewport_h(sheet, viewport)
                # Set New Scale
                viewport = set_new_scale(sheet, viewport, window_l=5.22, window_h=7.31)
                # Set Location of Scheme Viewport
                set_location(sheet, viewport, 9.97, 6.44, 0)
    return filtered_sheets_list


def filter_phase_id_by_name(string_in_name):
    phases_data_list = []
    phases_list = FilteredElementCollector(doc).OfClass(Phase).ToElements()
    selected_phase = []
    for phase in phases_list:
        phase_name = phase.Name
        phases_data_list.append((phase_name, phase.Id))
    for phase_data in phases_data_list:
        if string_in_name in phase_data[0]:
            selected_phase = phase_data[1]
    return selected_phase


def copy_view(parent_schedule, new_view_name, new_phase):
    global doc
    # Create ICollection[ElementId]
    v_ids_list = []
    v_ids_list.append(parent_schedule.Id)
    v_ids_collection = List[ElementId](v_ids_list)
    TransactionManager.Instance.EnsureInTransaction(doc)
    # Copy Element
    new_view_ids_list = ElementTransformUtils.CopyElements(doc, v_ids_collection, doc, Transform.Identity, CopyPasteOptions())
    new_view = doc.GetElement(new_view_ids_list[0])
    # Set New Name
    new_view.Name = new_view_name
    # Set Phase
    view_phase_parameter = new_view.get_Parameter(BuiltInParameter.VIEW_PHASE)
    view_phase_parameter.Set(filter_phase_id_by_name(new_phase))
    # Set New Phase
    TransactionManager.Instance.TransactionTaskDone()
    return new_view


def set_schedule_column_width_by_name(schedule_view, field_name="POMIESZCZENIE NAZWA", width_value=3.31):
    global doc
    field_order = schedule_view.Definition.GetFieldOrder()
    selected_field_id = 0
    for schedule_field_id in field_order:
        if schedule_view.Definition.GetField(schedule_field_id).GetName() == field_name:
            selected_field_id = schedule_view.Definition.GetField(schedule_field_id)
    # Set Column Width
    TransactionManager.Instance.EnsureInTransaction(doc)
    selected_field_id.SheetColumnWidth = cm_to_internal(width_value)
    TransactionManager.Instance.TransactionTaskDone()


def add_schedule_filter_equal_to_string(schedule_view, field_name, filter_value):
    global doc
    output_view = schedule_view
    field_order = schedule_view.Definition.GetFieldOrder()
    selected_field_id = 0
    for schedule_field_id in field_order:
        if schedule_view.Definition.GetField(schedule_field_id).GetName() == field_name:
            selected_field_id = schedule_field_id
    #Create Filter
    ap_number_filter = ScheduleFilter(selected_field_id, ScheduleFilterType.Equal, filter_value)
    # Add Filter
    TransactionManager.Instance.EnsureInTransaction(doc)
    schedule_view.Definition.AddFilter(ap_number_filter)
    TransactionManager.Instance.TransactionTaskDone()
    return output_view


def create_schedule_from_sheet_data(sheet_data, phase_str):
    global doc
    global input_building_code
    new_schedule_interior_name = "ZST-WEW-" + input_building_code + "." + sheet_data[2] + "." + sheet_data[1]
    new_schedule_exterior_name = "ZST-ZEW-" + input_building_code + "." + sheet_data[2] + "." + sheet_data[1]
    new_schedule_interior = copy_view(parent_schedule_interior, new_schedule_interior_name, phase_str)
    new_schedule_exterior = copy_view(parent_schedule_exterior, new_schedule_exterior_name, phase_str)
    TransactionManager.Instance.EnsureInTransaction(doc)
    set_parameter_by_name(new_schedule_interior, "OBIEKT PAKIET", "790")
    set_parameter_by_name(new_schedule_interior, "PROJEKT FAZA", "MR")
    set_parameter_by_name(new_schedule_interior, "PROJEKT BRANŻA", "AR")
    set_parameter_by_name(new_schedule_interior, "BUDYNEK ETAP", input_building_code[0])
    set_parameter_by_name(new_schedule_interior, "BUDYNEK NUMER", input_building_code[1])
    set_parameter_by_name(new_schedule_interior, "BUDYNEK SEKCJA", sheet_data[1])
    set_parameter_by_name(new_schedule_interior, "BUDYNEK POZIOM", sheet_data[2])
    set_parameter_by_name(new_schedule_exterior, "OBIEKT PAKIET", "790")
    set_parameter_by_name(new_schedule_exterior, "PROJEKT FAZA", "MR")
    set_parameter_by_name(new_schedule_exterior, "PROJEKT BRANŻA", "AR")
    set_parameter_by_name(new_schedule_exterior, "BUDYNEK ETAP", input_building_code[0])
    set_parameter_by_name(new_schedule_exterior, "BUDYNEK NUMER", input_building_code[1])
    set_parameter_by_name(new_schedule_exterior, "BUDYNEK SEKCJA", sheet_data[1])
    set_parameter_by_name(new_schedule_exterior, "BUDYNEK POZIOM", sheet_data[2])
    sheet = sheet_data[0]
    new_schedule_interior = add_schedule_filter_equal_to_string(new_schedule_interior, "POMIESZCZENIE NR LOKALU", sheet_data[1])
    new_schedule_exterior = add_schedule_filter_equal_to_string(new_schedule_exterior, "POMIESZCZENIE NR LOKALU", sheet_data[1])
    new_schedule_interior_id = new_schedule_interior.Id
    new_schedule_exterior_id = new_schedule_exterior.Id
    schedule_interior_viewport_location = XYZ(cm_to_internal(1.23), cm_to_internal(10), 0)
    ap_num = sheet_data[3]
    schedule_exterior_viewport_location = XYZ(cm_to_internal(1.23), cm_to_internal(10-((0.39*(ap_num+1))+0.2)), 0)
    schedule_interior_viewport = ScheduleSheetInstance.Create(doc, sheet.Id, new_schedule_interior_id, schedule_interior_viewport_location)
    schedule_exterior_viewport = ScheduleSheetInstance.Create(doc, sheet.Id, new_schedule_exterior_id, schedule_exterior_viewport_location)
    TransactionManager.Instance.TransactionTaskDone()
    set_schedule_column_width_by_name(new_schedule_interior, field_name="POMIESZCZENIE NAZWA", width_value=3.31)
    set_schedule_column_width_by_name(new_schedule_interior, field_name="POW ISO", width_value=1.16)
    set_schedule_column_width_by_name(new_schedule_exterior, field_name="POMIESZCZENIE NAZWA PLUS", width_value=3.31)
    set_schedule_column_width_by_name(new_schedule_exterior, field_name="POW ISO", width_value=1.16)
    return (new_schedule_interior, new_schedule_exterior)


# Inputs
input_building_code = IN[0]
# Basic card prefix or Electrical/ plumbing fixtures card for ex. "V-M.", "V-MI."
view_name_prefix_string = IN[1]
view_scheme_name_prefix_string = view_name_prefix_string[:1] + "S" + view_name_prefix_string[1:]
sheet_name_prefix_str = view_name_prefix_string[2:]+""+input_building_code
sheet_parameters_names_list = create_parameters_list(IN[2])
parent_schedule_interior = UnwrapElement(IN[3])
parent_schedule_exterior = UnwrapElement(IN[4])
# Code
doc = DocumentManager.Instance.CurrentDBDocument
# Collect sheet list
sheet_list = filtered_views_by_type(doc, sheet_type_list())
# Filter Sheet List
filtered_sheets = []
for sheet in sheet_list:
    sheet_number = sheet.get_Parameter(BuiltInParameter.SHEET_NUMBER).AsString()
    if sheet_name_prefix_str in sheet_number:
        filtered_sheets.append((sheet_number, sheet))
filtered_sheets = sorted(filtered_sheets, key=lambda x: x[0], reverse=False)
filtered_sheets = zip(*filtered_sheets)[1]
# Sheet With Dataset
filtered_sheets_dataset = []
for sheet in filtered_sheets:
    parameter_values_list = []
    for parameter_name in sheet_parameters_names_list:
        parameter_value = get_sh_parameter_value_by_name(sheet, parameter_name)
        parameter_values_list.append(parameter_value)
    # Room numbers integer
    parameter_values_list[-1] = int(parameter_values_list[-1])
    filtered_sheets_dataset.append([sheet]+parameter_values_list)
filtered_sheets_dataset = group_by_sub_index_value(sorted(filtered_sheets_dataset, key=lambda x: x[2], reverse=False), 2)
#
sheet_of_apartments_with_one_levels = flatten(filtered_sheets_dataset[:-1])
sheet_of_apartments_with_two_levels = flatten(filtered_sheets_dataset[-1:])
#
for sheet_data in sheet_of_apartments_with_one_levels :
    create_schedule_from_sheet_data(sheet_data, "PK")
for sheet_data in sheet_of_apartments_with_two_levels:
    create_schedule_from_sheet_data(sheet_data, "PB")
#
OUT = filtered_sheets_dataset
# sfilters = schedule_view.Definition.GetFilters()


