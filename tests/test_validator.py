from services.validator import validate_registration_number, validate_semester

def test_valid_reg_no():
    assert validate_registration_number("1234567890") == (True, "")

def test_short_reg_no():
    valid, msg = validate_registration_number("12345")
    assert not valid
    assert "format" in msg.lower() or "must be 10-12 digits" in msg.lower()

def test_invalid_semester():
    valid, msg = validate_semester(9)
    assert not valid

def test_valid_semester():
    assert validate_semester(4) == (True, "")
