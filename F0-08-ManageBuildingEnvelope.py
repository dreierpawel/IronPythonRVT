# P.DREIER ©  github.com/dreierpawel
import clr
import sys

import math

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


def to_cm(value):
    return UnitUtils.ConvertFromInternalUnits(value, UnitTypeId.Centimeters)


def vertical_building_envelopes_types():
    global doc
    return FilteredElementCollector(doc).OfCategory(
        BuiltInCategory.OST_Walls).WhereElementIsElementType().ToElements()


def horizontal_building_envelopes_types():
    # Create ICollection[BuiltInCategory]
    horizontal_building_envelope_categories_ids = List[BuiltInCategory]()
    horizontal_building_envelope_categories_ids.Add(BuiltInCategory.OST_Floors)
    horizontal_building_envelope_categories_ids.Add(BuiltInCategory.OST_Roofs)
    horizontal_building_envelope_categories_ids.Add(BuiltInCategory.OST_Ceilings)
    filter_horizontal_building_envelope_categories_ids = ElementMulticategoryFilter(
        horizontal_building_envelope_categories_ids)
    return FilteredElementCollector(doc).WherePasses(
        filter_horizontal_building_envelope_categories_ids).WhereElementIsElementType().ToElements()


def get_compound_structure_layers(item):
    layers = []
    layermat = []
    layerfunc = []
    layerwidth = []
    layercore = []
    layerwraps = []
    layervar = []
    layerdeck = []
    try:
        if hasattr(item, "GetCompoundStructure"):
            compstruc = item.GetCompoundStructure()
            vertcomp = compstruc.IsVerticallyCompound
            varlayer = compstruc.VariableLayerIndex
            num = compstruc.LayerCount
            counter = 0
            while counter < num:
                layers.append(compstruc.GetLayers()[counter])
                layermat.append(item.Document.GetElement(compstruc.GetMaterialId(counter)))
                layerfunc.append(compstruc.GetLayerFunction(counter))
                layerwidth.append(to_cm(compstruc.GetLayerWidth(counter)))
                layercore.append(compstruc.IsCoreLayer(counter))
                if compstruc.IsCoreLayer(counter):
                    layerwraps.append(False)
                else:
                    layerwraps.append(compstruc.ParticipatesInWrapping(counter))
                if varlayer == counter:
                    layervar.append(True)
                else:
                    layervar.append(False)
                layerdeck.append(compstruc.IsStructuralDeck(counter))
                counter += 1
    except:
        pass
    return layers, layermat, layerfunc, layerwidth, layercore, layerwraps, layervar, layerdeck


def building_envelopes_inspector(elements_list):
    if len(elements_list) > 1:
        return map(list, zip(*[get_compound_structure_layers(x) for x in elements_list]))
    else:
        return get_compound_structure_layers(elements_list)


def filter_building_envelope(lst):
    for i, e in enumerate(lst):
        if str(e) == "[]":  # filter empty list
            lst[i] = False
        else:
            for m in e:
                if str(m) == "None":
                    lst[i] = False
                else:
                    lst[i] = True


def filter_list_by_bool_mask(lst, bool_lst):
    output = []
    for ele, bool_m in zip(lst, bool_lst):
        if bool_m is True:
            output.append(ele)
        else:
            pass
    return output


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


def get_parameter_value(element, parameter_name):
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


def concat_list(l1, l2, joiner="."):
    return [[i + joiner + j for i, j in zip(x, y)] for x, y in zip(l1, l2)]


