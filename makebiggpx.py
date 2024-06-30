import glob
import xml.etree.ElementTree as ET

class GPXFile:
   
    def __init__(self, gpxFile):
        self.tree = ET.parse(gpxFile)
        self.root = self.tree.getroot()
        self.isTomTom = (self.root.attrib['creator'] == "TomTom MyDrive")

    def dump(self):
        print("--- DUMP ---")
        for node in self.root.iter():
            print(node.tag, node.attrib)

    # add a single wpt node for TomTom files
    def createWpt(self):
        if self.isTomTom:
            for node in self.root.findall("*"):
                if node.tag.endswith("rte"):
                    name = ""
                    lat = ""
                    lon = ""
                    for child in node.findall("*"):
                        if child.tag.endswith("name"):
                            name = child.text
                        elif child.tag.endswith("rtept"):
                            lat = child.attrib['lat']
                            lon = child.attrib['lon']
                            break
                    node.clear()
                    self.root.remove(node)
            wpt = ET.SubElement(self.root, 'wpt', {'lat':lat, 'lon':lon})
            nameNode = ET.SubElement(wpt, 'name')
            nameNode.text = name

    # convert trk to rte
    def convertTrkToRte(self):
        for node in self.root.iter():
            if node.tag.endswith("trk"): # rename trk to rte
                node.tag = "rte"
            elif node.tag.endswith("trkpt"): # rename trkpt to rtept
                for child in node:
                    if child.tag.endswith("name"): # remove name nodes
                        node.remove(child)
                node.tag = "rtept"

    # remove trkseg level leaving all trkpt nodes as direct children of trk
    def movetrkpts(self):
        trkNode = None
        newTrksegNode = None
        for node in self.root.iter():
            if node.tag.endswith("trk"):
                trkNode = node
            elif node.tag.endswith("trkseg"):
                newTrksegNode = ET.XML(ET.tostring(node))
                break
        if trkNode != None:
            numTrkNodeTags = len(trkNode.findall("*"))
            for i in range(numTrkNodeTags):
                trkNode[i].clear()
            trkNode.clear()

            # add trkpt nodes to now empty trk node
            for trkpt in newTrksegNode.iter():
                if trkpt.tag.endswith("trkpt"):
                    trkpt.text = ""
                    trkNode.append(trkpt)

    # remove all but the first wpt
    def tidywpts(self):
        wptIndex = 0
        for node in self.root.findall("*"):
            if node.tag.endswith("wpt"):
                if wptIndex > 0:
                    self.root.remove(node)
                wptIndex = wptIndex + 1

        
    # remove some rtept elements to reduce file size
    def prune(self, numToDelete):
        rte = None
        for child in self.root:
            if child.tag.endswith("rte"):
                rte = child
                break
        numDeleted = numToDelete # skip the first batch
        for rtept in rte.findall("*"):
            if numDeleted == numToDelete:
                numDeleted = 0
            else:
                rte.remove(rtept)
                numDeleted = numDeleted + 1
    
    def modify(self):
        self.createWpt()
        self.movetrkpts()
        self.convertTrkToRte()
        self.prune(10)
        self.tidywpts()

# MAIN
try:
    print("Reading gpx files")

    # list the gpx files in the current dir               
    gpxFiles = []
    for file in glob.glob("[0-9]*.gpx"):
        gpxFiles.append(file)
    gpxFiles.sort()

    # create a GPXFile instance for each
    gpxObjects = []
    for file in gpxFiles:
        print(file)
        gpxObjects.append(GPXFile(file))

    print("Modifying")
    for gpx in gpxObjects:
        gpx.modify()

    print("Producing output file")

    # create a new empty doc from the first one
    newTree = ET.parse(gpxFiles[0])
    newRoot = newTree.getroot()
    newRoot.clear()

    # add the required attributes
    newRoot.set("xmlns:gpxx", "http://www.garmin.com/xmlschemas/GpxExtensions/v3")
    newRoot.set("xmlns:gpxtpx", "http://www.garmin.com/xmlschemas/TrackPointExtension/v1") 
    newRoot.set("creator", "makebiggpx.py") 
    newRoot.set("version", "1.0")
    newRoot.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance") 
    newRoot.set("xsi:schemaLocation", "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd")

    # populate the root with the content
    for gpx in gpxObjects:
        for node in gpx.root.findall("*"):
            newRoot.append(node)

    # hacky replacements to remove namespaces and other stuff
    s = str(ET.tostring(newRoot))
    s = s.replace("\\n", "")
    s = s.replace(":ns0", "")
    s = s.replace("ns0:", "")
    s = s.replace("b'<gpx", "<gpx")
    s = s.replace("gpx>'", "gpx>")

    with open('new.gpx', 'w') as f:
        f.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\" ?>")
        f.write(s)

    print("Done")

except Exception as e:
    print("Exception")
    print(e)

    














