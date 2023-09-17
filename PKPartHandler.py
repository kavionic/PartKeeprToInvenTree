from io import BytesIO
import requests, json

class PKAttachment(object):
    def __init__(self, data):
        self.mimeType = data["mimetype"]
        self.id = data["@id"][data["@id"].rfind("/")+1:]
        self.isImage = data["isImage"]
        self.originalFilename = data["originalFilename"]
        self.size = data["size"]
        self.description = data["description"]
        
class PKPartParameter(object):
    def __init__(self, data):
        self.Name           = data['name']
        self.Description    = data['description']
        self.Unit           = data['unit']['symbol']
        self.UnitName       = data['unit']['name']
        self.IsNumeric      = data['valueType'] == 'numeric'
        
        if self.IsNumeric:
            self.NumericValue = data['value'] * pow(data['siPrefix']['base'], data['siPrefix']['exponent'])
            self.StringValue = "%s" % self.NumericValue #data['value'] + data['siPrefix']['symbol']
        else:
            self.NumericValue = None
            self.StringValue = data['stringValue']
        
class PKDistributor(object):
    def __init__(self, data):
        distributor = data['distributor']
        self.Name = distributor['name']
        self.Address = distributor['address']
        self.URL = distributor['url']
        self.Phone = distributor['phone']
        self.Fax = distributor['fax']
        self.Email = distributor['email']
        self.Comment = distributor['comment']
        self.SKU_URL = distributor['skuurl']
        self.EnabledForReports = distributor['enabledForReports']
        
        self.OrderNumber = data['orderNumber']
        self.PackagingUnit = data['packagingUnit']
        self.Price = data['price']
        self.Currency = data['currency']
        self.SKU = data['sku']
        self.IgnoreForReports = data['ignoreForReports']
        
class PKManufacturer(object):
    def __init__(self, data):
        self.Name       = data['manufacturer']['name']
        self.URL        = data['manufacturer']['url']
        self.Email      = data['manufacturer']['email']
        self.Comment    = data['manufacturer']['comment']
        self.Phone      = data['manufacturer']['phone']
        
        self.PartNumber = data['partNumber']
    
class PKCategory(object):
    def __init__(self, name):
        self.Name           = name
        self.Parent         = None
        self.Parts          = []
        self.SubCategories  = []
        
    def ToStringLeaf(self):
        if self.Parent != None:
            return self.Parent.ToStringLeaf() + " -> " + self.Name
        else:
            return self.Name;
        
class PKPart(object):
    def __init__(self, data):
        self.Name           = data["name"]
        self.Description    = data["description"]
        self.ID             = data["@id"][data["@id"].rfind("/")+1:]
        
        self.Footprint      = data.get('footprint', {});
        if self.Footprint:
            self.Footprint = self.Footprint.get('name', "")
        else:
            self.Footprint = ""

        self.Category           =  data["category"]["name"]
        self.CategoryPath       = data["category"]["categoryPath"].split(u' ➤ ')
        self.StorageLocation    = data["storageLocation"]["name"]
        self.StoragePath        = data["storageLocation"]["categoryPath"].split(u' ➤ ')

        self.IPN                = data['internalPartNumber']
        self.OrigIPN            = self.IPN
        
        self.Stock              = float(data['stockLevel'])
        self.Price              = data['averagePrice']

        self.Revision           = ""
        self.Image              = None

        self.Parameters = []
        for parameterData in data['parameters']:
            self.Parameters.append(PKPartParameter(parameterData))
            
        self.Attachments = []
        for att in data.get('attachments', []):
            if att["isImage"]:
                if not self.Image:
                    self.Image = PKAttachment(att)
                else:
                    print("****Duplicate Image: %s:%d" % (att["originalFilename"], att["size"]))                  
            else:
                self.Attachments.append(PKAttachment(att))

        self.Distributors = []
        for distributorData in data.get('distributors', []):
            distributor = PKDistributor(distributorData)
            if distributor.OrderNumber == "":
                if distributor.Name == "eBay":
                    distributor.OrderNumber = self.Name
                    print("Set order number for %s from dist %s to %s" % (self.Name, distributor.Name, self.Name))
                else:
                    print("Part %s from dist %s does not have a part number" % (self.Name, distributor.Name))
                    raise "Broken distributor"
            self.Distributors.append(distributor)

        self.Manufacturers = []
        for manufacturerData in data.get('manufacturers', []):
            self.Manufacturers.append(PKManufacturer(manufacturerData))

class PKPartTree(object):
    def __init__(self):
        self.RootCategory = PKCategory("Root")

    def AddPartInternal(self, parent, path, part: PKPart):
#        print("Path: %s (%s)" % (path, parent.Name))
        node = None
        name = path[0]
        for i in parent.SubCategories:
#            print("  Name: %s" % i.Name)
            if i.Name == name:
                node = i
                break
           
        if node == None:
            node  = PKCategory(name)
            node.Parent = parent
            parent.SubCategories.append(node)
#            print("Created PKCategory: %s" % node.ToStringLeaf())
            
        if node != None:
            if len(path) > 1:
                return self.AddPartInternal(node, path[1:], part)
            else:
                if part.OrigIPN == "":
                    duplicates = 0
                    for i in node.Parts:
                        if i.name == part.name and i.OrigIPN == "":
                            duplicates += 1
#                            if i.IPN == "":
#                                print("Set IPN of %s to %s" % (part.name, i.description))
                            i.IPN = i.description
                            
                    if duplicates > 0:
                        part.IPN = part.description
#                        print("Set IPN of %s to %s" % (part.name, part.IPN))
                node.Parts.append(part)
                return node
        return None
    
    def AddPart(self, part: PKPart):
        return self.AddPartInternal(self.RootCategory, part.categoryPath[1:], part)
        
class PKPartHandler(object):
    def __init__(self, serverURL, userName, password):
        self.ServerURL = serverURL
        self.Auth=(userName, password)

    def MakePartsUnique(self, partList):
#        tree = PKPartTree()
#        for pkPart in partList:
#            tree.AddPart(pkPart)

        nameToPartMap = {}
        for pkPart in partList:
            key = (pkPart.Name, pkPart.IPN)
            nameToPartMap.setdefault(key, []).append(pkPart)

        for key in nameToPartMap:
            if len(nameToPartMap[key]) > 1:
                revision = 1
                for pkPart in nameToPartMap[key]:
                    pkPart.Revision = "%d" % revision
                    revision += 1
#                    print("Set revision of %s to %s" % (pkPart.Name, pkPart.Revision))

    def GetAllParts(self) -> list:
        url = self.ServerURL + '/api/parts?itemsPerPage=9999999999'

        request = requests.get(url, auth=self.Auth)

        if (request.status_code == 200):
            partList = []
            for partData in request.json()["hydra:member"]:
                pkpart = PKPart(partData)
                partList.append(pkpart)

            self.MakePartsUnique(partList)
            
            return partList
        else:
            return None

    def GetPartAttachment(self, attachment):
        url = self.ServerURL + '/api/part_attachments/' + attachment.id + '/getFile'

        request = requests.get(url, auth=self.Auth)

        if (request.status_code == 200):
#            print("Attachment %s(%s) retrieved: %d" % (attachment.originalFilename, attachment.id, len(request.content)))
            return BytesIO(request.content)
        else:
            print("******** FAILED TO RETRIEVE ATTACHMENT %s(%s) ********" % (attachment.originalFilename, attachment.id))
            return None

