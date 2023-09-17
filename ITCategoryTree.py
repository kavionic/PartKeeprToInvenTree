import requests
from inventree.part import PartCategory,Part
from Utils import ExceptionTracker

class ITCategoryNode(object):
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

class ITCategoryTree(object):
    def __init__(self, api):
        self.API = api
        self.Root = ITCategoryNode("Root", -1, -1)
        self.MaxRetries = 3

        exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to get category list.")
        while True:
            try:
                categorys = PartCategory.list(api)
                break
            except requests.exceptions.HTTPError as err:
                exceptTracker.ExceptionReceived(err)
        
        categoryDict = {}
        for categoryData in categorys:
            categoryDict[categoryData.pk] = ITCategoryNode(categoryData.name, categoryData.pk, categoryData.parent)


        for categoryID in categoryDict:
            category = categoryDict[categoryID]
            if category.ParentID == None:
                category.Parent = self.Root
            else:
                category.Parent = categoryDict[category.ParentID]
            category.Parent.Children.append(category)
        
    def FindOrCreateNode(self, parent, path):
#        print("Path: %s (%s)" % (path, parent.Name))
        node = None
        name = path[0]
        for i in parent.Children:
            if i.Name == name:
                node = i
                break
           
        if node == None:
            args = { 'name' : name }
            if parent.ID != -1:
                args['parent'] = parent.ID
            exceptTracker = ExceptionTracker(self.MaxRetries, "Failed to create category.")
            while True:
                try:
                    category = PartCategory.create(self.API, args)
                    break
                except requests.exceptions.HTTPError as err:
                    exceptTracker.ExceptionReceived(err)
            node  = ITCategoryNode(name, category.pk, parent.ID)
            node.Parent = parent
            parent.Children.append(node)
#            print("Created category: %s(%d)" % (node.ToStringLeaf(), node.ID))
            
        if node != None:
            if len(path) > 1:
                return self.FindOrCreateNode(node, path[1:])
            else:
                return node
        return None
            
    def FindOrCreatePath(self, path):
        return self.FindOrCreateNode(self.Root, path[1:])
