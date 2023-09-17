import requests
from inventree.company import Company, SupplierPart, ManufacturerPart
from inventree.part import Part
from Utils import ExceptionTracker
from PKPartHandler import PKDistributor


class ITSupplierList(object):
    def __init__(self, api, defaultCurrency):
        self.API = api
        self.DefaultCurrenct = defaultCurrency
        self.MaxRetries = 3

        exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to get supplier list.")
        while True:
            try:
                self.Suppliers = Company.list(api)
                break
            except requests.exceptions.HTTPError as err:
                exceptTracker.ExceptionReceived(err)
        
    def CreateSupplierPart(self, pkSupplier: PKDistributor, itPart: Part, manufacturerPart: ManufacturerPart) -> SupplierPart:
        supplier = None

        if pkSupplier.Currency == None:
            pkSupplier.Currency = self.DefaultCurrenct

        for i in self.Suppliers:
            if i.is_supplier and i.name == pkSupplier.Name:
#                print("Found supplier: %s" % i.name)
                supplier = i
                break
                
        if supplier == None:
#            print("Create supplier: %s" % pkSupplier.Name)
            args = {'name': pkSupplier.Name, 'currency': pkSupplier.Currency, 'is_customer': False, 'is_manufacturer': False, 'is_supplier': True}
            if pkSupplier.Comment != "":
                args['description'] = pkSupplier.Comment
            if pkSupplier.URL != "":
                args['website'] = pkSupplier.URL
            if pkSupplier.Phone != "":
                args['phone'] = pkSupplier.Phone
            if pkSupplier.Email != "":
                args['email'] = pkSupplier.Email
            exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to create supplier.")
            while True:
                try:
                    supplier = Company.create(self.API, args)
                    break
                except requests.exceptions.HTTPError as err:
                    exceptTracker.ExceptionReceived(err)
            self.Suppliers.append(supplier)
                
        if supplier != None:
            args = {
                'link': pkSupplier.SKU_URL,
                'part': itPart.pk,
                'SKU': pkSupplier.OrderNumber, #supplierNode.SKU,
                'supplier': supplier.pk,
            }
            if manufacturerPart != None:
                args['manufacturer_part'] = manufacturerPart.pk
                
            exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to create supplier part.")
            while True:
                try:
                    return SupplierPart.create(self.API, args)
                except requests.exceptions.HTTPError as err:
                    exceptTracker.ExceptionReceived(err)
        return None 
