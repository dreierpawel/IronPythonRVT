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
import System.Reflection

# Definitions


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


def get_parameter_value_by_name(element, parameter_name, empty_value=""):
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


# CODE
doc = DocumentManager.Instance.CurrentDBDocument
materials = FilteredElementCollector(doc).OfClass(Material).ToElements()

filter_materials = []
for m in materials:
    if "--" in m.Name:
        m_name = m.Name
        m_des_from_name = m_name.split("--")[1].replace("-", ".")
        m_mark_from_name = m_name.split("--")[0].replace("-", ".")
        new_name = "--".join([m_mark_from_name, m_des_from_name])
        filter_materials.append([m, new_name, m_mark_from_name, m_des_from_name])

marks = []
for i in filter_materials:
    mark = i[2]
    marks.append(mark)
new_marks = replace_duplicates_items(marks)

for mkr, e in zip(new_marks, filter_materials):
    e[2] = mkr
    e[1] = "--".join([mkr, e[3]])

for els in filter_materials:
    m = els[0]
    TransactionManager.Instance.EnsureInTransaction(doc)
    m.Name = els[1]
    m_new_mark = m.LookupParameter("Mark")
    m_new_mark.Set(els[2])
    m_new_des = m.LookupParameter("Description")
    m_new_des.Set(els[3])
    TransactionManager.Instance.TransactionTaskDone()

OUT = filter_materials
