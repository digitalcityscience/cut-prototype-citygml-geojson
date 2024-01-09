
import os
import xml.etree.ElementTree as ET


def find_unique_xml_nodes(directory):
    unique_nodes = set()

    for file in os.listdir(directory):
        if file.endswith('.xml'):
            tree = ET.parse(os.path.join(directory, file))
            root = tree.getroot()

            def recurse_tree(node):
                tag = node.tag
                tag = tag[tag.find("}")+1:]
                unique_nodes.add(tag)
                for child in node:
                    recurse_tree(child)

            recurse_tree(root)

    return unique_nodes


directory_path = "./../data/LoD2_CityGML_HH_2016"
unique_nodes = find_unique_xml_nodes(directory_path)
print(unique_nodes)
