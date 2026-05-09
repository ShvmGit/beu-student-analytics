import re

def validate_registration_number(reg_no: str) -> tuple[bool, str]:
    """
    BEU registration numbers are typically 10-digit numeric strings.
    Pattern: r'^\\d{10,12}$'  (adjust if actual format differs)
    Returns (True, "") on valid.
    Returns (False, "error message") on invalid.
    """
    if re.match(r'^\d{10,12}$', reg_no):
        return (True, "")
    return (False, "Registration number must be 10-12 digits in format.")

def validate_semester(semester: int) -> tuple[bool, str]:
    """
    Valid range: 1 to 8 (4-year engineering program).
    Returns (True, "") on valid.
    Returns (False, "Semester must be between 1 and 8") on invalid.
    """
    if 1 <= semester <= 8:
        return (True, "")
    return (False, "Semester must be between 1 and 8")

def sanitize_input(text: str) -> str:
    """Strip whitespace. Remove non-alphanumeric chars from reg_no. Lowercase."""
    return re.sub(r'[^a-zA-Z0-9]', '', text.strip()).lower()
