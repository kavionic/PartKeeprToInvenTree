import requests
from inventree.company import Company, ManufacturerPart
from Utils import ExceptionTracker
from PKPartHandler import PKManufacturer


class ITManufacturerList(object):
    def __init__(self, api):
        self.API = api
        self.MaxRetries = 3

        exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to get manufacturers list.")
        while True:
            try:
                self.Manufacturers = Company.list(api)
                break
            except requests.exceptions.HTTPError as err:
                exceptTracker.ExceptionReceived(err)
        
    def CreateManufacturerPart(self, pkManufacturer: PKManufacturer, partID: int, fallbackMPN: str) -> ManufacturerPart:
        manufacturer = None
        for i in self.Manufacturers:
            if i.is_manufacturer and i.name == pkManufacturer.Name:
#                print("Found manufacturer: %s" % i.name)
                manufacturer = i
                break
                
        if manufacturer == None:
#            print("Create manufacturer: %s" % pkManufacturer.Name)
            args = { 'name': pkManufacturer.Name, 'is_customer': False, 'is_manufacturer': True, 'is_supplier': False }
            if pkManufacturer.Comment:
                args['description'] = pkManufacturer.Comment
            if pkManufacturer.URL:
                args['website'] = pkManufacturer.URL
            if pkManufacturer.Phone:
                args['phone'] = pkManufacturer.Phone
            if pkManufacturer.Email:
                args['email'] = pkManufacturer.Email
            
            exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to create manufacturer.")
            while True:
                try:
                    manufacturer = Company.create(self.API, args)
                    break
                except requests.exceptions.HTTPError as err:
                    exceptTracker.ExceptionReceived(err)
            self.Manufacturers.append(manufacturer)
                
        if manufacturer != None:
            if pkManufacturer.PartNumber != "":
                MPN = pkManufacturer.PartNumber
            else:
                MPN = fallbackMPN
            exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to create manufacturer part.")
            while True:
                try:
                    return ManufacturerPart.create(self.API,
                        {
                            'part': partID,
                            'manufacturer': manufacturer.pk,
                            'MPN': MPN
                        })
                except requests.exceptions.HTTPError as err:
                    exceptTracker.ExceptionReceived(err)

                    
        return None
