import sqlite3
import os
import json
from geojson import load
from shapely.geometry import shape

TABLE_NAME = 'features'


def init_spatialite(db_conn):
    db_conn.enable_load_extension(True)
    db_conn.load_extension("mod_spatialite")
    db_conn.execute('SELECT InitSpatialMetadata(1)')


def create_table(db_conn):
    db_conn.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            geojson TEXT
        )
    ''')
    db_conn.execute(f'''
        SELECT AddGeometryColumn('{TABLE_NAME}', 'geom', 4326, 'POLYGON', 'XY')
    ''')


def insert_data(db_conn, feature):
    wkt = shape(feature['geometry']).wkt
    geojson_str = json.dumps(feature)
    db_conn.execute(f'''
        INSERT INTO {TABLE_NAME} (geojson, geom)
        VALUES (?, GeomFromText(?, 4326))
    ''', (geojson_str, wkt))


def load_file(filepath, db_conn):
    with open(filepath, 'r') as file:
        geojson_data = load(file)
        # print(f"will put {len(geojson_data['features'])} features into db")

        for feature in geojson_data['features']:
            if feature['geometry']['type'] == 'Polygon':
                insert_data(db_conn, feature)


def create_db(geojson_dir, db_path):
    db_conn = sqlite3.connect(db_path)
    init_spatialite(db_conn)
    create_table(db_conn)

    load_file(os.path.join(geojson_dir, "ground.geojson"), db_conn)
    load_file(os.path.join(geojson_dir, "roof.geojson"), db_conn)

    db_conn.commit()
    db_conn.close()
