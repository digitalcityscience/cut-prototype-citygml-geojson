from flask.testing import FlaskClient
import pathmagic
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
