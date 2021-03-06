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


def to_cm(value):
    return UnitUtils.ConvertFromInternalUnits(value, UnitTypeId.Centimeters)


def getInstanceLocationPoint(instance):
    return to_cm(instance.Location.Point.Z)


def extract(lst, i):
    return list(list(zip(*lst))[i])


def flatten(t):
    return [item for sublist in t for item in sublist]


def filter_building_envelopes_elements_from_selected_elements(elements):
    global doc
    # Filter walls from elements input
    vertical_building_envelope = []
    horizontal_building_envelope = []
    for e in elements:
        e_type = e.GetType()
        h_bool = e_type == Floor or (e_type == FootPrintRoof) or e_type == Ceiling
        if e.GetType() == Wall:
            vertical_building_envelope.append(e)
        if h_bool:
            if e.GetType() == FootPrintRoof:
                # Roofs
                level_id = e.get_Parameter(BuiltInParameter.ROOF_BASE_LEVEL_PARAM).AsElementId()
                level = doc.GetElement(level_id)
                level_elevation = to_cm(level.Elevation)
                level_offset = to_cm(e.get_Parameter(BuiltInParameter.ROOF_LEVEL_OFFSET_PARAM).AsDouble())
                element_location = level_elevation + level_offset
                e = e.RoofType
            else:
                # Floors and Ceilings
                level_id = e.get_Parameter(BuiltInParameter.LEVEL_PARAM).AsElementId()
                level = doc.GetElement(level_id)
                level_elevation = to_cm(level.Elevation)
                try:
                    level_offset = to_cm(e.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).AsDouble())
                    e = e.FloorType
                except:
                    level_offset = to_cm(e.get_Parameter(BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM).AsDouble())
                    e_id = e.GetTypeId()
                    e = doc.GetElement(e_id)
                element_location = level_elevation + level_offset
                horizontal_building_envelope.append((e, element_location))
    # Assign your output to the OUT variable.
    try:
        if h_bool:
            horizontal_building_envelope = extract(sorted(horizontal_building_envelope , key=lambda x: x[1], reverse=True), 0)
    except:
        if h_bool:
            horizontal_building_envelope = extract(horizontal_building_envelope, 0)

    return (vertical_building_envelope, horizontal_building_envelope)


def list_chop(lst):
    output = []
    for i in lst:
        output.append([i])
    return output


def add_enter(lst):
    output = []
    for i in lst:
        output.append(str(i).replace(",0", ""))
    return "\n".join(output)


def add_cm_to_str(lst):
    output = []
    for i in lst:
        i = str(i).replace(".", ",") + " cm"
        output.append(i)
    return output


def sort_walls_Ext_to_Int(walls):
    # Sort walls exterior -> interior
    walls = sorted(walls, key=lambda x: x[1], reverse=False)
    num_lst = []
    for w in walls:
        num = w[1]
        num_lst.append(str(num))
        code = "".join(num_lst)
    if code == "001":
        # 001 E E C
        el = walls[2]
        walls.remove(walls[2])
        walls.insert(1, el)
    if code == "133":
        # 133 C I I
        el = walls[0]
        walls.remove(walls[0])
        walls.insert(1, el)
    return walls


def GetCompoundStructureLayers(item):
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
            # vertcomp = compstruc.IsVerticallyCompound
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
    # return layers, layermat, layerfunc, layerwidth, layercore, layerwraps, layervar, layerdeck
    return layermat, layerfunc, layerwidth, layercore, layervar, layerdeck


