# PartKeeprToInvenTree

PartKeeprToInvenTree is a python tool that can extract the inventory from PartKeepr and commit it to InvenTree.

It can potentially be used out-of-the-box, but you should expect to have to make some adaptations. I wrote this just to be able to convert my own PartKeepr installation to InvenTree. And there is a fairly high probability that it will choke on something from your database that was not present in mine.

And it will only copy the type of data that was present in my database. I only used the inventory part of PartKeepr, so if you have projects in your database they will not be transferred over.

The tool will transfer distributors, manufacturers, categories, storage locations, parameter templates and parts. For parts it will import the standard part data, part image, attachments and part parameters. Since PartKeepr don't have a dedicated image property for parts, the first attachment found that is a bitmap file will be treated as the part image.

The way PartKeepr and InvenTree handle part parameters and units are quite different. So expect issues if you use that extensively. InvenTree is much more limited in this regard, and the list of valid units can not be updated via the REST API (AFAIK). So if your database use units not supported by InvenTree that will cause the import to fail. This can probably be fixed by adding the missing unit to the InvenTree configuration or by modifying the source database.

Also note that the tool only create distributors, manufacturers, categories, storage locations and parameter templates as they are encountered while transferring parts. So if you have any of those entities that is never referenced by a part, they will not be transferred.

The tool will not transfer images, attachment or parameters for any other entities but parts. So if you for example have images on your storage locations you will have to either extend the tool, or transfer them manually (my PartKeepr database had lost all location images, so I had no use for it).


TLDR; If you are lucky you can use this tool to transfer your inventory, but more likely you will need to use it as a base for a tool that fulfill your needs.


NOTE: The first thing this tool do is to wipe most data from InvenTree. If that is not something you want you have to disable the DeleteAllXXX() calls from main() in PartKeeprToInvenTree.py. But if you disable DeleteAllParts() you can only run the tool once since it will not be all that happy about the part-name collisions that will occur on the second run. It is only useful for the initial population of the InvenTree inventory when transitioning from PartKeepr to InvenTree. Not for incremental updates.
