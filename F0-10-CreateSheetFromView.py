# P.DREIER ©  github.com/dreierpawel
import math
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

# Definitions


def create_parameters_list(parameter_string, parameter_prefix="BIMPL_"):
    parameter_string = parameter_string.upper()
    parameter_string = parameter_string.replace(" ", "_")
    parameter_string = parameter_string.split(",")
    output_parameters_list = []
    for i in parameter_string:
        i = parameter_prefix + i
        output_parameters_list.append(i)
    return output_parameters_list


def project_code(doc):
    var_project_code = doc.ProjectInformation.LookupParameter("PI_KOD_PROJEKTU").AsString()
    if str(var_project_code) == "None":
        var_project_code = "XX_XX"
    return var_project_code


def view_types_list():
    view_types_list = [
        "Elevation",
        "Section",
        "FloorPlan",
        "CeilingPlan",
        "Detail",
        "Legend",
        "Schedule",
        "ThreeD",
        "AreaPlan",
        "EngineeringPlan",
    ]
    return view_types_list


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


def update_views_and_sheets_code_format(doc, views_code_format, sheets_code_format):
    view_code_format_string = views_code_format.replace(",", "-").upper()
    sheet_code_format_string = sheets_code_format.replace(",", "-").upper()
    view_code_format_parameter = doc.ProjectInformation.LookupParameter("PI_FORMAT_KODU")
    sheet_code_format_parameter = doc.ProjectInformation.LookupParameter("PI_FORMAT_KODU_ARKUSZ")
    TransactionManager.Instance.EnsureInTransaction(doc)
    view_code_format_parameter.Set(view_code_format_string)
    sheet_code_format_parameter.Set(sheet_code_format_string)
    TransactionManager.Instance.TransactionTaskDone()
    return [view_code_format_string, sheet_code_format_string]


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


def get_parameter_by_parameter_list(element, parameter_list, empty_value=""):
    parameter_values = []
    for i in parameter_list:
        parameter_values.append(get_sh_parameter_value_by_name(element, i, empty_value))
    return parameter_values


def parameters_views_list(views, view_parameter_lst):
    views_parameters = []
    for i, view in enumerate(views):
        # Create view lists of parameters value
        views_parameters.append(get_parameter_by_parameter_list(view, view_parameter_lst, "NN"))
    return views_parameters


def set_parameter_by_name(element, parameter_name, value):
    if element.LookupParameter(parameter_name).IsReadOnly is False:
        p = element.LookupParameter(parameter_name)
        p.Set(value)
        return element
    else:
        return element


def replace_empty_parameter(element, parameter_names, value=""):
    for parameter_name in parameter_names:
        if str(get_sh_parameter_value_by_name(element, parameter_name)) == "":
            set_parameter_by_name(element, parameter_name, value)


def code_from_parameters(views_parameters, rev_location=-2):
    # Create File Code
    rev_symbol = "R"
    output = []
    for p in views_parameters:
        p = "-".join(p)
        p = p[:rev_location] + rev_symbol + p[rev_location:]
        output.append(p)
    return output


def code_views_list(views, project_code, view_parameter_lst):
    global doc
    views_parameters = []
    for i, view in enumerate(views):
        # Start Transaction
        TransactionManager.Instance.EnsureInTransaction(doc)
        # Get View Level
        if not view.ViewType == ViewType.Schedule or view.ViewType == ViewType.Legend:
            view_level = get_sh_parameter_value_by_name(view, "Associated Level", "NN")
            # Set Parameter BIMPL_POZIOM
            set_parameter_by_name(view, "BIMPL_POZIOM", view_level)
            # setParameterByName(view, "BIMPL_KOD_ZDATNOŚCI", "")
        else:
            view_level = get_sh_parameter_value_by_name(view, "BIMPL_POZIOM", "ZZZ")
            # Set Parameter BIMPL_POZIOM
            set_parameter_by_name(view, "BIMPL_POZIOM", view_level)
            # setParameterByName(view, "BIMPL_KOD_ZDATNOŚCI", "")
        # Set Empty Parameter...
        replace_empty_parameter(view, ["BIMPL_NUMER"], "01")
        replace_empty_parameter(view, ["BIMPL_REWIZJA"], "00")
        replace_empty_parameter(view, view_parameter_lst, "NN")
        # Create view lists of parameters value
        views_parameters.append(get_parameter_by_parameter_list(view, view_parameter_lst, "NN"))
        # Create Document Code Parameter
        code_lst = code_from_parameters(views_parameters)
        set_parameter_by_name(view, "BIMPL_KOD_DOKUMENTU", code_lst[i])
        # Set "BIMPL_KOD_PROJEKTU" Parameter
        set_parameter_by_name(view, "BIMPL_KOD_PROJEKTU", project_code)
        TransactionManager.Instance.TransactionTaskDone()
    # return views
    return views


