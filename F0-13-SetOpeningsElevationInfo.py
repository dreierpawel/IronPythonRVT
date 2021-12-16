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


def doc():
    return DocumentManager.Instance.CurrentDBDocument


def to_cm(value):
    return UnitUtils.ConvertFromInternalUnits(value, UnitTypeId.Centimeters)


def flatten(t):
    return [item for sublist in t for item in sublist]


def get_instance(filter):
    return filter.WhereElementIsNotElementType().ToElements()


def get_family(instance):
    global doc
    id = instance.GetTypeId()
    family = doc.GetElement(id)
    family_name = family.Family.Name
    return (family, family_name)


def filter_instance_by_family_name(instance, string_in_name):
    family_name = get_family(instance)[1]
    if string_in_name in family_name:
        return instance
    else:
        pass


def get_family_len_parameter_by_name(instance, parameter_name):
    family = get_family(instance)[0]
    parameter_value = to_cm(family.LookupParameter(parameter_name).AsDouble())
    return parameter_value


def get_family_txt_parameter_by_name(instance, parameter_name):
    family = get_family(instance)[0]
    parameter_value = family.LookupParameter(parameter_name).AsString()
    return parameter_value


def get_instance_location_point(instance):
    return to_cm(instance.Location.Point.Z)


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


def take_level_name(element, levels_and_elevations_lst):
    p = get_instance_location_point(element)
    levels_lst = zip(*levels_and_elevations_lst)[0]
    elev_lst = zip(*levels_and_elevations_lst)[1]
    if p <= min(elev_lst):
        return (levels_lst[0].Name)
    else:
        if p <= min(elev_lst):
            i = elev_lst.index(min(elev_lst))
            return levels_lst[i].Name
        else:
            elev_h = take_closest(elev_lst, p)
            test = elev_h - p
            if test <= 0:
                i = elev_lst.index(take_closest(elev_lst, p))
                return levels_lst[i].Name
            else:
                i = elev_lst.index(take_closest(elev_lst, p, -1))
                return levels_lst[i].Name


def elev_replacer(value):
    value = str("+" + value.replace(".", ","))
    value = value + ""
    value = value.replace("+-", "-")
    return value


doc = doc()
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application
uidoc = uiapp.ActiveUIDocument

# collect all Levels in the project
all_levels_list = FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType().ToElements()

# Sort Lvels
levels_and_parameters_lst = []
for level in all_levels_list:
    level_elevation = to_cm(level.Elevation)
    levels_and_parameters_lst.append((level, level_elevation))
# Sort Levels and parameters list by elevation
levels_and_parameters_lst = sorted(levels_and_parameters_lst, key=lambda x: x[1], reverse=False)
# Get first elements from sublist
levels_lst = zip(*levels_and_parameters_lst)[0]

# Windows & Doors Instance List
windows = get_instance(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows))
doors = get_instance(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors))
windows_doors = flatten([windows, doors])

for element in windows_doors:
    location_h = get_instance_location_point(element)
    opening_h = get_family_len_parameter_by_name(element, "OTWÓR WYSOKOŚĆ")
    opening_rough_h = get_family_len_parameter_by_name(element, "OTWÓR ŻELBET WYSOKOŚĆ")
    floor_h = get_family_len_parameter_by_name(element, "POSADZKA GRUBOŚĆ WARSTW")
    # Get Parameters
    top_value = str((location_h + opening_rough_h) / 100)
    top_value = elev_replacer(top_value)
    bottom_value = str((location_h) / 100)
    bottom_value = elev_replacer(bottom_value)
    bottom_f_value = str((location_h + floor_h) / 100)
    bottom_f_value = elev_replacer(bottom_f_value)
    elev_top = element.LookupParameter("OTWÓR RZĘDNA WIERZCHU")
    elev_bottom = element.LookupParameter("OTWÓR RZĘDNA SPODU")
    elev_f_bottom = element.LookupParameter("OTWÓR RZĘDNA SPODU WYKOŃCZENIE")
    level = element.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)
    level_name = doc.GetElement(level.AsElementId()).Name
    # Set Parameters Value
    TransactionManager.Instance.EnsureInTransaction(doc)
    elev_top.Set(top_value)
    elev_bottom.Set(bottom_value)
    elev_f_bottom.Set(bottom_f_value)
    element.LookupParameter("NADPROŻE RZĘDNA").Set(top_value)
    element.LookupParameter("BIMPL_POZIOM").Set(level_name)
    element.LookupParameter("BIMPL_ROLA").Set("AR")
    try:
        element.LookupParameter("OTWÓR RZĘDNA WIERZCHU WYKOŃCZENIE").Set("")
    except:
        pass
    TransactionManager.Instance.TransactionTaskDone()

