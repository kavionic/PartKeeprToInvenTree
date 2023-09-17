import os
import io
import requests
from inventree.part import Part, PartCategory, ParameterTemplate, Parameter
from inventree.stock import StockItem, StockLocation
from Utils import ExceptionTracker
from PKPartHandler import PKPart, PKCategory
from ITStorageTree import ITStorageNode

class ITPartHandler(object):

    def __init__(self, api):
        self.API = api
        self.MaxRetries = 3
        self.PartParameterTemplates = ParameterTemplate.list(self.API)
        
    def DeleteAllParts(self):
        exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to get part list.")
        while True:
            try:
                partList = Part.list(self.API)
                break
            except requests.exceptions.HTTPError as err:
                exceptTracker.ExceptionReceived(err)
#        partIDs = []
#        for part in partList:
#            partIDs.append(part.pk)
# 
#        if len(partIDs) > 0:
#            print("Deleting %d parts." % len(partIDs))
#            Part.bulkDelete(partIDs)
        index = 0
        for itPart in partList:
            print("Delete part %d/%d: %s" %(index + 1, len(partList), itPart.name))
            index += 1
            if itPart._data['active']:
                del itPart._data['image']
                itPart._data['active'] = False
                exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to deactivate part.")
                while True:
                    try:
                        itPart.save()
                        break
                    except requests.exceptions.HTTPError as err:
                        exceptTracker.ExceptionReceived(err)
            exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to delete part.")
            while True:
                try:
                    itPart.delete()
                    break
                except requests.exceptions.HTTPError as err:
                    exceptTracker.ExceptionReceived(err)

    def DeleteAllCategories(self):
        exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to get category list.")
        while True:
            try:
                categoryList = PartCategory.list(self.API)
                break
            except requests.exceptions.HTTPError as err:
                exceptTracker.ExceptionReceived(err)
        index = 0
        for category in categoryList:
            print("Delete category %d/%d: %s" %(index + 1, len(categoryList), category.name))
            index += 1
            exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to delete part category.")
            while True:
                try:
                    category.delete()
                    break
                except requests.exceptions.HTTPError as err:
                    exceptTracker.ExceptionReceived(err)

    def DeleteAllStockLocations(self):
        exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to get stock locations.")
        while True:
            try:
                locationList = StockLocation.list(self.API)
                break
            except requests.exceptions.HTTPError as err:
                exceptTracker.ExceptionReceived(err)
    
        index = 0
        for location in locationList:
            print("Delete stock location %d/%d: %s" %(index + 1, len(locationList), location.name))
            index += 1
            exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to delete stock location.")
            while True:
                try:
                    location.delete()
                    break
                except requests.exceptions.HTTPError as err:
                    exceptTracker.ExceptionReceived(err)

    def GetOrCreatePartParameterTemplate(self, name: str, description: str, units: str = ""):
        for template in self.PartParameterTemplates:
            if template.name == name:
                return template
        exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to create part parameter template.")
        while True:
            try:
                template = ParameterTemplate.create(self.API, { 'name' : name, 'description': description, 'units' : units })
                self.PartParameterTemplates.append(template)
                return template
            except requests.exceptions.HTTPError as err:
                exceptTracker.ExceptionReceived(err)

    def AddPartParameter(self, itPart: Part, templateName: str, description: str, stringValue: str, numericValue: float = None, units: str = ""):
        template = self.GetOrCreatePartParameterTemplate(templateName, description, units)
        exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to create part parameter.")
        while True:
            try:
                return Parameter.create(self.API, { 'part' : itPart.pk, 'template' : template.pk, 'data' : stringValue, 'data_numeric' : numericValue })
            except requests.exceptions.HTTPError as err:
                exceptTracker.ExceptionReceived(err)

    def CreatePart(self, pkPart: PKPart, categoryNode: PKCategory, storageNode: ITStorageNode):
        if len(pkPart.Description) == 0:
            pkPart.Description = pkPart.Name
            
        exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to create part.")
        while True:
            try:
                itPart = Part.create(self.API,
                    {
                        'name' : pkPart.Name,
                        'category' : categoryNode.ID,
                        'default_location' : storageNode.ID,
                        'description' : pkPart.Description,
                        'active' : True,
                        'virtual' : False,
                        'IPN' : pkPart.IPN,
                        'revision' : pkPart.Revision
                    })
                break
            except requests.exceptions.HTTPError as err:
                exceptTracker.ExceptionReceived(err)
        if pkPart.Footprint != "":
            self.AddPartParameter(itPart, "Footprint", "PCB footprint type.", pkPart.Footprint)
            
        for pkPartParameter in pkPart.Parameters:
            self.AddPartParameter(itPart, pkPartParameter.Name, pkPartParameter.Description, pkPartParameter.StringValue, pkPartParameter.NumericValue, pkPartParameter.Unit)
            
        return itPart
    
    def CreateStockPart(self, itPart, pkpart, supplierPart, storageNode):
        args = {
            'part' : itPart.pk,
            'delete_on_deplete' : True,
            'location' : storageNode.ID,
            'quantity' : pkpart.Stock,
            'purchase_price' : pkpart.Price
        }
        if supplierPart != None:
            args['supplier_part'] = supplierPart.pk
        exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to create stock part.")
        while True:
            try:
                return StockItem.create(self.API, args)
            except requests.exceptions.HTTPError as err:
                exceptTracker.ExceptionReceived(err)
    
    def SetPartImage(self, itPart, attachment, imageStream):
        files = {}
        files['image'] = (attachment.originalFilename, imageStream)
        exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to create part image.")
        while True:
            try:
                itPart.save(data={}, files=files)
                break
#        itPart.uploadImage(image)
            except requests.exceptions.HTTPError as err:
                exceptTracker.ExceptionReceived(err)
                imageStream.seek(0)

    def AddPartAttachment(self, itPart, attachment, dataStream):
        dataStream.name = attachment.originalFilename
        exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to create part attachment.")
        while True:
            try:
                itPart.uploadAttachment(dataStream)
                break
            except requests.exceptions.HTTPError as err:
                exceptTracker.ExceptionReceived(err)
                dataStream.seek(0)
