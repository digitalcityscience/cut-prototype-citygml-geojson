from typing import Dict, Union, Optional, Callable
import geopandas as gpd
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
import pandas as pd
import os
from pathlib import Path

ns: Dict[str, str] = {
    'gml': 'http://www.opengis.net/gml',
    'bldg': 'http://www.opengis.net/citygml/building/1.0',
    'gen': 'http://www.opengis.net/citygml/generics/1.0',
}

target_crs: str = 'EPSG:4326'
original_crs: str = 'EPSG:25832'


def get_attrib(path: str, building: ET.Element) -> Optional[str]:
    element: Optional[ET.Element] = building.find(path, ns)
    return element.text if element is not None else None


def get_ground_attributes(building: ET.Element) -> Dict[str, Optional[str]]:
    return {
        "lage": get_attrib('.//gen:stringAttribute[@name="DatenquelleLage"]/gen:value', building),
        "bodenhoehe": get_attrib('.//gen:stringAttribute[@name="DatenquelleBodenhoehe"]/gen:value', building),
        "dachhoehe": get_attrib('.//gen:stringAttribute[@name="DatenquelleDachhoehe"]/gen:value', building),
        "geschossanzahl": get_attrib('.//gen:stringAttribute[@name="DatenquelleGeschossanzahl"]/gen:value', building),
        "Geometrietyp2DReferenz": get_attrib(
            './/gen:stringAttribute[@name="Geometrietyp2DReferenz"]/gen:value',
            building
        ),
        "Grundrissaktualitaet": get_attrib('.//gen:stringAttribute[@name="Grundrissaktualitaet"]/gen:value', building),
        "function": get_attrib('bldg:function', building),
        "roofType": get_attrib('bldg:roofType', building),
        "measuredHeight": get_attrib('bldg:measuredHeight', building),
        "storeysAboveGround": get_attrib('bldg:storeysAboveGround', building)
    }


def extract_ground_attributes(polygon: ET.Element, building: ET.Element) -> Dict[str, Union[str, Optional[str]]]:
    id: str = polygon.attrib["{http://www.opengis.net/gml}id"]
    attributes: Dict[str, Optional[str]] = get_ground_attributes(building)
    attributes["id"] = id
    attributes["surface_type"] = "ground"
    return attributes


def extract_roof_attributes(polygon: ET.Element, building: ET.Element) -> Dict[str, str]:
    id = polygon.attrib["{http://www.opengis.net/gml}id"]
    attributes = {}
    attributes["surface_type"] = "roof"
    attributes["id"] = id
    return attributes


def extract_coords(linearRing: ET.Element):
    posLists = linearRing.findall('./gml:posList', ns)
    assert len(posLists) == 1
    posList = posLists[0]
    split_str = posList.text.split()
    coords = [tuple(map(float, split_str[i:i + 2])) for i in range(0, len(split_str), 3)]
    return coords


def extract_geometry(polygon: ET.Element) -> Polygon:
    exterior = polygon.find('.//gml:exterior//gml:LinearRing', ns)
    assert exterior is not None
    exterior_coords = extract_coords(exterior)

    holes = []
    for interior in polygon.findall('.//gml:interior//gml:LinearRing', ns):
        holes.append(extract_coords(interior))

    return Polygon(exterior_coords, holes)


def extract_surfaces(
    citygml_file_path: str,
    node: str,
    extract_attributes: Callable[[ET.Element, ET.Element], Dict]
) -> gpd.GeoDataFrame:
    tree = ET.parse(citygml_file_path)
    root = tree.getroot()
    buildings = root.findall('.//bldg:Building', ns)

    all_features, all_attributes = [], []
    for building in buildings:
        for surface in building.findall(f'.//bldg:{node}', ns):
            assert len(surface.findall('.//bldg:lod2MultiSurface', ns)) == 1

            multiSurfaces = surface.findall('.//gml:MultiSurface', ns)
            assert len(multiSurfaces) == 1
            multiSurface = multiSurfaces[0]

            polygons = multiSurface.findall('.//gml:Polygon', ns)
            assert len(polygons) == 1
            polygon = polygons[0]

            attributes = extract_attributes(polygon, building)
            geometry = extract_geometry(polygon)
            all_attributes.append(attributes)
            all_features.append(geometry)

    gdf = gpd.GeoDataFrame(geometry=all_features, crs=original_crs).assign(**pd.DataFrame(all_attributes))
    gdf.set_index('id', inplace=True)
    return gdf.to_crs(target_crs)


def extract_all_surface_types(directory_path: str) -> Dict[str, gpd.GeoDataFrame]:
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


def convert(directory_path: str, output_geojson_path: str) -> None:
    Path(output_geojson_path).mkdir(parents=True, exist_ok=True)
    ret = extract_all_surface_types(directory_path)
    for name, df in ret.items():
        outfile = os.path.join(output_geojson_path, f"{name}.geojson")
        df.to_file(outfile, driver='GeoJSON')