def code_sheets_list(views, project_code, sheet_parameter_lst):
    global doc
    views_parameters = []
    for i, view in enumerate(views):
        # Start Transaction
        TransactionManager.Instance.EnsureInTransaction(doc)
        # Get View Level
        view_level = get_sh_parameter_value_by_name(view, "BIMPL_POZIOM", "NN")
        # Set Parameter BIMPL_POZIOM
        set_parameter_by_name(view, "BIMPL_POZIOM", view_level)
        # Set Empty Parameter...
        replace_empty_parameter(view, ["BIMPL_NUMER"], "01")
        replace_empty_parameter(view, ["BIMPL_REWIZJA"], "00")
        replace_empty_parameter(view, sheet_parameter_lst, "NN")
        # Create view lists of parameters value
        views_parameters.append(get_parameter_by_parameter_list(view, sheet_parameter_lst, "NN"))
        # Create Document Code Parameter
        code_lst = code_from_parameters(views_parameters)
        set_parameter_by_name(view, "BIMPL_KOD_DOKUMENTU", code_lst[i])
        # Set "BIMPL_KOD_PROJEKTU" Parameter
        set_parameter_by_name(view, "BIMPL_KOD_PROJEKTU", project_code)
        TransactionManager.Instance.TransactionTaskDone()
    return views


def sort_views_by_parameter(views_list, parameter_name):
    views_and_parameters_lst = []
    for view in views_list:
        view_parameter_value = get_sh_parameter_value_by_name(view, parameter_name)
        view_and_parameters = (view, view_parameter_value)
        views_and_parameters_lst.append(view_and_parameters)
    # Sort Levels list and Levels Parameters list by Elevation
    views_and_parameters_lst = sorted(views_and_parameters_lst, key=lambda x: x[1], reverse=False)
    # Get Levels list
    views_lst = zip(*views_and_parameters_lst)[0]
    return views_lst


def list_duplicates(source_list):
    tally = defaultdict(list)
    for i, item in enumerate(source_list):
        tally[item].append(i)
    return ((key, locs) for key, locs in tally.items() if len(locs) > 1)


def get_duplicates_and_index(source_list):
    output = []
    for duplicate in sorted(list_duplicates(source_list)):
        output.append(duplicate)
    return output


def add_duplicate_info_txt(source_list, added_txt = "COPY NR "):
    output = []
    for s in source_list:
        s = str(s)
        s = added_txt + s
        output.append(s)
    return output


def replace_duplicates_items(source):
    duplicates_and_index_list = get_duplicates_and_index(source)
    for i, elem in enumerate(duplicates_and_index_list):
        duplicate_item = elem[0]
        duplicate_indexes = elem[1]
        count_duplicates = len(duplicate_indexes)
        duplicates_range_list = list(range(1, count_duplicates + 1))
        duplicates_txt = add_duplicate_info_txt(duplicates_range_list)
        for d, z  in zip(duplicates_txt, duplicate_indexes):
            d = str(d) + "__" + str(duplicate_item)
            source[z] = d
    return source


def package_dictionary():
    package_dict = {
        "0": "PLAN ",
        "1": "RZUT ",
        "2": "RZUT STROPU ",
        "3": "PRZEKRÓJ NR ",
        "4": "ELEWACJA NR ",
        "5": "DETAL ",
        "6": "MODEL ",
        "7": "ZESTAWIENIE ",
        "8": "",
        "9": "LEGENDA "}
    return package_dict


def replace_duplicate_sheets_codes(all_sheets_list, code_views_parameters_short):
    sheets_number_lst = []
    for sheet in all_sheets_list:
        sheet_number = sheet.get_Parameter(BuiltInParameter.SHEET_NUMBER).AsString()
        sheets_number_lst.append(sheet_number)
    sheets_number_lst = code_views_parameters_short + sheets_number_lst
    replace_duplicates_items(sheets_number_lst)
    l = len(code_views_parameters_short)
    return sheets_number_lst[:l]


