from app.services.safety_source_adapters.nhtsa import parse_vehicle_query


def test_parse_vehicle_query_year_first():
    vehicle = parse_vehicle_query("2020 Honda Civic")

    assert vehicle is not None
    assert vehicle.model_year == "2020"
    assert vehicle.make == "Honda"
    assert vehicle.model == "Civic"
    assert vehicle.query_label == "2020 Honda Civic"


def test_parse_vehicle_query_year_last():
    vehicle = parse_vehicle_query("Honda Civic 2020")

    assert vehicle is not None
    assert vehicle.model_year == "2020"
    assert vehicle.make == "Honda"
    assert vehicle.model == "Civic"
    assert vehicle.query_label == "2020 Honda Civic"


def test_parse_vehicle_query_multi_token_model():
    vehicle = parse_vehicle_query("Ford F-150 2021")

    assert vehicle is not None
    assert vehicle.model_year == "2021"
    assert vehicle.make == "Ford"
    assert vehicle.model == "F-150"
    assert vehicle.query_label == "2021 Ford F-150"


def test_parse_vehicle_query_requires_year_and_model():
    assert parse_vehicle_query("Honda Civic") is None
    assert parse_vehicle_query("2020 Honda") is None
