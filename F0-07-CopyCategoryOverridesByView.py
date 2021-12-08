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
# INPUTS
doc = DocumentManager.Instance.CurrentDBDocument
parent_view = UnwrapElement(IN[0])
bool_test = UnwrapElement(IN[1])
child_view = doc.ActiveView

if bool_test is True:
    try:
        child_view_filters_ids_list = child_view.GetFilters()
        for i in child_view_filters_ids_list:
            TransactionManager.Instance.EnsureInTransaction(doc)
            child_view.RemoveFilter(i)
            TransactionManager.Instance.TransactionTaskDone()
    except:
        pass

# Get Filters from Parent View
parent_view_filters_ids_list = parent_view.GetFilters()
# Set Filters Overrides to Child View
for view_filter in parent_view_filters_ids_list:
    try:
        view_filter_visibility = parent_view.GetFilterVisibility(view_filter)
        view_filter_overrides = parent_view.GetFilterOverrides(view_filter)
        TransactionManager.Instance.EnsureInTransaction(doc)
        child_view.AddFilter(view_filter)
        child_view.SetFilterOverrides(view_filter, view_filter_overrides)
        child_view.SetFilterVisibility(view_filter, view_filter_visibility)
        TransactionManager.Instance.TransactionTaskDone()
        output_f = "Success"
    except:
        output_f = "Error"

categories = doc.Settings.Categories
for i in categories:
    try:
        parent_view_override = parent_view.GetCategoryOverrides(i.Id)
        parent_category_hidden = parent_view.GetCategoryHidden(i.Id)
        TransactionManager.Instance.EnsureInTransaction(doc)
        child_view.SetCategoryOverrides(i.Id, parent_view_override)
        child_view.SetCategoryHidden(i.Id, parent_category_hidden)
        TransactionManager.Instance.TransactionTaskDone()
        output_c = "Success"
    except:
        output_c = "Error"

# OUTPUT
OUT = output_f, output_c
