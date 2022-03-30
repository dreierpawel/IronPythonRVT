import clr
import sys
sys.path.append('C:\Program Files (x86)\IronPython 2.7\Lib')
import System
from System import Array
from System.Collections.Generic import *
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.<span class="elia_highlightedItem " data-track="c9240c17-6237-43df-9cad-4d7042c12634"
            data-lemma="geometry" data-pos="NOUN"
            data-genre=WyJTY2kiXQ==
        >Geometry<svg width="13" height="13" viewBox="0 0 13 13" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M6.5006 12.5C3.18807 12.4964 0.503638 9.8122 0.5 6.50001V6.38001C0.565965 3.08273 3.28103 0.456785 6.57901 0.500539C9.87699 0.544293 12.5214 3.24134 12.4999 6.53921C12.4783 9.83708 9.79887 12.4993 6.5006 12.5ZM3.5003 5.90001V7.10001H5.90054V9.5H7.10066V7.10001H9.5009V5.90001H7.10066V3.50001H5.90054V5.90001H3.5003Z" fill="#C4064E"/>
</svg>
</span> import *
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

#######OK NOW YOU CAN CODE########


def get_selected_elements():
    global uiapp
    global uidoc
    selected_elements = uidoc.Selection
    selected_elements_ids = selected_elements.GetElementIds()
    elements_lst = []
    for element_id in selected_elements_ids:
        elements_lst.append(doc.GetElement(element_id))
    return elements_lst


# Doc & App
doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
app = uiapp.Application
# Input
# OUT
OUT = get_selected_elements()
