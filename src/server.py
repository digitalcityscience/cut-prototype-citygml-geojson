from flask import Flask, request, jsonify, url_for
from sqlalchemy import create_engine, event, text
import json
from datetime import datetime

TABLE_NAME = 'features'


class Server:
    def __init__(self, port, db_path):
        self.port = port
        self.app = Flask(__name__)
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.setup_db()

        @self.app.route('/')
        def index():
            return 'empty'

        @self.app.route('/features')
        def features():
            bbox = request.args.get(
                'bbox', default="-180,-90,180,90")
            bbox_values = [float(val) for val in bbox.split(',')]

            surface_type = request.args.get('surface_type', default=None, type=str)

            if len(bbox_values) != 4:
                return jsonify({'error': 'Invalid bbox parameter'}), 400

            min_lon, min_lat, max_lon, max_lat = bbox_values

            limit = request.args.get('limit', default=100, type=int)  # Number of items per request
            startindex = request.args.get('startindex', default=0, type=int)  # Starting index for items

            base_sql = f"FROM {TABLE_NAME} WHERE MbrWithin(geom, BuildMbr(:min_lon, :min_lat, :max_lon, :max_lat))"

            # Add surface type filter if provided
            if surface_type:
                base_sql += " AND json_extract(geojson, '$.properties.surface_type') = :surface_type"

            count_sql = text(f"SELECT COUNT(*) {base_sql}")
            sql = text(f"SELECT id, geojson {base_sql} LIMIT :limit OFFSET :startindex")

            # count_sql = text(f"""
            #     SELECT COUNT(*)
            #     FROM {TABLE_NAME}
            #     WHERE MbrWithin(geom, BuildMbr(:min_lon, :min_lat, :max_lon, :max_lat))
            # """)

            # sql = text(f"""
            #     SELECT id, geojson
            #     FROM {TABLE_NAME}
            #     WHERE MbrWithin(geom, BuildMbr(:min_lon, :min_lat, :max_lon, :max_lat))
            #     LIMIT :limit OFFSET :startindex
            # """)

            with self.engine.connect() as conn:

                query_params = {
                    'min_lat': min_lat, 'min_lon': min_lon,
                    'max_lat': max_lat, 'max_lon': max_lon,
                }

                if surface_type:
                    query_params['surface_type'] = surface_type

                total_count = conn.execute(count_sql, query_params).scalar()

                query_params['limit'] = limit
                query_params['startindex'] = startindex

                result = conn.execute(sql, query_params)
                features = [json.loads(row[1]) for row in result]

            # Generate navigation links

            base_url = url_for('features', _external=True)

            links = []

            if startindex > 0:
                prev_index = max(startindex - limit, 0)
                links.append({"href": f"{base_url}?limit={limit}&startindex={prev_index}",
                             "rel": "prev", "type": "application/json"})

            if startindex + limit < total_count:
                next_index = startindex + limit
                links.append({"href": f"{base_url}?limit={limit}&startindex={next_index}",
                             "rel": "next", "type": "application/json"})

            return jsonify({
                'type': 'FeatureCollection',
                'features': features,
                'links': links,
                'timeStamp': datetime.utcnow().isoformat() + 'Z',  # Include a timestamp
                'numberMatched': total_count,
                'numberReturned': len(features),
            })

    def setup_db(self):
        @event.listens_for(self.engine, "connect")
        def load_spatialite(dbapi_connection, connection_record):
            dbapi_connection.enable_load_extension(True)
            dbapi_connection.execute('SELECT load_extension("mod_spatialite")')

    def run(self, debug=True):
        self.app.run(debug=debug, port=self.port, host="0.0.0.0")
