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

# Definitions


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


def create_data_list_from_selected_groups(elements):
    # filter groups from selection
    groups_list = []
    for e in elements:
        if e.GetType() == Autodesk.Revit.DB.Group:
            groups_list.append(e)
    # Create Groups Data List
    groups_data_list = []
    for i, group_instance in enumerate(groups_list):
        group_name = group_instance.Name
        group_type_id = group_instance.GetTypeId()
        group_type = doc.GetElement(group_type_id)
        groups_data_list.append([i, group_instance, group_name, group_type, group_type_id])
    return groups_data_list


def filter_elements_by_type(elements_list, type_name):
    filtered_list =[]
    for element in elements_list:
        if element.GetType() == type_name:
            filtered_list.append(element)
    return filtered_list


def group_rooms_by_apartment_number():
    global doc
    # Collect All Rooms
    collector = FilteredElementCollector(doc).WherePasses(Architecture.RoomFilter()).ToElements()
    apartment_rooms = []
    apartment_rooms2 = []
    for room in collector:
        # Filter rooms list by room type parameter
        bool_test = "+" in room.LookupParameter("POMIESZCZENIE TYP").AsString()
        bool_test2 = "WEW" in get_sh_parameter_value_by_name(room,"POMIESZCZENIE WEW ZEW")
        if bool_test and bool_test2:
            room_ap_number = room.LookupParameter("POMIESZCZENIE NR LOKALU").AsString()
            room_level_name = room.Level.Name
            room_phase_name = doc.GetElement(room.get_Parameter(BuiltInParameter.ROOM_PHASE).AsElementId()).Name
            apartment_rooms.append((room_ap_number, room, room_level_name, room_phase_name))
    # Sort Rooms List (room_ap_number, room, room_level_name, room_phase_name)
    # Sort by ap_number
    apartment_rooms = sorted(apartment_rooms, key=lambda x: x[0], reverse=False)
    # Sort by ap_level
    apartment_rooms = sorted(apartment_rooms, key=lambda x: x[2], reverse=False)
    apartment_rooms_group_by_levels = group_by_sub_index_value(apartment_rooms, 2)
    # Filter Rooms By Phase (room_ap_number, room, room_level_name, room_phase_name)
    filtered_rooms = []
    filtered_rooms2 = []
    for levels_lst in apartment_rooms_group_by_levels[:-2]:
        for room in levels_lst:
            if "PK" in room[3]:
                filtered_rooms.append(room)
    for levels_lst in apartment_rooms_group_by_levels[-2:]:
        for room in levels_lst:
            if "PB" in room[3]:
                filtered_rooms2.append(room)
    joined_filtered_rooms = filtered_rooms + filtered_rooms2
    # Group Rooms By Apartment Number (room_ap_number, room, room_level_name, room_phase_name)
    rooms_grouped_by_ap_number = group_by_sub_index_value(joined_filtered_rooms, 0)
    # Group Rooms By Levels (room_ap_number, room, room_level_name, room_phase_name)
    rooms_grouped_by_levels = []
    for rooms_data in rooms_grouped_by_ap_number:
        room_data_by_level = []
        room_grouped_by_apartment_number = group_by_sub_index_value(rooms_data, 2)
        room_data_by_level.append(room_grouped_by_apartment_number)
        rooms_grouped_by_levels.append(room_data_by_level)
    rooms_grouped_by_levels = zip(*rooms_grouped_by_levels)[0]
    # Simplify Rooms List
    final_rooms_list = []
    for ap_data_lst in rooms_grouped_by_levels:
        ap_number = ap_data_lst[0][0][0]
        ap_level = extract(extract(ap_data_lst,0),2)
        ap_phase = list(set(extract(extract(ap_data_lst,0),3)))
        room_lst = []
        for sub_ap_data_lst in ap_data_lst:
            room = zip(*sub_ap_data_lst)[1]
            room_lst.append(room)
        ap_rooms_list = flatten(room_lst)
        final_rooms_list.append([ap_number, ap_level, len(ap_rooms_list), ap_rooms_list[0], ap_phase])
    return final_rooms_list


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


def create_parameters_list(parameter_string):
    parameter_string = parameter_string.upper()
    #parameter_string = parameter_string.replace(" ", "_")
    parameter_string = parameter_string.split(",")
    return parameter_string


def storey_dictionary():
    d = {'01': 'Parter',
         '02': '01',
         '03': '02',
         '04': '03',
         '05': '04',
         '06': '05',
         '07': '06',
         '08': '07',
         '09': '08',
         }
    return d


