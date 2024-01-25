from flask.testing import FlaskClient
import pathmagic
import urllib.parse
assert pathmagic


def test_endpoint_no_parameters_retuns_all(client: FlaskClient, snapshot):
    response = client.get('/features')

    assert response.status_code == 200
    assert response.json == snapshot


def test_endpoint_with_bbox_returns_empty(client: FlaskClient, snapshot) -> None:
    response = client.get(
        '/features?bbox=10.039595125418998,53.58188067839408,10.042624874581003,53.58367932160592')

    assert response.status_code == 200
    assert response.json == snapshot


def test_endpoint_with_bbox_returns_correct_features(client: FlaskClient, snapshot) -> None:
    response = client.get(
        '/features?bbox=10.315909,53.446486,10.316386,53.446842')

    assert response.status_code == 200
    actual = response.json
    actual["features"] = [f["properties"]["id"] for f in actual["features"]]
    assert actual == snapshot


def test_endpoint_with_bbox_enclosing_all_returns_all(client: FlaskClient, snapshot) -> None:
    response = client.get('/features?bbox=-180,-90,180,90')
    assert response.status_code == 200
    actual = response.json
    actual["features"] = [f["properties"]["id"] for f in actual["features"]]
    assert actual == snapshot


def test_endpoint_with_limit(client: FlaskClient, snapshot) -> None:
    response = client.get('/features?bbox=-180,-90,180,90&limit=1&startindex=0')

    assert response.status_code == 200
    actual = response.json
    actual["features"] = [f["properties"]["id"] for f in actual["features"]]
    assert actual == snapshot


def test_endpoint_with_limit_returns_prev_and_next(client: FlaskClient, snapshot) -> None:
    response = client.get('/features?bbox=-180,-90,180,90&limit=1&startindex=1')

    assert response.status_code == 200
    actual = response.json
    actual["features"] = [f["properties"]["id"] for f in actual["features"]]
    assert actual == snapshot


def test_endpoint_with_filter_ground(client: FlaskClient) -> None:
    response = client.get('/features?surface_type=ground')

    assert response.status_code == 200
    actual = response.json
    assert (len(actual["features"])) == 2


def test_endpoint_with_filter_roof(client: FlaskClient) -> None:
    response = client.get('/features?surface_type=roof')

    assert response.status_code == 200
    actual = response.json
    assert (len(actual["features"])) == 3


def test_endpoint_with_filter_id(client: FlaskClient) -> None:
    response = client.get("/features?properties=id")

    assert response.status_code == 200
    actual = response.json
    assert actual["features"][0]["properties"] == {
        "id": "DEHH_2cfcae78-56f5-4a77-b74d-51cce7cc3d3e_2_poly"
    }


def test_endpoint_with_filter_id_and_lage(client: FlaskClient) -> None:
    response = client.get("/features?properties=id,lage")

    assert response.status_code == 200
    actual = response.json
    assert actual["features"][0]["properties"] == {
        "id": "DEHH_2cfcae78-56f5-4a77-b74d-51cce7cc3d3e_2_poly",
        "lage": "1000",
    }


def test_endpoint_with_filter_invalid_property(client: FlaskClient) -> None:
    response = client.get("/features?properties=id,invalid")

    assert response.status_code == 200
    actual = response.json
    assert actual["features"][0]["properties"] == {
        "id": "DEHH_2cfcae78-56f5-4a77-b74d-51cce7cc3d3e_2_poly",
    }


def test_endpoint_with_bpoly_returns_correct_features(client: FlaskClient) -> None:
    polygon_str = "10.315909,53.446486;10.315909,53.446842;10.316386,53.446842;10.316386,53.446486;10.315909,53.446486"
    response = client.get(f'/features?bounding_polygon={polygon_str}')

    assert response.status_code == 200
    actual = response.json
    ids = [f["properties"]["id"] for f in actual["features"]]
    assert ids == [
        'DEHH_2cfcae78-56f5-4a77-b74d-51cce7cc3d3e_2_poly',
        'DEHH_d1c15e0c-707a-4734-abea-2a1f810c1890_2_poly',
        'DEHH_1fd3c3ef-fc46-4024-ac10-3b272044391d_2_poly']


def test_endpoint_with_bpoly_urlencoded(client: FlaskClient) -> None:
    polygon_str = "10.315909,53.446486;10.315909,53.446842;10.316386,53.446842;10.316386,53.446486;10.315909,53.446486"
    encoded_polygon = urllib.parse.quote(polygon_str)
    url = f"/features?bounding_polygon={encoded_polygon}"

    response = client.get(url)

    assert response.status_code == 200
    actual = response.json
    ids = [f["properties"]["id"] for f in actual["features"]]
    assert ids == [
        'DEHH_2cfcae78-56f5-4a77-b74d-51cce7cc3d3e_2_poly',
        'DEHH_d1c15e0c-707a-4734-abea-2a1f810c1890_2_poly',
        'DEHH_1fd3c3ef-fc46-4024-ac10-3b272044391d_2_poly']


def test_endpoint_with_intersect(client: FlaskClient, snapshot) -> None:
    response = client.get(
        '/features?bbox=10.315909,53.446486,10.316386,53.446842&intersect=true')

    assert response.status_code == 200
    actual = response.json
    assert actual == snapshot


def test_endpoint_with_bpoly_and_intersect(client: FlaskClient, snapshot) -> None:
    polygon_str = "10.315909,53.446486;10.315909,53.446842;10.316386,53.446842;10.316386,53.446486;10.315909,53.446486"
    response = client.get(f'/features?bounding_polygon={polygon_str}&intersect=true')

    assert response.status_code == 200
    actual = response.json
    assert actual == snapshot
