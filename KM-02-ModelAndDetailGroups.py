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


def to_cm(value):
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


def get_group_members(group_instance):
    member_ids = group_instance.GetMemberIds()
    elements_in_group_list = []
    for element_id in member_ids:
        element = doc.GetElement(element_id)
        elements_in_group_list.append(element)
    return elements_in_group_list


def filter_elements_by_type(elements_list, type_name):
    filtered_list =[]
    for element in elements_list:
        if element.GetType() == type_name:
            filtered_list.append(element)
    return filtered_list


def get_groups_members_from_data_list(data_list):
    grouped_group_members_list = []
    for groups_by_type_id in data_list:
        group_members_list = []
        for group_data in groups_by_type_id:
            group_inst = group_data[1]
            group_members = get_group_members(group_inst)
            room_members = filter_elements_by_type(group_members, Autodesk.Revit.DB.Architecture.Room)
            if len(room_members) > 0:
                group_members_list.append((group_data[3], room_members[0]))
        grouped_group_members_list.append(group_members_list)
    grouped_group_members_list = [x for x in grouped_group_members_list if x != []]
    return grouped_group_members_list


def rename_group_by_apartment_number(grouped_members_list):
    group_types_list = []
    for group_type_and_rooms in grouped_members_list:
        group_type = group_type_and_rooms[0][0]
        rooms_list = zip(*group_type_and_rooms)[1]
        ap_type_string = get_sh_parameter_value_by_name(rooms_list[0], "POMIESZCZENIE TYP")
        if "+" in ap_type_string:
            ap_number_list = []
            for room in rooms_list:
                ap_number = get_sh_parameter_value_by_name(room, "POMIESZCZENIE NR LOKALU")
                ap_number_list.append(ap_number)
            ap_number_string = "/".join(ap_number_list)
            group_type_full_name = "GRUPA MIESZKANIE " + ap_type_string + " " + ap_number_string
            TransactionManager.Instance.EnsureInTransaction(doc)
            group_type.Name = group_type_full_name
            TransactionManager.Instance.TransactionTaskDone()
            group_types_list.append(group_type)
    return group_types_list


def filter_group_instance_by_group_type_name(name_contains):
    global doc
    groups_list = FilteredElementCollector(doc).OfClass(Group).ToElements()
    groups_data_list = []
    for i, group_instance in enumerate(groups_list):
        group_name = group_instance.Name
        if name_contains in group_name:
            group_type_id = group_instance.GetTypeId()
            group_type = doc.GetElement(group_type_id)
            groups_data_list.append([group_instance, group_name, group_type, group_type_id])
    return groups_data_list


def filter_views_by_building_code(building_code):
    global doc
    global view_name_prefix_string
    # Collect All Views
    all_views = FilteredElementCollector(doc).OfCategory(
        BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
    # Filter Views by Parameters
    filtered_views = []
    for view in all_views:
        view_name = view.Name
        bool_string = view_name_prefix_string + building_code
        if bool_string in view_name:
            # List of filtered views
            filtered_views.append((view, view_name))
    # Sort Views List
    filtered_views = sorted(filtered_views, key=lambda x: x[1], reverse=False)
    # Get Clean Views List
    filtered_views = zip(*filtered_views)[0]
    return filtered_views


def show_attached_detail_group_to_model_group(views_list):
    global doc
    global attached_group_string
    detail_group_list = []
    for apartment_view in views_list:
        # Get Apartment Number from View Parameter
        ap_number = get_sh_parameter_value_by_name(apartment_view, "BUDYNEK SEKCJA")
        # Create Bounding Box from View CropBox
        bb = apartment_view.CropBox
        bb.Max = XYZ(bb.Max.X, bb.Max.Y, 1200)
        bb.Min = XYZ(bb.Min.X, bb.Min.Y, -25)
        outline = Outline(bb.Min, bb.Max)
        # Collect groups in Bounding Box
        filter = BoundingBoxIsInsideFilter(outline, False)
        collector = FilteredElementCollector(doc, apartment_view.Id).OfClass(Group).WherePasses(filter).ToElements()
        # Filter apartment group
        apartment_groups_list = []
        for group_instance in collector:
            group_instance_name = group_instance.Name
            if ap_number in group_instance_name:
                apartment_groups_list.append(group_instance)
        if len(apartment_groups_list) >= 1:
            apartment_group_from_view = apartment_groups_list[0]
        if apartment_group_from_view.GetType() == Autodesk.Revit.DB.Group:
            # Get available attached groups
            available_attached_groups = apartment_group_from_view.GetAvailableAttachedDetailGroupTypeIds()
            if len(available_attached_groups) >= 1:
                available_attached_groups_list = []
                for detail_group in available_attached_groups:
                    detail_group_name = Autodesk.Revit.DB.Element.Name.__get__(doc.GetElement(detail_group))
                    if attached_group_string in detail_group_name:
                        available_attached_groups_list.append(detail_group)
                if len(available_attached_groups_list) >= 1:
                    detail_groups_to_attach = available_attached_groups_list[0]
                    # Attach detail group
                    TransactionManager.Instance.EnsureInTransaction(doc)
                    apartment_group_from_view.ShowAttachedDetailGroups(apartment_view, detail_groups_to_attach)
                    TransactionManager.Instance.TransactionTaskDone()
                detail_group_list.append(available_attached_groups_list)
    return detail_group_list


# Inputs
select_elements = UnwrapElement(IN[0])
input_building_code = IN[1]
# Basic card prefix or Electrical/ plumbing fixtures card for ex. "V-M.", "V-MI."
view_name_prefix_string = IN[2]
# For ex. "MR-950-TAGS"
attached_group_string = IN[3]
# Code
doc = DocumentManager.Instance.CurrentDBDocument
# Create group data list from selection
group_data_list = create_data_list_from_selected_groups(select_elements)
# Create lists by Group Type
group_data_list = group_by_sub_index_value(group_data_list, 4)
# Get Groups Members
group_type_and_room_members = get_groups_members_from_data_list(group_data_list)
# Rename Group Type by rooms
group_types_lst = rename_group_by_apartment_number(group_type_and_room_members)
# Get And Filter Group Instances
apartments_groups = filter_group_instance_by_group_type_name("GRUPA MIESZKANIE")
# Create Filtered Views List -> [views_lst]
views_list = filter_views_by_building_code(input_building_code)
# Show Attached detail group to model group by list of views
detail_groups = show_attached_detail_group_to_model_group(views_list)
# OUT
OUT = detail_groups
