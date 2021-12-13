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


doc = doc()
string = IN[0]
string_num = [int(s) for s in string.split() if s.isdigit()]

for i, num in enumerate(string_num):
    if not len(str(num)) >= 2:
        del string_num[i]

id_nums = list(set(string_num))

output = []

v = doc.ActiveView

for id in id_nums:
    element = doc.GetElement(ElementId(id))
    bool1 = str(element.get_BoundingBox(v))
    if not bool1 == "None":
        TransactionManager.Instance.EnsureInTransaction(doc)
        n_v_id = v.Duplicate(ViewDuplicateOption.Duplicate)
        n_v = doc.GetElement(n_v_id)
        bb = element.get_BoundingBox(n_v)
        n_v.Name = (str(id))
        # n_v.CropBoxActive = true
        n_v.SetSectionBox(bb)
        TransactionManager.Instance.TransactionTaskDone()
        # output.append((element,str(bb),n_v_id))
        output.append((v))
    else:
        pass

OUT = v, output