def add_data_to_wall_tag(layer_tag, walls):
    # Get Information about walls and layers
    walls = walls
    wallsData = []
    for w in walls:
        w = w[0]
        wType = w.WallType
        wTypeFunction = wType.Function
        wTypeId = wType.Id
        wTypeCode = wType.LookupParameter("PRZEGRODA KOD").AsString()
        wTypeName = wType.FamilyName
        if wTypeName == "Curtain Wall":
            panelId = wType.get_Parameter(BuiltInParameter.AUTO_PANEL_WALL).AsElementId()
            panel = doc.GetElement(panelId)
            panelThickness = to_cm(panel.get_Parameter(BuiltInParameter.CURTAIN_WALL_SYSPANEL_THICKNESS).AsDouble())
            panelMaterialId = panel.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM).AsElementId()
            panelMaterial = doc.GetElement(panelMaterialId)
            wTypeName = panelMaterial.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION).AsString()
            layerfunc = MaterialFunctionAssignment.Finish1
            lst = [panelMaterial, layerfunc, panelThickness, False, False, False]
            wTypeStructure = list_chop(lst)
        else:
            wTypeStructure = GetCompoundStructureLayers(wType)
        wTypeInfo = [wTypeName, wTypeId, wType, wTypeFunction, wTypeCode, wTypeStructure]
        wallsData.append(wTypeInfo)

    # Walls Reverse Structure of Last Wall
    output = []
    l = len(wallsData) - 1
    for i, w in enumerate(wallsData):
        if i == l:
            lastItem = w[-1]
            newWallCode = w[-2].split("/")
            newWallCode.reverse()
            newWallCode = "/".join(newWallCode)
            w[4] = newWallCode
            w = w[:-1]
            new_lst = []
            for item in lastItem:
                item.reverse()
            w.append(lastItem)
            output.append(w)
        else:
            output.append(w)

    # Extract and make strings from data

    partitionCode = "/".join(extract(output, 4))
    structureLayers = extract(output, 5)
    materials = flatten(extract(structureLayers, 0))
    thickness = flatten(extract(structureLayers, 2))
    materialsNames = []
    materialsCodes = []
    thicknessCode = []
    for t in thickness:
        thicknessCode.append(math.ceil(t))
    for material, thick in zip(materials, thicknessCode):
        matName = material.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION).AsString()
        matCode = material.get_Parameter(BuiltInParameter.ALL_MODEL_MARK).AsString()
        thick = str(thick).replace(".0", "")
        matCode = [matCode, thick]
        matCode = ".".join(matCode)
        materialsNames.append(matName)
        materialsCodes.append(matCode)

    # Wall Codes
    wallCodes = extract(output, 4)
    partitionStructure = extract(extract(output, 5), 1)

    materialsCodes = add_enter(materialsCodes)
    materialsNames = add_enter(materialsNames)
    thickness = add_enter(add_cm_to_str(thickness))

    walls_lst = []
    walls_num = []
    for elem, code in zip(partitionStructure, wallCodes):
        num = len(elem)
        walls_Codes = code + ("\n" * num)
        walls_lst.append(walls_Codes)
        walls_num.append(num)

    # Get Walls ID

    wallTypes_lst = extract(output, 2)

    id_lst = []

    for i in wallTypes_lst:
        wallId = str(i.Id)
        id_lst.append(wallId)

    # Change values of tags
    TransactionManager.Instance.EnsureInTransaction(doc)
    layer_tag.LookupParameter("KOD ZBIORCZY PRZEGRODY BUDOWLANEJ").Set("/".join(wallCodes).replace("/", " / "))
    layer_tag.LookupParameter("KODY WARSTW PRZEGRODY BUDOWLANEJ").Set(materialsCodes)
    layer_tag.LookupParameter("NAZWY MATERIAŁÓW PRZEGRODY BUDOWLANEJ").Set(materialsNames)
    layer_tag.LookupParameter("GRUBOŚCI WARSTW PRZEGRODY BUDOWLANEJ").Set(thickness)
    layer_tag.LookupParameter("ILOŚĆ WARSTW").Set(len(materials))
    layer_tag.LookupParameter("ILOŚĆ WARSTW WYKOŃCZENIA ZEW").Set(len(extract(structureLayers, 0)[0]))
    layer_tag.LookupParameter("KOD ZBIORCZY TABELI").Set("".join(walls_lst))
    layer_tag.LookupParameter("ID WARSTW").Set("[" + ",".join(id_lst) + "]")
    TransactionManager.Instance.TransactionTaskDone()


