from util import abs_floor_minimum, to_degrees_east, get_first_key

def test_abs_floor_minimum():
    assert abs_floor_minimum(3.1,-6.7) == 6

def test_to_degrees_east():
    for lon in range(-180, 181):
        result = to_degrees_east(lon)
        assert 0 <= result < 360

def test_get_first_key():
    assert get_first_key(["test","test2"]) == "test"