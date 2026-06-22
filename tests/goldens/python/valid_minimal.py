import calculator


def test_adds_two_numbers():
    result = calculator.add(a=2, b=3)
    assert result == 5
