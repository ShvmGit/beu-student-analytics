from pydantic import BaseModel, Field, field_validator
from typing import Literal

# Roman numeral ↔ integer conversion for BEU semesters
ROMAN_TO_INT = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}
INT_TO_ROMAN = {v: k for k, v in ROMAN_TO_INT.items()}


def semester_roman_to_int(roman: str) -> int:
    """Convert roman numeral semester string to integer."""
    return ROMAN_TO_INT.get(roman.strip().upper(), 1)


def semester_int_to_roman(num: int) -> str:
    """Convert integer semester to roman numeral string."""
    return INT_TO_ROMAN.get(num, "I")


class Subject(BaseModel):
    subject_code: str
    subject_name: str
    max_marks: int = Field(ge=0)
    obtained_marks: int = Field(ge=0)
    grade: str | None = None
    credit: int = Field(default=0, ge=0)
    is_pass: bool = Field(default=True)
    is_practical: bool = Field(default=False)
    ese_marks: int | None = None   # End-semester exam marks
    ia_marks: int | None = None    # Internal assessment marks

    def model_post_init(self, __context):
        """Auto-compute pass from grade. 'F' = fail, anything else = pass."""
        if self.grade:
            self.is_pass = self.grade.upper() != "F"


class RawResult(BaseModel):
    """Normalized BEU result. Output of Agent B."""
    reg_no: str
    student_name: str | None = None
    father_name: str | None = None
    mother_name: str | None = None
    college_name: str | None = None
    course: str | None = None
    semester: int = Field(ge=1, le=8)
    sgpa: float | None = Field(default=None, ge=0.0, le=10.0)
    cgpa: float | None = Field(default=None, ge=0.0, le=10.0)
    overall_status: str | None = None  # "PASS" or "FAIL" from API fail_any
    subjects: list[Subject]
    total_max_marks: int = 0
    total_obtained_marks: int = 0

    def model_post_init(self, __context):
        """Auto-compute totals if not set."""
        if not self.total_max_marks:
            self.total_max_marks = sum(s.max_marks for s in self.subjects)
        if not self.total_obtained_marks:
            self.total_obtained_marks = sum(s.obtained_marks for s in self.subjects)
