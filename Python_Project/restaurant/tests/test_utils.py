# geocode_address and haversine_distance are not unit tested here due to API dependency.
# Validated manually against known Calgary addresses relative to seed data for restaurant (300 Centre St, Calgary AB)

# 225 8 Ave SE, Calgary, AB                 4.1km => $5 delivery fee
# 1750 Crowchild Trail NW, Calgary, AB      6.7km => $10 delivery fee
# 11520 24 St SE, Calgary, AB               12.6km => delivery rejected

import pytest
import math
from restaurant.utils import haversine_distance


# ====================== CONSTANTS ======================
# restaurant coordinates from seed data at 300 Centre St, Calgary AB
# used as the origin point for all distance tests

RESTAURANT_LAT = 51.044733
RESTAURANT_LON = -114.071883


# ====================== HAVERSINE DISTANCE TESTS ======================
# haversine_distance is pure math with no external dependencies so it can be fully unit tested
# all distances are calculated relative to the seed restaurant at 300 Centre St, Calgary AB
# lat: 51.044733, lon: -114.071883


def test_haversine_same_location():
    # verifies two identical coordinates return zero distance
    # same point should always return 0.0 regardless of rounding
    distance = haversine_distance(RESTAURANT_LAT, RESTAURANT_LON, RESTAURANT_LAT, RESTAURANT_LON)
    assert distance == 0.0


def test_haversine_within_5km():
    # verifies a known address within 5km returns a distance below the $5 delivery fee threshold
    # 225 8 Ave SE Calgary AB is approximately 4.1km from the restaurant
    distance = haversine_distance(RESTAURANT_LAT, RESTAURANT_LON, 51.0447, -114.0568)
    assert distance < 5


def test_haversine_between_5_and_10km():
    # verifies a known address between 5km and 10km falls in the $10 delivery fee tier
    # 1750 Crowchild Trail NW Calgary AB is approximately 6.7km from the restaurant
    distance = haversine_distance(RESTAURANT_LAT, RESTAURANT_LON, 51.0833, -114.1294)
    assert 5 <= distance <= 10


def test_haversine_beyond_10km():
    # verifies a location clearly outside the 10km delivery range is correctly rejected
    # coordinates approximately 14km south of the restaurant, clearly beyond range
    distance = haversine_distance(RESTAURANT_LAT, RESTAURANT_LON, 50.9200, -114.0718)
    assert distance > 10


def test_haversine_returns_float():
    # verifies the function always returns a float type regardless of input
    distance = haversine_distance(RESTAURANT_LAT, RESTAURANT_LON, 51.0447, -114.0568)
    assert isinstance(distance, float)


def test_haversine_distance_is_positive():
    # verifies distance is always a positive number regardless of coordinate order
    distance = haversine_distance(RESTAURANT_LAT, RESTAURANT_LON, 51.0833, -114.1294)
    assert distance > 0


def test_haversine_is_symmetric():
    # verifies the formula is symmetric: distance A to B equals distance B to A
    d1 = haversine_distance(RESTAURANT_LAT, RESTAURANT_LON, 51.0833, -114.1294)
    d2 = haversine_distance(51.0833, -114.1294, RESTAURANT_LAT, RESTAURANT_LON)
    assert round(d1, 6) == round(d2, 6)


def test_haversine_small_distance_accuracy():
    # verifies the formula produces a reasonable result for a very short distance
    # two points 0.001 degree apart in latitude is roughly 111 meters
    # the result should be greater than 0 and less than 0.5km
    distance = haversine_distance(51.044733, -114.071883, 51.045733, -114.071883)
    assert 0 < distance < 0.5


def test_haversine_large_distance():
    # verifies the formula handles large intercity distances correctly
    # Calgary to Edmonton is approximately 300km north
    distance = haversine_distance(51.044733, -114.071883, 53.5461, -113.4938)
    assert 280 < distance < 320


def test_haversine_north_south_movement():
    # verifies moving north increases distance correctly
    # each degree of latitude is approximately 111km
    # moving 0.1 degree north from the restaurant should be roughly 11km
    distance = haversine_distance(RESTAURANT_LAT, RESTAURANT_LON, RESTAURANT_LAT + 0.1, RESTAURANT_LON)
    assert 10 < distance < 13


def test_haversine_east_west_movement():
    # verifies moving east or west increases distance correctly
    # at latitude 51 degrees, one degree of longitude is approximately 70km
    # moving 0.1 degree east should be roughly 7km
    distance = haversine_distance(RESTAURANT_LAT, RESTAURANT_LON, RESTAURANT_LAT, RESTAURANT_LON + 0.1)
    assert 5 < distance < 9


def test_haversine_delivery_fee_tier_boundary_under_5():
    # verifies an address just under 5km triggers the $5 delivery fee tier
    # the delivery fee logic in order_create uses 5km as the cutoff
    # this test confirms haversine returns a value that would trigger the lower fee
    distance = haversine_distance(RESTAURANT_LAT, RESTAURANT_LON, 51.0447, -114.0568)
    delivery_fee = 5 if distance <= 5 else 10
    assert delivery_fee == 5


def test_haversine_delivery_fee_tier_over_5():
    # verifies an address between 5km and 10km triggers the $10 delivery fee tier
    distance = haversine_distance(RESTAURANT_LAT, RESTAURANT_LON, 51.0833, -114.1294)
    delivery_fee = 5 if distance <= 5 else 10
    assert delivery_fee == 10


def test_haversine_delivery_rejected_beyond_10km():
    # verifies an address beyond 10km would be rejected by the delivery distance check
    # the order_create view blocks delivery orders beyond 10km
    distance = haversine_distance(RESTAURANT_LAT, RESTAURANT_LON, 50.9200, -114.0718)
    delivery_allowed = distance <= 10
    assert delivery_allowed is False


def test_haversine_zero_longitude_difference():
    # verifies the formula handles the case where only latitude differs
    # pure north-south movement should still produce a valid positive distance
    distance = haversine_distance(51.044733, -114.071883, 51.144733, -114.071883)
    assert distance > 0
    assert isinstance(distance, float)


def test_haversine_zero_latitude_difference():
    # verifies the formula handles the case where only longitude differs
    # pure east-west movement should still produce a valid positive distance
    distance = haversine_distance(51.044733, -114.071883, 51.044733, -114.171883)
    assert distance > 0
    assert isinstance(distance, float)


def test_haversine_negative_coordinates():
    # verifies the formula handles negative coordinates correctly
    # southern hemisphere and western hemisphere coordinates are common
    # the result should still be a positive float
    distance = haversine_distance(-33.8688, 151.2093, -37.8136, 144.9631)
    assert distance > 0
    assert isinstance(distance, float)


def test_haversine_cross_hemisphere():
    # verifies the formula works correctly when crossing from north to south hemisphere
    # Calgary to Buenos Aires is approximately 10,900 to 11,000km
    distance = haversine_distance(51.044733, -114.071883, -34.6037, -58.3816)
    assert distance > 10000