# Openings Instance List
speciality_equipment = get_instance(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_SpecialityEquipment))
structural_framing = get_instance(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralFraming))
elements = flatten([speciality_equipment, structural_framing])
openings = []
for e in elements:
    try:
        parameter_value = get_family_txt_parameter_by_name(e, "BIMPL_TYP")
        if "OT." in parameter_value:
            openings.append(e)
    except:
        pass

output = []

for opening in openings:
    # Get Parameters
    opening_system = get_family_txt_parameter_by_name(opening, "BIMPL_SYSTEM")
    opening_type = get_family_txt_parameter_by_name(opening, "BIMPL_TYP")
    if opening_system == "STR":
        level = opening.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)
        level_name = doc.GetElement(level.AsElementId()).Name
    else:
        location_h = get_instance_location_point(opening)
        level_name = take_level_name(opening, levels_and_parameters_lst)
        if "T.O" in opening_type:
            # Oval openings in walls
            opening_fi = to_cm(opening.LookupParameter("OTWÓR ŚREDNICA").AsDouble())
            fi_value = str(round((location_h + (opening_fi / 2)) / 100, 2))
            TransactionManager.Instance.EnsureInTransaction(doc)
            op_elevation = opening.LookupParameter("OTWÓR RZĘDNA OSI")
            op_elevation.Set(elev_replacer(fi_value))
            opening.LookupParameter("OTWÓR RZĘDNA SPODU").Set("")
            TransactionManager.Instance.TransactionTaskDone()
        else:
            # Rectang openings in walls
            opening_h = to_cm(opening.LookupParameter("OTWÓR WYSOKOŚĆ").AsDouble())
            elev_top = str(round((location_h + (opening_h)) / 100, 2))
            elev_bottom = str(round(location_h / 100, 2))
            TransactionManager.Instance.EnsureInTransaction(doc)
            op_top_elev = opening.LookupParameter("OTWÓR RZĘDNA WIERZCHU")
            op_top_elev.Set(elev_replacer(elev_top))
            op_bottom_elev = opening.LookupParameter("OTWÓR RZĘDNA SPODU")
            op_bottom_elev.Set(elev_replacer(elev_bottom))
            TransactionManager.Instance.TransactionTaskDone()
    # Set Parameters
    TransactionManager.Instance.EnsureInTransaction(doc)
    opening.LookupParameter("BIMPL_POZIOM").Set(level_name)
    # opening.LookupParameter("OTWÓR RZĘDNA WIERZCHU WYKOŃCZENIE").Set("")
    TransactionManager.Instance.TransactionTaskDone()

# Elevators Instance List
caseworks = get_instance(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Casework))
elevators = []
for c in caseworks:
    elevator = filter_instance_by_family_name(c, "WINDA")
    if not str(elevator) == "None":
        elevators.append(elevator)

for element in elevators:
    location_h = get_instance_location_point(element)
    opening_h = get_family_len_parameter_by_name(element, "OTWÓR WYSOKOŚĆ")
    opening_rough_h = get_family_len_parameter_by_name(element, "OTWÓR ŻELBET WYSOKOŚĆ")
    floor_h = get_family_len_parameter_by_name(element, "POSADZKA GRUBOŚĆ WARSTW")
    # Get Parameters
    top_value = str((location_h + opening_rough_h) / 100)
    top_value = elev_replacer(top_value)
    bottom_value = str((location_h) / 100)
    bottom_value = elev_replacer(bottom_value)
    bottom_f_value = str((location_h + floor_h) / 100)
    bottom_f_value = elev_replacer(bottom_f_value)
    elev_top = element.LookupParameter("OTWÓR RZĘDNA WIERZCHU")
    elev_bottom = element.LookupParameter("OTWÓR RZĘDNA SPODU")
    elev_f_bottom = element.LookupParameter("OTWÓR RZĘDNA SPODU WYKOŃCZENIE")
    level = element.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)
    level_name = doc.GetElement(level.AsElementId()).Name
    # Set Parameters Value
    TransactionManager.Instance.EnsureInTransaction(doc)
    elev_top.Set(top_value)
    elev_bottom.Set(bottom_value)
    elev_f_bottom.Set(bottom_f_value)
    element.LookupParameter("BIMPL_POZIOM").Set(level_name)
    element.LookupParameter("BIMPL_ROLA").Set("AR")
    element.LookupParameter("OTWÓR RZĘDNA WIERZCHU WYKOŃCZENIE").Set("")
    TransactionManager.Instance.TransactionTaskDone()

all_elements = flatten([windows, doors, elevators, openings])

for e in all_elements:
    e.LookupParameter("BIMPL_NUMER").Set(str(e.Id))

OUT = all_elements
