from services.beu_api import normalize_result


def test_normalize_handles_real_api_response():
    """normalize_result should parse a real BEU API data payload correctly."""
    real_response = {
        "semester": "II",
        "exam_held": "November/2025",
        "redg_no": 24153125054,
        "name": "SHIVAM KUMAR",
        "father_name": "RAM NAVMI KUMAR",
        "mother_name": "HEMANTI GUPTA",
        "college_code": 125,
        "college_name": "RASHTRAKAVI RAMDHARI SINGH DINKAR COLLEGE OF ENGINEERING, BEGUSARAI",
        "course_code": 153,
        "course": "Computer Science and Engineering (Data Science)",
        "examYear": 2025,
        "theorySubjects": [
            {"code": "100202", "name": "Engineering Mathematics-II", "ese": "25", "ia": "20", "total": "45", "grade": "P", "credit": "4"},
            {"code": "100215", "name": "Engineering Chemistry", "ese": "40", "ia": "21", "total": "61", "grade": "C", "credit": "3"},
        ],
        "practicalSubjects": [
            {"code": "100215P", "name": "Engineering Chemistry Lab", "ese": "25", "ia": "18", "total": "43", "grade": "A", "credit": "1"},
        ],
        "sgpa": ["8.4", "7.6", "-", "-", "-", "-", "-", "-"],
        "cgpa": "8",
        "fail_any": "PASS",
    }
    result = normalize_result(real_response)

    assert result.reg_no == "24153125054"
    assert result.student_name == "SHIVAM KUMAR"
    assert result.semester == 2
    assert result.sgpa == 7.6  # semester II = index 1
    assert result.cgpa == 8.0
    assert result.overall_status == "PASS"
    assert len(result.subjects) == 3  # 2 theory + 1 practical
    assert result.subjects[0].subject_name == "Engineering Mathematics-II"
    assert result.subjects[0].obtained_marks == 45
    assert result.subjects[0].max_marks == 100  # theory
    assert result.subjects[0].is_pass is True
    assert result.subjects[2].max_marks == 50   # practical
    assert result.subjects[2].is_practical is True


def test_normalize_handles_missing_fields():
    """normalize_result should not crash on minimal data."""
    minimal_response = {
        "redg_no": "24153125041",
        "semester": "I",
        "theorySubjects": [],
        "practicalSubjects": [],
        "sgpa": ["-", "-", "-", "-", "-", "-", "-", "-"],
        "fail_any": "PASS",
    }
    result = normalize_result(minimal_response)
    assert result.reg_no == "24153125041"
    assert result.semester == 1
    assert result.subjects == []
    assert result.sgpa is None


def test_normalize_detects_fail():
    """Should correctly detect failed subjects from grade."""
    response = {
        "redg_no": "24153125099",
        "semester": "III",
        "theorySubjects": [
            {"code": "200301", "name": "DSA", "ese": "10", "ia": "5", "total": "15", "grade": "F", "credit": "4"},
        ],
        "practicalSubjects": [],
        "sgpa": ["-", "-", "-", "-", "-", "-", "-", "-"],
        "fail_any": "FAIL",
    }
    result = normalize_result(response)
    assert result.subjects[0].is_pass is False
    assert result.overall_status == "FAIL"
