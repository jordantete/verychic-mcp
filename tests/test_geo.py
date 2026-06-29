from verychic_mcp.geo import haversine_km


def test_haversine_known_distance_paris_london():
    # Paris (48.8566, 2.3522) to London (51.5074, -0.1278) is ~343.6 km.
    d = haversine_km(48.8566, 2.3522, 51.5074, -0.1278)
    assert abs(d - 343.6) < 2.0


def test_haversine_zero_for_identical_points():
    assert haversine_km(48.8566, 2.3522, 48.8566, 2.3522) == 0.0
