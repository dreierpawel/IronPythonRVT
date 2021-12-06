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


def get_sh_parameter_value_by_name(element, parameter_name, empty_value=""):
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
                parameter_value = empty_value
    except Exception:
        parameter_value = False
    return parameter_value


def get_parameter_by_parameter_list(element, parameter_list, empty_value=""):
    parameter_values = []
    for i in parameter_list:
        parameter_values.append(get_sh_parameter_value_by_name(element, i, empty_value))
    return parameter_values


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


def list_duplicates(source_List):
    tally = defaultdict(list)
    for i, item in enumerate(source_List):
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


def rename_views_by_sh_parameters(all_views_list):
    global doc
    package_dict = package_dictionary()
    views_lst = []
    parameters_lst = []
    for view in all_views_list:
        # Detect Package Number and Collect Parameters Values
        parameter_value_first_char = package_dict.get(get_sh_parameter_value_by_name(view, "BIMPL_PAKIET")[0])
        parameter_value_first_char = str(parameter_value_first_char)
        if parameter_value_first_char != "None":
            view_name_parameter_value = get_sh_parameter_value_by_name(view, "View Name")
            view_name_parameter_value = view_name_parameter_value.split("(")
            if len(view_name_parameter_value) == 2:
                view_name_parameter_value = view_name_parameter_value[1]
                view_name_parameter_value = " (" + view_name_parameter_value
            else:
                view_name_parameter_value = ""
            test = get_sh_parameter_value_by_name(view, "BIMPL_POZIOM") == "NN" or get_sh_parameter_value_by_name(view, "BIMPL_POZIOM") == "WK"
            if not test:
                view_level_parameter_value = get_sh_parameter_value_by_name(view, "BIMPL_POZIOM")
            else:
                view_level_parameter_value = get_sh_parameter_value_by_name(view, "BIMPL_NUMER")
            view_project_code_parameter_value = get_sh_parameter_value_by_name(view, "BIMPL_KOD_DOKUMENTU")
            view_joined_name = parameter_value_first_char + view_level_parameter_value + view_name_parameter_value
            view_full_name = view_project_code_parameter_value + "-" + view_joined_name
            # Set Parameters Values to View
            TransactionManager.Instance.EnsureInTransaction(doc)
            set_parameter_by_name(view, "BIMPL_NAZWA_DOKUMENTU", view_joined_name)
            set_parameter_by_name(view, "BIMPL_KOD_DOKUMENTU", view_project_code_parameter_value)
            TransactionManager.Instance.TransactionTaskDone()
            views_lst.append(view)
            parameters_lst.append(view_full_name)
    all_views_names_list = replace_duplicates_items(parameters_lst)
    for view, name in zip(views_lst, all_views_names_list):
        TransactionManager.Instance.EnsureInTransaction(doc)
        view.Name = name
        TransactionManager.Instance.TransactionTaskDone()
    return views_lst


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


# CODE
doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application
uidoc = uiapp.ActiveUIDocument
# 01 - Get Project Code Format from "BIMPL_KOD_PROJEKTU" for ex. "20_02"
project_code = project_code(doc)
# 01 - Get Views Code Format Parameters
views_code_format = doc.ProjectInformation.LookupParameter("PI_FORMAT_KODU").AsString()
views_code_format = views_code_format.replace("-", ",").upper()
# 01 - Get Sheets Code Format Parameters
sheets_code_format = doc.ProjectInformation.LookupParameter("PI_FORMAT_KODU_ARKUSZ").AsString()
sheets_code_format = sheets_code_format.replace("-", ",").upper()
# 02 - Collect all Views
all_views_list = filtered_views_by_type(doc, view_types_list())
# 02 - Collect all Sheets
all_sheets_list = filtered_views_by_type(doc, sheet_type_list())
# 02 - Import List of Parameters to Code for Views and Create Parameters List for Views
view_parameter_lst = create_parameters_list(views_code_format)
# 02 - Import List of Parameters to Code for Sheets and Create Parameters List for Views
sheet_parameter_lst = create_parameters_list(sheets_code_format)
# 02 - Update Views & Sheets Codes Formats ex. PROJEKT-FAZA-BRANŻĄ-...
update_views_and_sheets_code_format(doc, views_code_format, sheets_code_format)
# 03 - Code all views and sheets & Sort by Parameter - "BIMPL_PAKIET"
all_views_list = sort_views_by_parameter(code_views_list(all_views_list, project_code, view_parameter_lst ), "BIMPL_PAKIET")
all_sheets_list = sort_views_by_parameter(code_sheets_list(all_sheets_list, project_code, sheet_parameter_lst), "BIMPL_PAKIET")
# 04 - Rename Views by Parameters
all_views_list = rename_views_by_sh_parameters(all_views_list)
# 05 - Rename Sheets by Parameters
all_sheets_list = rename_sheets_by_sh_parameters(all_sheets_list)
# OUT
OUT = all_views_list, all_sheets_list
