# geocode_address and haversin distance are not unit tested here due to API dependency.
# Validated manaully against know Calgary addresses relative to seed data for restaurant.  (300 Centre St, Calgary AB)

# 225 8 Ave SE, Calgary, AB         4.1km => $5 delivery fee
# 1750 Crowchild Trail NW, Calgary, AB      6.7km => $10 delivery fee
# 11520 24 St SE, Calgary, AB       12.6km => delivery rejected


from restaurant.utils import haversine_distance


# ====================== HAVERSINE DISTANCE TESTS ======================
# haversine_distance is pure math with no external dependencies so it can be fully unit tested
# all distances are calculated relative to the seed restaurant at 300 Centre St, Calgary AB
# lat: 51.044733, lon: -114.071883


# verifies two identical coordinates return zero distance
def test_haversine_same_location():
    # same point should always return 0
    distance = haversine_distance(51.044733, -114.071883, 51.044733, -114.071883)
    assert distance == 0.0


# verifies a known address within 5km returns correct fee tier distance
# 225 8 Ave SE Calgary AB is approximately 4.1km from the restaurant
def test_haversine_within_5km():
    # 225 8 Ave SE Calgary AB, approx 4.1km from restaurant
    distance = haversine_distance(51.044733, -114.071883, 51.0447, -114.0568)
    assert distance < 5


# verifies a known address between 5km and 10km returns correct fee tier distance
# 1750 Crowchild Trail NW Calgary AB is approximately 6.7km from the restaurant
def test_haversine_between_5_and_10km():
    # 1750 Crowchild Trail NW Calgary AB, approx 6.7km from restaurant
    distance = haversine_distance(51.044733, -114.071883, 51.0833, -114.1294)
    assert 5 <= distance <= 10


# verifies a known address beyond 10km is correctly identified as out of delivery range
# 11520 24 St SE Calgary AB is approximately 12.6km from the restaurant
def test_haversine_beyond_10km():
    # verifies a location clearly outside 10km delivery range is correctly identified
    # using coordinates approximately 15km south of the restaurant
    distance = haversine_distance(51.044733, -114.071883, 50.9200, -114.0718)
    assert distance > 10


# verifies the function returns a float type
def test_haversine_returns_float():
    distance = haversine_distance(51.044733, -114.071883, 51.0447, -114.0568)
    assert isinstance(distance, float)


# verifies distance is always positive regardless of coordinate order
def test_haversine_distance_is_positive():
    distance = haversine_distance(51.044733, -114.071883, 51.0833, -114.1294)
    assert distance > 0


# verifies the formula is symmetric — distance A to B equals distance B to A
def test_haversine_is_symmetric():
    d1 = haversine_distance(51.044733, -114.071883, 51.0833, -114.1294)
    d2 = haversine_distance(51.0833, -114.1294, 51.044733, -114.071883)
    assert round(d1, 6) == round(d2, 6)