def storey_replacer(storey_string):
    storey_dict = storey_dictionary()
    new_storey_string = ""
    for k, v in storey_dict.items():
        if storey_string == k:
            new_storey_string = storey_string.replace(k, v)
    return new_storey_string


def storey_subtitle_replacer(storey_data):
    if "Parter" != storey_data:
        storey_data = "Piętro " + storey_data
    return storey_data


# Inputs
input_building_code = IN[0]
# Basic card prefix or Electrical/ plumbing fixtures card for ex. "V-M.", "V-MI."
view_name_prefix_string = IN[1]
get_parameters_values_list = create_parameters_list(IN[2])
set_parameters_values_list = create_parameters_list(IN[3])
# Code
doc = DocumentManager.Instance.CurrentDBDocument
# Collect apartments rooms data list
rooms_data_list = group_rooms_by_apartment_number()
# Collect sheet list
sheet_list = filtered_views_by_type(doc, sheet_type_list())
sheet_name_prefix_str = view_name_prefix_string[2:]+""+input_building_code
# Filter Sheet List
filtered_sheets = []
for sheet in sheet_list:
    sheet_number = sheet.get_Parameter(BuiltInParameter.SHEET_NUMBER).AsString()
    if sheet_name_prefix_str in sheet_number:
        filtered_sheets.append((sheet_number, sheet))
filtered_sheets = sorted(filtered_sheets, key=lambda x: x[0], reverse=False)
filtered_sheets = zip(*filtered_sheets)[1]
#
joined_data_list = []
for sheet, rooms_data in zip(filtered_sheets, rooms_data_list):
    rooms_data = [sheet] + rooms_data
    rooms_data[5] = rooms_data[5][0]
    rooms_data[2] = rooms_data[2][0]
    # Data list : 0:Sheet, 1: Apartment Number, 2:Level Name string, 3: Interior Rooms Number integer 4: Room, 5: Phase
    joined_data_list.append(rooms_data)
# Get & Set Parameters

temp = []
for data_list in joined_data_list:
    sheet = data_list[0]
    room = data_list[4]
    quantity_of_rooms = data_list[3]
    level = data_list[2]
    storey = storey_replacer(level)
    apartment_parameters_values_lst = []
    for parameter_string in get_parameters_values_list:
        parameter_value = get_sh_parameter_value_by_name(room, parameter_string)
        apartment_parameters_values_lst.append(parameter_value)
    data_list = apartment_parameters_values_lst + [quantity_of_rooms] + [storey]
    for parameter_value, parameter_name_to_set in zip(data_list, set_parameters_values_list):
        TransactionManager.Instance.EnsureInTransaction(doc)
        set_parameter_by_name(sheet, parameter_name_to_set, parameter_value)
        TransactionManager.Instance.TransactionTaskDone()
    title_block_on_sheet = FilteredElementCollector(doc, sheet.Id).OfCategory(BuiltInCategory.OST_TitleBlocks).FirstElement()
    TransactionManager.Instance.EnsureInTransaction(doc)
    set_parameter_by_name(sheet, "BUDYNEK ETAP", input_building_code[0])
    set_parameter_by_name(sheet, "BUDYNEK NUMER", input_building_code[1])
    set_parameter_by_name(sheet, "BUDYNEK POZIOM", level)
    set_parameter_by_name(sheet, "KARTA PIĘTRO PODTYTUŁ", storey_subtitle_replacer(storey))
    set_parameter_by_name(title_block_on_sheet, "KARTA LICZBA POMIESZCZEŃ", quantity_of_rooms)
    # Get Viewport Orientation
    viewport_list = FilteredElementCollector(doc, sheet.Id).OfClass(Viewport).ToElements()
    selected_viewport = 0
    for viewport in viewport_list:
        if view_name_prefix_string in doc.GetElement(viewport.ViewId).Name:
            selected_viewport = viewport
    # Set Viewport Orientation to Title Block
    if selected_viewport.get_Parameter(BuiltInParameter.VIEWPORT_ATTR_ORIENTATION_ON_SHEET) == 0:
        set_parameter_by_name(title_block_on_sheet, "V0", True)
    if not selected_viewport.get_Parameter(BuiltInParameter.VIEWPORT_ATTR_ORIENTATION_ON_SHEET) == 0:
        set_parameter_by_name(title_block_on_sheet, "V0", False)
    set_parameter_by_name(title_block_on_sheet, "KARTA POW LOKALU", get_sh_parameter_value_by_name(sheet, "KARTA POW LOKALU" ))
    TransactionManager.Instance.TransactionTaskDone()
    temp.append(data_list)
# OUT
OUT = temp
