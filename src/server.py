from flask import Flask, request, jsonify, url_for, Response
from sqlalchemy import create_engine, event, text
import json
from datetime import datetime
from flask_swagger_ui import get_swaggerui_blueprint

TABLE_NAME: str = "features"


class Server:
    def __init__(self, port: str, db_path: str) -> None:

        self.port = port
        self.app = Flask(__name__)
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.setup_db()

        swaggerui_blueprint = get_swaggerui_blueprint(
            "", "/static/swagger.json", config={"app_name": "HCU-CUT"}
        )
        self.app.register_blueprint(swaggerui_blueprint)

        @self.app.route("/features")
        def features() -> Response:
            bbox = request.args.get("bbox")
            bounding_polygon = request.args.get("bounding_polygon")

            if (bbox is not None) and (bounding_polygon is not None):
                return jsonify(
                    {"error": "Either bbox or bounding_polygon must be set, but not both"}
                ), 400

            intersect = request.args.get("intersect", default="false").lower() == "true"

            select_geom = "geojson"
            if intersect:
                geo = "GeomFromText(:polygon_wkt)" if bounding_polygon \
                    else "BuildMbr(:min_lon, :min_lat, :max_lon, :max_lat)"
                select_geom += f", AsGeoJSON(ST_Intersection(geom, {geo})) as inter_geom"

            surface_type = request.args.get("surface_type", default=None, type=str)

            limit = request.args.get(
                "limit", default=100, type=int
            )  # Number of items per request
            startindex = request.args.get(
                "startindex", default=0, type=int
            )  # Starting index for items

            base_sql = f"FROM {TABLE_NAME}"
            conditions = []
            if bounding_polygon:
                try:
                    polygon_coords = bounding_polygon.split(";")
                    polygon_points = [tuple(map(float, coord.split(","))) for coord in polygon_coords]
                    polygon_wkt = "POLYGON((" + ", ".join(f"{lon} {lat}" for lon, lat in polygon_points) + "))"
                    if intersect:
                        conditions.append("ST_Intersects(geom, GeomFromText(:polygon_wkt))")
                    else:
                        conditions.append("MbrWithin(geom, GeomFromText(:polygon_wkt))")
                except (ValueError, TypeError):
                    return jsonify({"error": "Invalid bounding_polygon parameter"}), 400
            elif bbox:
                bbox_values = [float(val) for val in bbox.split(",")]
                if len(bbox_values) != 4:
                    return jsonify({"error": "Invalid bbox parameter"}), 400
                min_lon, min_lat, max_lon, max_lat = bbox_values
                if intersect:
                    conditions.append("ST_Intersects(geom, BuildMbr(:min_lon, :min_lat, :max_lon, :max_lat))")
                else:
                    conditions.append("MbrWithin(geom, BuildMbr(:min_lon, :min_lat, :max_lon, :max_lat))")

            if surface_type:
                conditions.append("json_extract(geojson, '$.properties.surface_type') = :surface_type")

            if conditions:
                stmts = " AND ".join(conditions)
                base_sql += f" WHERE {stmts}"

            count_sql = text(f"SELECT COUNT(*) {base_sql}")
            sql = text(f"SELECT id, {select_geom} {base_sql} LIMIT :limit OFFSET :startindex")

            with self.engine.connect() as conn:
                query_params = {
                    "min_lat": min_lat,
                    "min_lon": min_lon,
                    "max_lat": max_lat,
                    "max_lon": max_lon,
                } if bbox else {}

                if surface_type:
                    query_params["surface_type"] = surface_type

                if bounding_polygon:
                    query_params["polygon_wkt"] = polygon_wkt

                total_count = conn.execute(count_sql, query_params).scalar()

                query_params["limit"] = limit
                query_params["startindex"] = startindex

                result = conn.execute(sql, query_params)

                if intersect:
                    features = []
                    for _, gjson, inter in result:
                        feature = json.loads(gjson)
                        feature['geometry'] = json.loads(inter)
                        features.append(feature)
                else:
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
                    "timeStamp": datetime.utcnow().isoformat() + "Z",  # Include a timestamp
                    "numberMatched": total_count,
                    "numberReturned": len(features),
                }
            )

    def setup_db(self) -> None:
        @ event.listens_for(self.engine, "connect")
        def load_spatialite(dbapi_connection, connection_record):
            dbapi_connection.enable_load_extension(True)
            dbapi_connection.execute('SELECT load_extension("mod_spatialite")')

    def run(self, debug: bool = True) -> None:
        self.app.run(debug=debug, port=self.port, host="0.0.0.0")
