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


def filter_views_by_building_code(building_code):
    global doc
    # Collect All Views
    all_views = FilteredElementCollector(doc).OfCategory(
        BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
    # Filter Views by Parameters
    filtered_views = []
    for i, view in enumerate(all_views):
        # Parameters List to Create Boolean
        view_p_num = view.LookupParameter("OBIEKT PAKIET").AsString()
        view_phase = view.LookupParameter("PROJEKT FAZA").AsString()
        view_role = view.LookupParameter("PROJEKT BRANŻA").AsString()
        view_building_phase = view.LookupParameter("BUDYNEK ETAP").AsString()
        view_building_num = view.LookupParameter("BUDYNEK NUMER").AsString()
        try:
            view_building_complete_code = view_building_phase + view_building_num
        except:
            view_building_complete_code = "00"
        # Boolean test
        if view_p_num == "100" and view_phase == "PB" and view_role == "AR" and \
                view_building_complete_code == building_code:
            # List of filtered views
            filtered_views.append((view, view.get_Parameter(BuiltInParameter.PLAN_VIEW_LEVEL).AsString()))
    # Filter Views List by Level Type
    for i, view in enumerate(filtered_views):
        view_level_parameter = view[1]
        if view_level_parameter == "P1" or view_level_parameter == "DA":
            del filtered_views[i]
    # Sort Views List
    filtered_views = sorted(filtered_views, key=lambda x: x[1], reverse=False)
    # Get Clean Views List
    filtered_views = zip(*filtered_views)[0]
    return filtered_views


def group_rooms_by_apartment_number():
    global doc
    # Collect All Rooms
    collector = FilteredElementCollector(doc).WherePasses(Architecture.RoomFilter()).ToElements()
    apartment_rooms = []
    for room in collector:
        # Filter rooms list by room type parameter
        if "+" in room.LookupParameter("POMIESZCZENIE TYP").AsString():
            room_ap_number = room.LookupParameter("POMIESZCZENIE NR LOKALU").AsString()
            room_level_name = room.Level.Name
            room_phase_name = doc.GetElement(room.get_Parameter(BuiltInParameter.ROOM_PHASE).AsElementId()).Name
            apartment_rooms.append((room_ap_number, room, room_level_name, room_phase_name))
    # Sort Rooms List (room_ap_number, room, room_level_name, room_phase_name)
    # Sort by ap_number
    apartment_rooms = sorted(apartment_rooms, key=lambda x: x[0], reverse=False)
    # Sort by ap_level
    apartment_rooms = sorted(apartment_rooms, key=lambda x: x[2], reverse=False)
    # Filter Rooms By Phase (room_ap_number, room, room_level_name, room_phase_name)
    filtered_rooms = []
    for room in apartment_rooms:
        if "PK" in room[3]:
            filtered_rooms.append(room)
    # Group Rooms By Levels (room_ap_number, room, room_level_name, room_phase_name)
    filtered_rooms = group_by_sub_index_value(filtered_rooms,2)
    # Group Rooms By Apartment Number (room_ap_number, room, room_level_name, room_phase_name)
    rooms_grouped_by_ap_number = []
    for rooms_grouped_by_levels in filtered_rooms:
        rooms_grouped_by_levels = group_by_sub_index_value(rooms_grouped_by_levels, 0)
        rooms_grouped_by_ap_number.append(rooms_grouped_by_levels)
    # Simplify Rooms List
    final_rooms_list = []
    for levels_lst in rooms_grouped_by_ap_number:
        for ap_data_lst in levels_lst:
            ap_number = ap_data_lst[0][0]
            ap_level = ap_data_lst[0][2]
            ap_rooms_list = zip(*ap_data_lst)[1]
            final_rooms_list.append([ap_number, ap_level, ap_rooms_list])
    # Return simple list (ap_number, ap_level, ap_rooms_list)
    return final_rooms_list


def create_apartments_views_from_room_data_list(grouped_rooms_by_level):
    global input_building_code
    global apartment_card_view_type
    global apartment_card_scheme_view_type
    global view_name_prefix_string
    global view_scheme_name_prefix_string
    # Create New Apartment Views by Room Bb Box
    new_apartment_views_list = []
    for levels_lst in grouped_rooms_by_level:
        for element in levels_lst:
            # Get View Family Type of Plan
            apartment_number = element[0]
            room_lst = element[2]
            plan = element[1]
            view_type_id = apartment_card_view_type.Id
            scheme_view_type_id = apartment_card_scheme_view_type.Id
            level = room_lst[1].LevelId
            level_str_value = room_lst[1].Level.Name
            apartment_view_name = view_name_prefix_string + input_building_code + "." + level_str_value + "." + element[0]
            apartment_scheme_view_name = view_scheme_name_prefix_string + input_building_code + "." + level_str_value + "." + element[0]
            # Create Views
            TransactionManager.Instance.EnsureInTransaction(doc)
            room_view = ViewPlan.Create(doc, view_type_id, level)
            room_view.Name = apartment_view_name
            set_parameter_by_name(room_view, "BUDYNEK ETAP", input_building_code[0])
            set_parameter_by_name(room_view, "BUDYNEK NUMER", input_building_code[1])
            set_parameter_by_name(room_view, "BUDYNEK SEKCJA", element[0])
            set_parameter_by_name(room_view, "OBIEKT NUMER", apartment_view_name)
            scheme_view = ViewPlan.Create(doc, scheme_view_type_id, level)
            scheme_view.Name = apartment_scheme_view_name
            set_parameter_by_name(scheme_view, "BUDYNEK ETAP", input_building_code[0])
            set_parameter_by_name(scheme_view, "BUDYNEK NUMER", input_building_code[1])
            set_parameter_by_name(scheme_view, "BUDYNEK SEKCJA", element[0])
            set_parameter_by_name(scheme_view, "OBIEKT NUMER", apartment_scheme_view_name)
            # Get Room Bounding Box and Create New
            rMaxX_lst = []
            rMaxY_lst = []
            rMinX_lst = []
            rMinY_lst = []
            for room in room_lst:
                roomBB = room.get_BoundingBox(plan)
                rMax = roomBB.Max
                rMaxX = rMax.X
                rMaxY = rMax.Y
                rMin = roomBB.Min
                rMinX = rMin.X
                rMinY = rMin.Y
                rMaxX_lst.append(rMaxX)
                rMaxY_lst.append(rMaxY)
                rMinX_lst.append(rMinX)
                rMinY_lst.append(rMinY)
            # Create New Room Bounding Box
            newBB = BoundingBoxXYZ()
            newBBMaxX = max(rMaxX_lst)
            newBBMaxY = max(rMaxY_lst)
            newBBMinX = min(rMinX_lst)
            newBBMinY = min(rMinY_lst)
            offset = cm_to_internal(50)
            newMaxP = XYZ(newBBMaxX + offset, newBBMaxY + offset, 10)
            newMinP = XYZ(newBBMinX - offset, newBBMinY - offset, 10)
            newBB.Max = newMaxP
            newBB.Min = newMinP
            # Set the new Bounding Box
            room_view.CropBoxActive = True
            room_view.CropBoxVisible = False
            room_view.CropBox = newBB
            TransactionManager.Instance.TransactionTaskDone()
            new_apartment_views_list.append((room_view, scheme_view, level_str_value, apartment_number))
    return new_apartment_views_list


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


def filter_views_by_parameter_and_value(all_views, parameter_name, parameter_value):
    views = []
    for i, v in enumerate(all_views):
        # Create List of Views to collect
        views.append((i, v)) if v.IsTemplate == False and get_sh_parameter_value_by_name(v, parameter_name) == parameter_value else None
    return views


def view_types_list():
    view_types_list = [
        "FloorPlan",
    ]
    return view_types_list


def sub_elements_from_list(lst, ind):
    output = []
    for l in lst:
        output.append(l[ind])
    return output


def flatten(a):
    out = []
    for sublist in a:
        out.extend(sublist)
    return out


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


def create_sheets_from_list(views_list):
    global doc
    global title_block_type
    global view_name_prefix_string
    global view_scheme_name_prefix_string
    output = []
    for view_tuple in views_list:
        apartment_view = view_tuple[0]
        scheme_view = view_tuple[1]
        title_block_type_id = title_block_type.Id
        TransactionManager.Instance.EnsureInTransaction(doc)
        sheet = ViewSheet.Create(doc, title_block_type_id)
        apartment_viewport = Viewport.Create(doc, sheet.Id, apartment_view.Id, XYZ.Zero)
        scheme_viewport = Viewport.Create(doc, sheet.Id, scheme_view.Id, XYZ.Zero)
        apartment_number = get_sh_parameter_value_by_name(apartment_view, "OBIEKT NUMER")[2:]
        sheet_name = "KARTA MARKET. (MIESZKANIE NR " + get_sh_parameter_value_by_name(apartment_view, "OBIEKT NUMER")[4:] + ")"
        set_parameter_by_name(sheet, "Sheet Number", apartment_number)
        set_parameter_by_name(sheet, "Sheet Name", sheet_name)
        TransactionManager.Instance.TransactionTaskDone()
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
                viewport = set_location(sheet, viewport, 10.5, 17.64, 0)
            if view_scheme_name_prefix_string in viewport_name:
                # Rotate Viewport
                viewport = rotate_viewport_h(sheet, viewport)
                # Set New Scale
                viewport = set_new_scale(sheet, viewport, window_l=5.22, window_h=7.31)
                # Set Location of Scheme Viewport
                viewport = set_location(sheet, viewport, 9.97, 6.44, 0)
        output.append((sheet, apartment_viewport, scheme_viewport))
    return output


def create_sheets_from_list2(views_list):
    global doc
    global title_block_type
    global view_name_prefix_string
    global view_scheme_name_prefix_string
    output = []
    for view_tuple in views_list:
        apartment_view = view_tuple[0][0]
        scheme_view = view_tuple[0][1]
        apartment_view2 = view_tuple[1][0]
        scheme_view2 = view_tuple[1][1]
        title_block_type_id = title_block_type.Id
        TransactionManager.Instance.EnsureInTransaction(doc)
        sheet = ViewSheet.Create(doc, title_block_type_id)
        apartment_viewport = Viewport.Create(doc, sheet.Id, apartment_view.Id, XYZ.Zero)
        scheme_viewport = Viewport.Create(doc, sheet.Id, scheme_view.Id, XYZ.Zero)
        apartment_viewport2 = Viewport.Create(doc, sheet.Id, apartment_view2.Id, XYZ.Zero)
        scheme_viewport2 = Viewport.Create(doc, sheet.Id, scheme_view2.Id, XYZ.Zero)
        apartment_number = get_sh_parameter_value_by_name(apartment_view, "OBIEKT NUMER")[2:]
        sheet_name = "KARTA MARKET. (MIESZKANIE NR " + get_sh_parameter_value_by_name(apartment_view, "OBIEKT NUMER")[4:] + ")"
        set_parameter_by_name(sheet, "Sheet Number", apartment_number)
        set_parameter_by_name(sheet, "Sheet Name", sheet_name)
        TransactionManager.Instance.TransactionTaskDone()
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
                viewport = set_location(sheet, viewport, 10.5, 17.64, 0)
            if view_scheme_name_prefix_string in viewport_name:
                # Rotate Viewport
                viewport = rotate_viewport_h(sheet, viewport)
                # Set New Scale
                viewport = set_new_scale(sheet, viewport, window_l=5.22, window_h=7.31)
                # Set Location of Scheme Viewport
                viewport = set_location(sheet, viewport, 9.97, 6.44, 0)
        output.append((sheet, apartment_viewport, scheme_viewport, apartment_viewport2, scheme_viewport2))
    return output


# Inputs
input_building_code = IN[0]
apartment_card_vt = UnwrapElement(IN[1])
apartment_card_scheme_vt = UnwrapElement(IN[2])
title_block_type = UnwrapElement(IN[3])
view_name_prefix_string = IN[4]
view_scheme_name_prefix_string = view_name_prefix_string[:1] + "S" + view_name_prefix_string[1:]
# Code
doc = DocumentManager.Instance.CurrentDBDocument
# Get View Types by View Template
all_view_family_types = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
apartment_card_view_type = 0
apartment_card_scheme_view_type = 0
for element in all_view_family_types:
    apartment_card_bool_val = element.DefaultTemplateId == apartment_card_vt.Id
    if apartment_card_bool_val:
        # Apartment Card View Type Value
        apartment_card_view_type = element
    apartment_card_scheme_card_bool_val = element.DefaultTemplateId == apartment_card_scheme_vt.Id
    if apartment_card_scheme_card_bool_val:
        # Apartment Card Scheme View Type Value
        apartment_card_scheme_view_type = element
# Create Filtered Views List -> [views_lst]
views_list = filter_views_by_building_code(input_building_code)
# Create Filtered and Grouped Rooms List -> [(ap_number, ap_level, ap_rooms_list)]
rooms_list = group_rooms_by_apartment_number()
# Group Rooms List by Levels and Count Apartments appears on Level
grouped_rooms_by_level = group_by_sub_index_value(rooms_list, 1)
ap_numbers_on_level_list = []
for element in grouped_rooms_by_level:
    level_name = element[0][1]
    ap_numbers_on_level = len(element)
    ap_numbers_on_level_list.append((level_name, ap_numbers_on_level))
# List (level_name, ap_numbers_on_level)
ap_numbers_on_level_list = ap_numbers_on_level_list
# Replace Level name by Level element on sublist
for levels_lst in grouped_rooms_by_level:
    for element in levels_lst:
        for view in views_list:
            if element[1] == view.get_Parameter(BuiltInParameter.PLAN_VIEW_LEVEL).AsString():
                element[1] = view
# Create New Apartment Views by Room Bb Box And Scheme Views
new_views_tuples_list = create_apartments_views_from_room_data_list(grouped_rooms_by_level)
# Sort Views List
new_views_tuples_list = sorted(new_views_tuples_list, key=lambda x: x[2], reverse=False)
# Group By Level
new_views_tuples_list = group_by_sub_index_value(new_views_tuples_list, 2)
# Split List
# One Level apartments
one_levels_views_list = new_views_tuples_list[:-2]
one_levels_views_list = flatten(one_levels_views_list)
# Two Levels apartments
two_levels_views_list = new_views_tuples_list[-2:]
two_levels_views_list = flatten(two_levels_views_list)
two_levels_views_list = group_by_sub_index_value(two_levels_views_list, 3)
# Create Sheets
output = create_sheets_from_list(one_levels_views_list)
output2 = create_sheets_from_list2(two_levels_views_list)
# OUT
OUT = output, output2