def rename_sheets_by_sh_parameters(all_sheets_list):
    global doc
    package_dict = package_dictionary()
    sheets_lst = []
    parameters_lst = []
    for sheet in all_sheets_list:
        # Detect Package Number and Collect Parameters Values
        parameter_value_first_char = package_dict.get(get_sh_parameter_value_by_name(sheet, "BIMPL_PAKIET")[0])
        parameter_value_first_char = str(parameter_value_first_char)
        if parameter_value_first_char != "None":
            # Set Parameters Values to View
            sheet_project_name_parameter_value = get_sh_parameter_value_by_name(sheet, "BIMPL_NAZWA_DOKUMENTU")
            sheet_project_code_parameter_value = get_sh_parameter_value_by_name(sheet, "BIMPL_KOD_DOKUMENTU")
            TransactionManager.Instance.EnsureInTransaction(doc)
            sheet_name = sheet.get_Parameter(BuiltInParameter.SHEET_NAME)
            sheet_name.Set(sheet_project_name_parameter_value)
            TransactionManager.Instance.TransactionTaskDone()
            sheets_lst.append(sheet)
            parameters_lst.append(sheet_project_code_parameter_value)
    sheet_numbers_list = replace_duplicates_items(parameters_lst)
    for sheet, sheet_project_code_parameter_value in zip(sheets_lst, sheet_numbers_list):
        TransactionManager.Instance.EnsureInTransaction(doc)
        sheet_number = sheet.get_Parameter(BuiltInParameter.SHEET_NUMBER)
        sheet_number.Set(sheet_project_code_parameter_value)
        TransactionManager.Instance.TransactionTaskDone()
    return sheets_lst


def sub_elements_from_list(lst, ind):
    output = []
    for l in lst:
        output.append(l[ind])
    return output


def get_parameter_by_name(element, parameter_name, default_empty_value=""):
    try:
        parameter_value = element.LookupParameter(parameter_name).AsString()
        if not str(parameter_value) == "None":
            return element.LookupParameter(parameter_name).AsString()
        else:
            return default_empty_value
    except:
        return default_empty_value


def filter_views_by_parameter_and_value(all_views, parameter_name, parameter_value):
    views = []
    for i, v in enumerate(all_views):
        # Create List of Views to collect
        views.append((i, v)) if v.IsTemplate == False and get_parameter_by_name(v, parameter_name) == parameter_value else None
    return views


def get_items_from_list(elements_list, indexs_list):
    output = []
    for i in indexs_list:
        output.append(elements_list[i])
    return output


def take_closest(my_list, my_number):
    new_lst = []
    for i in my_list:
        new_lst.append(i - my_number)
    absolute_lst = [abs(ele) for ele in new_lst]
    index = absolute_lst.index(min(absolute_lst))
    value = my_list[index]
    if value - my_number <= 0:
        try:
            value = my_list[index + 1]
        except IndexError:
            pass
    return value


def roundup(x, base=5):
    return base * math.ceil(x / base)


def to_cm(value):
    return UnitUtils.ConvertFromInternalUnits(value, UnitTypeId.Centimeters)


def cm_to_internal(value):
    return UnitUtils.ConvertToInternalUnits(value, UnitTypeId.Centimeters)


def list_to_internal(lst):
    output = []
    for l in lst:
        output.append(cm_to_internal(l))
    return output


def create_sheets_from_list(views, sheets_number_list, sheets_name_list, parameters_views_list, parameter_names_lst):
    global title_block_type
    output = []
    zip_list = zip(views, sheets_number_list, sheets_name_list, parameters_views_list)
    for viw, num, name, parameters_values_lst in zip_list:
        try:
            title_block_type_id = title_block_type.Id
            TransactionManager.Instance.EnsureInTransaction(doc)
            sheet = ViewSheet.Create(doc, title_block_type_id)
            new_viewport = Viewport.Create(doc, sheet.Id, viw.Id, XYZ.Zero)
            set_parameter_by_name(sheet, "BIMPL_KOD_DOKUMENTU", num)
            set_parameter_by_name(sheet, "BIMPL_NAZWA_DOKUMENTU", name)
            set_parameter_by_name(sheet, "BIMPL_ELEMENT_MODELU", str(viw.Id))
            view_scale = str(viw.get_Parameter(BuiltInParameter.VIEW_SCALE).AsInteger())
            view_scale = "1:" + view_scale
            set_parameter_by_name(sheet, "BIIMPL_SKALA", view_scale)
            set_parameter_by_name(sheet, "Sheet Number", num)
            set_parameter_by_name(sheet, "Sheet Name", name)
            for i, parameter_value in enumerate(parameters_values_lst):
                set_parameter_by_name(sheet, parameter_names_lst[i], parameter_value)
            TransactionManager.Instance.TransactionTaskDone()
            ### Get Parameters of Vieport
            newViewportCenterPoint = new_viewport.GetBoxCenter()
            new_viewport_outline = new_viewport.GetBoxOutline()
            new_viewport_bb_min_x = abs(new_viewport_outline.MinimumPoint.X)
            new_viewport_bb_min_y = abs(new_viewport_outline.MinimumPoint.Y)
            new_viewport_bb_max_x = abs(new_viewport_outline.MaximumPoint.X)
            new_viewport_bb_max_y = abs(new_viewport_outline.MaximumPoint.Y)
            # Vieport Dimensions
            new_viewport_length = new_viewport_bb_min_x + new_viewport_bb_max_x
            new_viewport_height = new_viewport_bb_min_y + new_viewport_bb_max_y
            # Get Title Block Instance
            title_block_instance = FilteredElementCollector(doc, sheet.Id).OfClass(FamilyInstance).OfCategory(BuiltInCategory.OST_TitleBlocks).FirstElement()
            # Get Title Block Instance Dimensions
            sheet_length = int(to_cm(title_block_instance.LookupParameter("ARKUSZ DŁUGOŚĆ").AsDouble()))
            sheet_height = int(to_cm(title_block_instance.LookupParameter("ARKUSZ WYSOKOŚĆ").AsDouble()))
            # Change Title Block Instance H
            printer_height_list = [29.7, 42, 59.4, 84.1, 91.4]
            new_sheet_height = take_closest(printer_height_list, to_cm(new_viewport_height))
            # Change Title Block Instance L
            title_block_frame_length = 11
            new_sheet_length = roundup(to_cm(new_viewport_length)) + title_block_frame_length
            # Set Title Block dimensions
            TransactionManager.Instance.EnsureInTransaction(doc)
            set_parameter_by_name(title_block_instance, "ARKUSZ DŁUGOŚĆ", cm_to_internal(new_sheet_length))
            set_parameter_by_name(title_block_instance, "ARKUSZ WYSOKOŚĆ", cm_to_internal(new_sheet_height))
            ElementTransformUtils.MoveElement(doc, title_block_instance.Id, XYZ.Zero)
            move_distance = cm_to_internal(29.7 - (0.5 * new_sheet_length) - 4)
            new_viewport.SetBoxCenter(XYZ(move_distance, cm_to_internal(new_sheet_height / 2), 0))
            TransactionManager.Instance.TransactionTaskDone()
            output.append((sheet, new_viewport, title_block_instance))
        except False:
            output.append("Can't create Sheet")
    return output