def create_be_codes_lst(materials, widths_lst, elements):
    global doc
    marks = []
    for mat_lst in materials:
        marks_sub = []
        for m in mat_lst:
            marks_sub.append(get_parameter_value(m, "Mark"))
        marks.append(marks_sub)

    widths = []
    full_width = []
    for width in widths_lst:
        width_sub = []
        for w in width:
            width_sub.append(str(math.ceil(w)).replace(".0", ""))
            full_width_sub = "GR. " + str(sum(width)).replace(".", ",") + " CM"
        widths.append(width_sub)
        full_width.append(full_width_sub)

    wall_code_lst = concat_list(marks, widths)
    full_code = []
    for codes in wall_code_lst:
        full_code.append("/".join(codes))

    type_code = []
    for codes in wall_code_lst:
        single_code = []
        for code in codes:
            single_code.append(code[:2])
        type_code.append("/".join(single_code).replace(".", ""))

    short_code = []
    for i in type_code:
        if i.count("/") > 2:
            short_code.append("WW")
        else:
            short_code.append(i)

    descriptions = []
    manual_codes = []
    for e in elements:
        e_des = get_parameter_value(e, "Description")
        if str(e_des) == "None":
            e_des = "Brak Opisu"
        e_code = get_parameter_value(e, "PRZEGRODA KOD")
        if str(e_code) == "None":
            e_code = "Brak Kodu"
        descriptions.append(str(e_des).upper())
        manual_codes.append(e_code)

    filter_code_lst = []
    for e, a_code, m_code in zip(elements, full_code, manual_codes):
        if not e.LookupParameter("PRZEGRODA KOD AUTOMATYCZNY").AsInteger() == 1:
            filter_code_lst.append(m_code)
            # filter_code_lst.append(0)
        else:
            filter_code_lst.append(a_code)
            # filter_code_lst.append(1)

    short_code_lst = []
    for e, a_code, m_code in zip(elements, short_code, manual_codes):
        if not e.LookupParameter("PRZEGRODA KOD AUTOMATYCZNY").AsInteger() == 1:
            short_code_lst.append(m_code)
        else:
            short_code_lst.append(a_code)

    full_name = concat_list([short_code_lst], [descriptions], " -- ")[0]
    full_name = concat_list([full_name], [full_width], " ")[0]
    full_name = replace_duplicates_items(full_name)
    return [full_name, full_code, descriptions, filter_code_lst]


def set_parameter_by_name(element, parameter_name, value):
    if element.LookupParameter(parameter_name).IsReadOnly is False:
        p = element.LookupParameter(parameter_name)
        p.Set(value)
        return element
    else:
        return element


def building_envelope_manage_codes(building_envelopes, codes_list):
    global doc
    names_lst = codes_list[0]
    codes_1_lst = codes_list[1]
    codes_3_lst = codes_list[3]
    for be_type, be_name, code_1, code_3 in zip(building_envelopes, names_lst, codes_1_lst, codes_3_lst):
        TransactionManager.Instance.EnsureInTransaction(doc)
        set_parameter_by_name(be_type, "PRZEGRODA KOD", code_3)
        set_parameter_by_name(be_type, "PRZEGRODA KODY WARSTW", code_1)
        be_type.Name = be_name
        TransactionManager.Instance.TransactionTaskDone()
    return building_envelopes


# CODE
doc = DocumentManager.Instance.CurrentDBDocument
# Collect Vertical Building Envelope Types (Wall Types)
vertical_be_types_lst = vertical_building_envelopes_types()
vertical_be_types_lst = building_envelopes_inspector(vertical_be_types_lst)[1]
# Filter Vertical Building Envelope
vertical_be_types_lst_mask = vertical_be_types_lst
filter_building_envelope(vertical_be_types_lst_mask)
# Collect Horizontal Building Envelope Types
horizontal_be_types_lst = horizontal_building_envelopes_types()
horizontal_be_types_lst = building_envelopes_inspector(horizontal_be_types_lst)[1]
# Filter Horizontal Building Envelope
horizontal_be_types_lst_mask = horizontal_be_types_lst
filter_building_envelope(horizontal_be_types_lst_mask)
# Filtered Vertical Building Envelope
vertical_be_types_lst = filter_list_by_bool_mask(vertical_building_envelopes_types(), vertical_be_types_lst_mask)
# Filtered Horizontal Building Envelope
horizontal_be_types_lst = filter_list_by_bool_mask(horizontal_building_envelopes_types(), horizontal_be_types_lst_mask)
# Vertical Building Envelopes - Materials [1],  Widths [3]
vertical_be_types_structure_lst = building_envelopes_inspector(vertical_be_types_lst)
vertical_be_types_structure_materials_lst = vertical_be_types_structure_lst[1]
vertical_be_types_structure_widths_lst = vertical_be_types_structure_lst[3]
vertical_codes = create_be_codes_lst(vertical_be_types_structure_materials_lst, vertical_be_types_structure_widths_lst, vertical_be_types_lst)

# Horizontal Building Envelopes - Materials [1],  Widths [3]
horizontal_be_types_structure_lst = building_envelopes_inspector(horizontal_be_types_lst)
horizontal_be_types_structure_materials_lst = horizontal_be_types_structure_lst[1]
horizontal_be_types_structure_widths_lst = horizontal_be_types_structure_lst[3]
horizontal_codes = create_be_codes_lst(horizontal_be_types_structure_materials_lst, horizontal_be_types_structure_widths_lst, horizontal_be_types_lst)

# Add Codes to Building Envelopes
building_envelope_manage_codes(vertical_be_types_lst, vertical_codes)
building_envelope_manage_codes(horizontal_be_types_lst, horizontal_codes)

# OUTPUT
OUT = vertical_be_types_lst, horizontal_be_types_lst
