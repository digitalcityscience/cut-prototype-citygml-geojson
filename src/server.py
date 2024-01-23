from flask import Flask, request, jsonify, url_for, Response, send_from_directory
from sqlalchemy import create_engine, event, text
import json
from datetime import datetime
from flask_swagger_ui import get_swaggerui_blueprint
import os

TABLE_NAME: str = "features"


class Server:
    def __init__(self, port: str, db_path: str) -> None:

        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        static_folder = os.path.join(parent_dir, 'static')

        self.port = port
        self.app = Flask(__name__, static_folder=static_folder)
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.setup_db()

        static_folder = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "static"
        )

        swaggerui_blueprint = get_swaggerui_blueprint(
            "", "/static/swagger.json", config={"app_name": "HCU-CUT"}
        )
        self.app.register_blueprint(swaggerui_blueprint)

        @self.app.route("/features")
        def features() -> Response:
            bbox = request.args.get("bbox", default="-180,-90,180,90")
            bbox_values = [float(val) for val in bbox.split(",")]

            surface_type = request.args.get("surface_type", default=None, type=str)

            if len(bbox_values) != 4:
                return jsonify({"error": "Invalid bbox parameter"}), 400

            min_lon, min_lat, max_lon, max_lat = bbox_values

            limit = request.args.get(
                "limit", default=100, type=int
            )  # Number of items per request
            startindex = request.args.get(
                "startindex", default=0, type=int
            )  # Starting index for items

            base_sql = f"FROM {TABLE_NAME} WHERE MbrWithin(geom, BuildMbr(:min_lon, :min_lat, :max_lon, :max_lat))"

            # Add surface type filter if provided
            if surface_type:
                base_sql += " AND json_extract(geojson, '$.properties.surface_type') = :surface_type"

            count_sql = text(f"SELECT COUNT(*) {base_sql}")
            sql = text(f"SELECT id, geojson {base_sql} LIMIT :limit OFFSET :startindex")

            with self.engine.connect() as conn:
                query_params = {
                    "min_lat": min_lat,
                    "min_lon": min_lon,
                    "max_lat": max_lat,
                    "max_lon": max_lon,
                }

                if surface_type:
                    query_params["surface_type"] = surface_type

                total_count = conn.execute(count_sql, query_params).scalar()

                query_params["limit"] = limit
                query_params["startindex"] = startindex

                result = conn.execute(sql, query_params)

                features = [json.loads(row[1]) for row in result]
                properties = request.args.get("properties")
                if properties:
                    properties = properties.split(",")
                    for feature in features:
                        props = feature["properties"]
                        feature["properties"] = {p: props[p] for p in properties if p in props}

            # Generate navigation links

            base_url = url_for("features", _external=True)

            links = []

            if startindex > 0:
                prev_index = max(startindex - limit, 0)
                links.append(
                    {
                        "href": f"{base_url}?limit={limit}&startindex={prev_index}",
                        "rel": "prev",
                        "type": "application/json",
                    }
                )

            if startindex + limit < total_count:
                next_index = startindex + limit
                links.append(
                    {
                        "href": f"{base_url}?limit={limit}&startindex={next_index}",
                        "rel": "next",
                        "type": "application/json",
                    }
                )

            return jsonify(
                {
                    "type": "FeatureCollection",
                    "features": features,
                    "links": links,
                    "timeStamp": datetime.utcnow().isoformat()
                    + "Z",  # Include a timestamp
                    "numberMatched": total_count,
                    "numberReturned": len(features),
                }
            )

    def setup_db(self) -> None:
        @event.listens_for(self.engine, "connect")
        def load_spatialite(dbapi_connection, connection_record):
            dbapi_connection.enable_load_extension(True)
            dbapi_connection.execute('SELECT load_extension("mod_spatialite")')

    def run(self, debug: bool = True) -> None:
        self.app.run(debug=debug, port=self.port, host="0.0.0.0")
