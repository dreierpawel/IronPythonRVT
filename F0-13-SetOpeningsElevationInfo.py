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


def toCM(value):
    return UnitUtils.ConvertFromInternalUnits(value, UnitTypeId.Centimeters)


def flatten(t):
    return [item for sublist in t for item in sublist]


def getInstance(filter):
    return filter.WhereElementIsNotElementType().ToElements()


def getFamily(instance):
    # doc = doc()
    id = instance.GetTypeId()
    family = doc.GetElement(id)
    family_name = family.Family.Name
    return (family, family_name)


def filterInstanceByFamilyName(instance, stringInName):
    family_name = getFamily(instance)[1]
    if stringInName in family_name:
        return instance
    else:
        pass


def getFamilyLenParameterByName(instance, parameterName):
    family = getFamily(instance)[0]
    parameter_value = toCM(family.LookupParameter(parameterName).AsDouble())
    return parameter_value


def getFamilyTxtParameterByName(instance, parameterName):
    family = getFamily(instance)[0]
    parameter_value = family.LookupParameter(parameterName).AsString()
    return parameter_value


def getInstanceLocationPoint(instance):
    return toCM(instance.Location.Point.Z)


def takeClosest(myList, myNumber, index_n=0):
    newlst = []
    for i in myList:
        newlst.append(i - myNumber)
    abslst = [abs(ele) for ele in newlst]
    index = abslst.index(min(abslst))
    value = myList[index + index_n]
    return value


def takeLevelName(element, levels_and_elevations_lst):
    p = getInstanceLocationPoint(element)
    levels_lst = zip(*levels_and_elevations_lst)[0]
    elev_lst = zip(*levels_and_elevations_lst)[1]
    if p <= min(elev_lst):
        return (levels_lst[0].Name)
    else:
        if p <= min(elev_lst):
            i = elev_lst.index(min(elev_lst))
            return levels_lst[i].Name
        else:
            elev_h = takeClosest(elev_lst, p)
            test = elev_h - p
            if test <= 0:
                i = elev_lst.index(takeClosest(elev_lst, p))
                return levels_lst[i].Name
            else:
                i = elev_lst.index(takeClosest(elev_lst, p, -1))
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
    level_elevation = toCM(level.Elevation)
    levels_and_parameters_lst.append((level, level_elevation))
# Sort Levels and parameters list by elevation
levels_and_parameters_lst = sorted(levels_and_parameters_lst, key=lambda x: x[1], reverse=False)
# Get first elements from sublist
levels_lst = zip(*levels_and_parameters_lst)[0]

# Windows & Doors Instance List
windows = getInstance(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows))
doors = getInstance(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors))
windows_doors = flatten([windows, doors])

for element in windows_doors:
    location_h = getInstanceLocationPoint(element)
    opening_h = getFamilyLenParameterByName(element, "OTWÓR WYSOKOŚĆ")
    opening_rough_h = getFamilyLenParameterByName(element, "OTWÓR ŻELBET WYSOKOŚĆ")
    floor_h = getFamilyLenParameterByName(element, "POSADZKA GRUBOŚĆ WARSTW")
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
speciality_equipment = getInstance(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_SpecialityEquipment))
structural_framing = getInstance(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralFraming))
elements = flatten([speciality_equipment, structural_framing])
openings = []
for e in elements:
    try:
        parameter_value = getFamilyTxtParameterByName(e, "BIMPL_TYP")
        if "OT." in parameter_value:
            openings.append(e)
    except:
        pass

output = []

for opening in openings:
    # Get Parameters
    opening_system = getFamilyTxtParameterByName(opening, "BIMPL_SYSTEM")
    opening_type = getFamilyTxtParameterByName(opening, "BIMPL_TYP")
    if opening_system == "STR":
        level = opening.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)
        level_name = doc.GetElement(level.AsElementId()).Name
    else:
        location_h = getInstanceLocationPoint(opening)
        level_name = takeLevelName(opening, levels_and_parameters_lst)
        if "T.O" in opening_type:
            # Oval openings in walls
            opening_fi = toCM(opening.LookupParameter("OTWÓR ŚREDNICA").AsDouble())
            fi_value = str(round((location_h + (opening_fi / 2)) / 100, 2))
            TransactionManager.Instance.EnsureInTransaction(doc)
            op_elevation = opening.LookupParameter("OTWÓR RZĘDNA OSI")
            op_elevation.Set(elev_replacer(fi_value))
            opening.LookupParameter("OTWÓR RZĘDNA SPODU").Set("")
            TransactionManager.Instance.TransactionTaskDone()
        else:
            # Rectang openings in walls
            opening_h = toCM(opening.LookupParameter("OTWÓR WYSOKOŚĆ").AsDouble())
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
caseworks = getInstance(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Casework))
elevators = []
for c in caseworks:
    elevator = filterInstanceByFamilyName(c, "WINDA")
    if not str(elevator) == "None":
        elevators.append(elevator)

for element in elevators:
    location_h = getInstanceLocationPoint(element)
    opening_h = getFamilyLenParameterByName(element, "OTWÓR WYSOKOŚĆ")
    opening_rough_h = getFamilyLenParameterByName(element, "OTWÓR ŻELBET WYSOKOŚĆ")
    floor_h = getFamilyLenParameterByName(element, "POSADZKA GRUBOŚĆ WARSTW")
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