# CODE
doc = DocumentManager.Instance.CurrentDBDocument
all_views = [doc.ActiveView]
# 01 - Get Project Code Format from "BIMPL_KOD_PROJEKTU" for ex. "20_02"
project_code = project_code(doc)
# 01 - Get Sheets Code Format Parameters
sheets_code_format = doc.ProjectInformation.LookupParameter("PI_FORMAT_KODU_ARKUSZ").AsString()
sheets_code_format = sheets_code_format.replace("-", ",").upper()
# 02 - Collect all Sheets
all_sheets_list = filtered_views_by_type(doc, sheet_type_list())
# 02 - Import List of Parameters to Code for Sheets and Create Parameters List for Views
sheet_parameter_short_lst = create_parameters_list(sheets_code_format)
sheet_parameter_long_lst = sheet_parameter_short_lst + create_parameters_list("Kod dokumentu,Nazwa dokumentu")
# 03 - Code all views and sheets & Sort by Parameter - "BIMPL_PAKIET"
all_sheets_list = sort_views_by_parameter(code_sheets_list(all_sheets_list, project_code, sheet_parameter_short_lst), "BIMPL_PAKIET")
# Get parameters from view + use sheet parameters long list
views_parameters_short = parameters_views_list(all_views, sheet_parameter_short_lst)
views_parameters_long = parameters_views_list(all_views, sheet_parameter_long_lst)
code_views_parameters_short = code_from_parameters(views_parameters_short)
# Replace duplicates names
code_views_parameters_short = replace_duplicate_sheets_codes(all_sheets_list, code_views_parameters_short)
# Inputs to Create Sheets
views_list = all_views
parameters_views_list = views_parameters_short
sheets_number_list = code_views_parameters_short
sheets_name_list = sub_elements_from_list(views_parameters_long, -1)
title_block_type = UnwrapElement(IN[0])
parameters_names_list = sheet_parameter_long_lst
sheets_role = all_views[0].LookupParameter("BIMPL_ROLA").AsString()
#
par_name_lLst = parameters_names_list[:-2]
# Get Document
doc_unit_type = doc.GetUnits().GetFormatOptions(SpecTypeId.Length).GetUnitTypeId()
# Filter Views By Parameter
parameter_name = "BIMPL_ROLA"
role = sheets_role
views = filter_views_by_parameter_and_value(views_list, parameter_name, role)
#
index_list = sub_elements_from_list(views, 0)
#
parameters_views_list = get_items_from_list(parameters_views_list, index_list)
sheets_number_list = get_items_from_list(sheets_number_list, index_list)
sheets_name_list = get_items_from_list(sheets_name_list, index_list)
#
views = sub_elements_from_list(views, 1)
# Create Sheets From List
output = create_sheets_from_list(views, sheets_number_list, sheets_name_list, parameters_views_list, par_name_lLst)
# Assign your output to the OUT variable.
OUT = output
