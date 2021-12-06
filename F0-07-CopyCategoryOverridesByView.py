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

# INPUTS
import_view = UnwrapElement(IN[0])
active = UnwrapElement(IN[1])
# CODE
doc = DocumentManager.Instance.CurrentDBDocument
categories = doc.Settings.Categories
output = []
for i in categories:
    try:
        from_overide = import_view.GetCategoryOverrides(i.Id)
        from_hidden = import_view.GetCategoryHidden(i.Id)
        TransactionManager.Instance.EnsureInTransaction(doc)
        active.SetCategoryOverrides(i.Id, from_overide)
        active.SetCategoryHidden(i.Id, from_hidden)
        TransactionManager.Instance.TransactionTaskDone()
        output.append((i.Name, from_hidden))
    except:
        pass

category_collector = FilteredElementCollector(doc).OfClass(typeof(categories))
# OUTPUT
OUT = doc.ActiveView, output, category_collector