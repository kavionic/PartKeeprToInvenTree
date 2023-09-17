import sys, time, getopt, requests

from inventree.api import InvenTreeAPI
from inventree.company import Company, SupplierPart

from PKPartHandler import PKPartHandler, PKPart
from ITPartHandler import ITPartHandler

from ITStorageTree import ITStorageTree
from ITCategoryTree import ITCategoryTree
from ITManufacturerList import ITManufacturerList
from ITSupplierList import ITSupplierList


def ImportPartKeeperParts(invenTreeAPI: InvenTreeAPI, itPartHandler: ITPartHandler, pkPartHandler: PKPartHandler, defaultCurrency: str):
    suppliers = Company.list(invenTreeAPI)

    storageTree         = ITStorageTree(invenTreeAPI)
    categoryTree        = ITCategoryTree(invenTreeAPI)
    manufacturerList    = ITManufacturerList(invenTreeAPI)
    supplierList        = ITSupplierList(invenTreeAPI, defaultCurrency)
    
    pkPartsList = pkPartHandler.GetAllParts()
 
    maxRetries = 3
    
    index = 0
    for pkPart in pkPartsList:
        retriesLeft = maxRetries
        storageNode = storageTree.FindOrCreatePath(pkPart.StoragePath + [pkPart.StorageLocation])
        categoryNode = categoryTree.FindOrCreatePath(pkPart.CategoryPath);

        print("Create part %d/%d: %s -> %s" % (index + 1, len(pkPartsList), categoryNode.ToStringLeaf(), pkPart.Name))
        index += 1
        
        itPart = itPartHandler.CreatePart(pkPart, categoryNode, storageNode)

        defaultManufacturerPart = None
        for manufacturerNode in pkPart.Manufacturers:
            manufacturerPart = manufacturerList.CreateManufacturerPart(manufacturerNode, itPart.pk, itPart.name)
            if defaultManufacturerPart == None:
                defaultManufacturerPart = manufacturerPart
                
        supplierPart = None
        for supplierNode in pkPart.Distributors:
            supplierPart = supplierList.CreateSupplierPart(supplierNode, itPart, defaultManufacturerPart)

        stockit = itPartHandler.CreateStockPart(itPart, pkPart, supplierPart, storageNode)
        
        if pkPart.Image != None:
            itPartHandler.SetPartImage(itPart, pkPart.Image, pkPartHandler.GetPartAttachment(pkPart.Image))
        
        for attachment in pkPart.Attachments:
            itPartHandler.AddPartAttachment(itPart, attachment, pkPartHandler.GetPartAttachment(attachment))
        
def PrintHelp():
    print("Usage:")
    print("%s %s" % (sys.argv[0], "--pkserver http://partkeeprserver --pkuser <partkeepr_user> --pkpwd <partkeepr_password> --itserver http://inventreeserver --ituser <inventree_user> --itpwd <inventree_password> [--default_currency <EUR>]"))

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["pkserver=", "pkuser=", "pkpwd=", "itserver=", "ituser=", "itpwd=", "default_currency="])
    except getopt.GetoptError:
        PrintHelp()
        sys.exit(2)
        
    pkServerURL     = ""
    pkUser          = ""
    pkPassword      = ""
    itServerURL     = ""
    itUser          = ""
    itPassword      = ""
    defaultCurrency = "USD"
    
    for opt, arg in opts:
        if opt == '-h':
            PrintHelp()
            sys.exit()
        elif opt == "--pkserver":
            pkServerURL = arg
        elif opt == "--pkuser":
            pkUser = arg
        elif opt == "--pkpwd":
            pkPassword = arg
        elif opt == "--itserver":
            itServerURL = arg
        elif opt == "--ituser":
            itUser = arg
        elif opt == "--itpwd":
            itPassword = arg
        elif opt == "--default_currency":
            defaultCurrency = arg

    invenTreeAPI = InvenTreeAPI(itServerURL, username=itUser, password=itPassword)

    pkPartHandler = PKPartHandler(pkServerURL, pkUser, pkPassword)
    itPartHandler = ITPartHandler(invenTreeAPI)

    itPartHandler.DeleteAllParts()
    itPartHandler.DeleteAllCategories()
    itPartHandler.DeleteAllStockLocations()

    ImportPartKeeperParts(invenTreeAPI, itPartHandler, pkPartHandler, defaultCurrency)

main()
