import requests
from inventree.stock import StockItem, StockLocation
from Utils import ExceptionTracker

class ITStorageNode(object):
    def __init__(self, name, id, parentID):
        self.Name = name
        self.ID = id
        self.ParentID = parentID
        self.Parent = None
        self.Children = []

    def ToStringLeaf(self):
        if self.Parent != None:
            return self.Parent.ToStringLeaf() + " -> " + self.Name
        else:
            return self.Name;
            
    def ToString(self, depth = 0):
        str = " " * depth + self.Name
        for child in self.Children:
            str += "\n" + child.ToString(depth + 1)
        return str
        
class ITStorageTree(object):
    def __init__(self, api):
        self.API = api
        self.Root = ITStorageNode("Root", -1, -1)
        self.MaxRetries = 3

        exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to get stock locations.")
        while True:
            try:
                locations = StockLocation.list(api)
                break
            except requests.exceptions.HTTPError as err:
                exceptTracker.ExceptionReceived(err)
        
        locationDict = {}
        for locationData in locations:
            locationDict[locationData.pk] = ITStorageNode(locationData.name, locationData.pk, locationData.parent)


        for locationID in locationDict:
            location = locationDict[locationID]
            if location.ParentID == None:
                location.Parent = self.Root
            else:
                location.Parent = locationDict[location.ParentID]
            location.Parent.Children.append(location)
        
    def FindOrCreateNode(self, parent: ITStorageNode, path: str):
#        print("Path: %s (%s)" % (path, parent.Name))
        node = None
        name = path[0]
        for i in parent.Children:
#            print("  Name: %s" % i.Name)
            if i.Name == name:
                node = i
                break
           
        if node == None:
            args = { 'name' : name }
            if parent.ID != -1:
                args['parent'] = parent.ID
                
            exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to create stock location.")
            while True:
                try:
                    location = StockLocation.create(self.API, args)
                    break
                except requests.exceptions.HTTPError as err:
                    exceptTracker.ExceptionReceived(err)

            node  = ITStorageNode(name, location.pk, parent.ID)
            node.Parent = parent
            parent.Children.append(node)
#            print("Created location: %s(%d)" % (node.ToStringLeaf(), node.ID))
            
        if node != None:
            if len(path) > 1:
                return self.FindOrCreateNode(node, path[1:])
            else:
                return node
        return None
            
    def FindOrCreatePath(self, path: str):
        return self.FindOrCreateNode(self.Root, path[1:])