def add_data_to_floor_tag(layer_tag, floors):
    # Get Information about floors and layers
    floorsData = []
    for fType in floors:
        fTypeId = fType.Id
        fTypeCode = fType.LookupParameter("PRZEGRODA KOD").AsString()
        fTypeName = fType.FamilyName
        fTypeStructure = GetCompoundStructureLayers(fType)
        fTypeFunction = "Horizontal"
        fTypeInfo = [fTypeName, fTypeId, fType, fTypeFunction, fTypeCode, fTypeStructure]
        floorsData.append(fTypeInfo)
    # Floors Reverse Structure of Last Wall
    output = []
    l = len(floorsData) - 1
    for i, w in enumerate(floorsData):
        if i == l:
            lastItem = w[-1]
            newFloorCode = w[-2].split("/")
            newFloorCode.reverse()
            newFloorCode = "/".join(newFloorCode)
            w[4] = newFloorCode
            w = w[:-1]
            new_lst = []
            for item in lastItem:
                item.reverse()
            w.append(lastItem)
            output.append(w)
        else:
            output.append(w)
    # Extract and make strings from data
    partitionCode = "/".join(extract(output, 4))
    structureLayers = extract(output, 5)
    materials = flatten(extract(structureLayers, 0))
    thickness = flatten(extract(structureLayers, 2))
    variable_layer_bool = flatten(extract(structureLayers, 4))
    slope_lst = []
    slope_min = []
    for i in variable_layer_bool:
        if i:
            slope_lst.append(" (SPADEK)")
            slope_min.append("MIN ")
        else:
            slope_lst.append("")
            slope_min.append("")
    materialsNames = []
    materialsCodes = []
    thicknessCode = []
    for t in thickness:
        thicknessCode.append(math.ceil(t))
    for material, thick, slope in zip(materials, thicknessCode, slope_lst):
        matName = material.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION).AsString()
        matName = matName + slope
        matCode = material.get_Parameter(BuiltInParameter.ALL_MODEL_MARK).AsString()
        thick = str(thick).replace(".0", "")
        matCode = [matCode, thick]
        matCode = ".".join(matCode)
        materialsNames.append(matName)
        materialsCodes.append(matCode)
    # Wall Codes
    floorCodes = extract(output, 4)
    partitionStructure = extract(extract(output, 5), 1)
    new_thickness = []
    for ti, slope_min in zip(thickness, slope_min):
        new_thickness.append((slope_min + str(ti)))
    thickness = new_thickness
    materialsCodes = add_enter(materialsCodes)
    materialsNames = add_enter(materialsNames)
    thickness = add_enter(add_cm_to_str(thickness))
    floor_lst = []
    floor_num = []
    for elem, code in zip(partitionStructure, floorCodes):
        num = len(elem)
        floor_Codes = code + ("\n" * num)
        floor_lst.append(floor_Codes)
        floor_num.append(num)
    # Get floor ID
    floorTypes_lst = extract(output, 2)
    id_lst = []
    for i in floorTypes_lst:
        floorId = str(i.Id)
        id_lst.append(floorId)
    # Change values of tags
    TransactionManager.Instance.EnsureInTransaction(doc)
    layer_tag.LookupParameter("KOD ZBIORCZY PRZEGRODY BUDOWLANEJ").Set("/".join(floorCodes).replace("/", " / "))
    layer_tag.LookupParameter("KODY WARSTW PRZEGRODY BUDOWLANEJ").Set(materialsCodes)
    layer_tag.LookupParameter("NAZWY MATERIAŁÓW PRZEGRODY BUDOWLANEJ").Set(materialsNames)
    layer_tag.LookupParameter("GRUBOŚCI WARSTW PRZEGRODY BUDOWLANEJ").Set(thickness)
    layer_tag.LookupParameter("ILOŚĆ WARSTW").Set(len(materials))
    layer_tag.LookupParameter("ILOŚĆ WARSTW WYKOŃCZENIA ZEW").Set(len(extract(structureLayers, 0)[0]))
    layer_tag.LookupParameter("KOD ZBIORCZY TABELI").Set("".join(floor_lst))
    layer_tag.LookupParameter("ID WARSTW").Set("[" + ",".join(id_lst) + "]")
    TransactionManager.Instance.TransactionTaskDone()


def add_data_to_building_envelope_tag(layer_tag, be_list):
    # vertical_building_envelope
    elements = filter_building_envelopes_elements_from_selected_elements(be_list)[0]
    # horizontal_building_envelope
    horizontal_elements = filter_building_envelopes_elements_from_selected_elements(be_list)[1]
    #
    wall_function_dict = {
        "Curtain Wall": -1,
        "Interior": 3,
        "Exterior": 0,
        "Foundation": 2,
        "Retaining": 4,
        "Soffit": 5,
        "Coreshaft": 1
    }
    if len(elements) != 0:
        # Filter walls from elements input
        walls = []
        for e in elements:
            if e.GetType() == Wall:
                function_number = wall_function_dict.get(str(e.WallType.Function))
                wTypeName = e.WallType.FamilyName
                if wTypeName == "Curtain Wall":
                    function_number = wall_function_dict.get("Curtain Wall")
                walls.append((e, function_number))
        walls = sort_walls_Ext_to_Int(walls)
        temp.append(walls)
        add_data_to_wall_tag(layer_tag, walls)
    if len(horizontal_elements) != 0:
        add_data_to_floor_tag(layer_tag, horizontal_elements)


# Inputs
elements_selected = UnwrapElement(IN[0])
layer_tag = UnwrapElement(IN[1])
# Code
doc = DocumentManager.Instance.CurrentDBDocument
#
OUT = add_data_to_building_envelope_tag(layer_tag, elements_selected)
