import geopandas as gpd
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
import pandas as pd
import os


def parse_citygml_footprints(citygml_file_path, original_crs, target_crs='EPSG:4326'):
    tree = ET.parse(citygml_file_path)
    root = tree.getroot()

    ns = {
        'gml': 'http://www.opengis.net/gml',
        'bldg': 'http://www.opengis.net/citygml/building/1.0'
    }

    buildings = root.findall('.//bldg:Building', ns)
    print(f"found {len(buildings)} buildings")

    footprints = []
    for building in buildings:
        # Extract the ground surface polygons (or lod2TerrainIntersection)
        ground_surfaces = building.findall('.//bldg:GroundSurface//gml:Polygon', ns)

        for surface in ground_surfaces:
            exterior_coords = surface.find('.//gml:exterior//gml:LinearRing', ns)
            coords = []

            if exterior_coords is not None:
                for coord in exterior_coords.findall('./gml:pos', ns):
                    x, y = map(float, coord.text.split()[:2])  # Only take X and Y for 2D footprint
                    # coords.append((x, y))
                    coords.append((x, y))

                if coords:
                    polygon = Polygon(coords)
                    footprints.append(polygon)

    print(f"found {len(footprints)} footprints")

    return gpd.GeoDataFrame(geometry=footprints, crs=original_crs).to_crs(target_crs)


def process_directory(directory_path, original_crs, output_geojson_path, target_crs='EPSG:4326'):
    all_footprints = []

    for filename in os.listdir(directory_path):
        if filename.endswith('.gml') or filename.endswith('.xml'):
            file_path = os.path.join(directory_path, filename)
            gdf = parse_citygml_footprints(file_path, original_crs, target_crs)
            all_footprints.append(gdf)

    combined_gdf = gpd.GeoDataFrame(pd.concat(all_footprints, ignore_index=True), crs=target_crs)
    combined_gdf.to_file(output_geojson_path, driver='GeoJSON')


def write_to_geojson(gdf, output_file_path):
    gdf.to_file(output_file_path, driver='GeoJSON')


def main():
    output_geojson_path = './data/out/footprints.geojson'
    process_directory("./data/LoD2_CityGML_HH_2016", 'EPSG:25832', output_geojson_path)


if __name__ == "__main__":
    main()
