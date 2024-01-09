import geopandas as gpd
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
import pandas as pd
import os
from pathlib import Path

ns = {
    'gml': 'http://www.opengis.net/gml',
    'bldg': 'http://www.opengis.net/citygml/building/1.0',
    'gen': 'http://www.opengis.net/citygml/generics/1.0',
}

target_crs = 'EPSG:4326'
original_crs = 'EPSG:25832'


def get_attrib(path, building):
    element = building.find(path, ns)
    return element.text if element is not None else None


def get_ground_attributes(building):
    return {
        "lage": get_attrib('.//gen:stringAttribute[@name="DatenquelleLage"]/gen:value', building),
        "bodenhoehe": get_attrib('.//gen:stringAttribute[@name="DatenquelleBodenhoehe"]/gen:value', building),
    }


def get_roof_attributes(building):
    return {
        "dachhoehe": get_attrib('.//gen:stringAttribute[@name="DatenquelleDachhoehe"]/gen:value', building),
        "measuredHeight": get_attrib('bldg:measuredHeight', building)
    }


def extract_ground_attributes(polygon, building):
    id = polygon.attrib["{http://www.opengis.net/gml}id"]
    attributes = get_ground_attributes(building)
    attributes["id"] = id
    attributes["surface_type"] = "ground"
    return attributes


def extract_roof_attributes(polygon, building):
    id = polygon.attrib["{http://www.opengis.net/gml}id"]
    attributes = get_roof_attributes(building)
    attributes["surface_type"] = "roof"
    attributes["id"] = id
    return attributes


def extract_geometry(polygon):
    exterior_coords = polygon.find('.//gml:exterior//gml:LinearRing', ns)
    assert exterior_coords is not None
    coords = [(
        float(coord.text.split()[0]),
        float(coord.text.split()[1]),
    ) for coord in exterior_coords.findall('./gml:pos', ns)]
    return Polygon(coords)


def extract_surfaces(citygml_file_path, node, extract_attributes):
    tree = ET.parse(citygml_file_path)
    root = tree.getroot()
    buildings = root.findall('.//bldg:Building', ns)

    all_features, all_attributes = [], []
    for building in buildings:
        for polygon in building.findall(f'.//bldg:{node}//gml:Polygon', ns):
            attributes = extract_attributes(polygon, building)
            geometry = extract_geometry(polygon)
            all_attributes.append(attributes)
            all_features.append(geometry)

    gdf = gpd.GeoDataFrame(geometry=all_features, crs=original_crs).assign(**pd.DataFrame(all_attributes))
    gdf.set_index('id', inplace=True)
    return gdf.to_crs(target_crs)


def extract_all_surface_types(directory_path):
    ground_surfaces = []
    roof_surfaces = []
    files = os.listdir(directory_path)
    for filename in filter(lambda f: f.endswith('.gml') or f.endswith('.xml'), files):
        print(f"processing {filename}")
        path = os.path.join(directory_path, filename)

        grounds = extract_surfaces(path, "GroundSurface", extract_ground_attributes)
        ground_surfaces.append(grounds)

        roofs = extract_surfaces(path, "RoofSurface", extract_roof_attributes)
        roof_surfaces.append(roofs)

    return dict(
        ground=gpd.GeoDataFrame(pd.concat(ground_surfaces), crs=target_crs),
        roof=gpd.GeoDataFrame(pd.concat(roof_surfaces), crs=target_crs)
    )


def convert(directory_path, output_geojson_path):
    Path(output_geojson_path).mkdir(parents=True, exist_ok=True)
    ret = extract_all_surface_types(directory_path)
    for name, df in ret.items():
        outfile = os.path.join(output_geojson_path, f"{name}.geojson")
        df.to_file(outfile, driver='GeoJSON')
