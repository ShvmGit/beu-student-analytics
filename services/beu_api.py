import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
from schemas.result_schema import RawResult, Subject, semester_roman_to_int, semester_int_to_roman
from services.cache import get_cached, set_cached
from services.config import settings


class BEUAPIException(Exception):
    pass


class ResultNotFoundException(Exception):
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def call_beu_api(reg_no: str, semester: int) -> dict:
    """
    HTTP GET to BEU API. Retries 3 times with exponential backoff.
    Returns the unwrapped 'data' dict from the API response envelope.
    """
    semester_roman = semester_int_to_roman(semester)
    url = f"{settings.beu_api_base_url}/result/get-result"
    params = {
        "year": "2025",
        "redg_no": reg_no,
        "semester": semester_roman,
        "exam_held": "November/2025",
    }

    logger.info(f"BEU API call: {url} params={params}")

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()

        envelope = response.json()

        # Unwrap the API envelope: {"status": 200, "data": {...}}
        if isinstance(envelope, dict) and "data" in envelope:
            data = envelope["data"]
            if not data:
                raise ResultNotFoundException(
                    f"Result not found for {reg_no} Sem {semester_roman}"
                )
            return data

        # If the API returned something unexpected
        raise ResultNotFoundException(
            f"Unexpected API response format for {reg_no} Sem {semester_roman}"
        )


def _parse_subjects(raw_list: list[dict], is_practical: bool) -> list[Subject]:
    """Parse a list of theory or practical subjects from the real BEU API."""
    subjects = []
    # Max marks: theory = 100, practical = 50 (standard BEU pattern)
    default_max = 50 if is_practical else 100

    for s in raw_list or []:
        if not s:
            continue

        subject_name = s.get("name", "Unknown Subject")
        subject_code = str(s.get("code", "000"))

        try:
            obtained_marks = int(s.get("total") or 0)
        except (ValueError, TypeError):
            obtained_marks = 0

        try:
            ese = int(s.get("ese") or 0)
        except (ValueError, TypeError):
            ese = 0

        try:
            ia = int(s.get("ia") or 0)
        except (ValueError, TypeError):
            ia = 0

        try:
            credit = int(s.get("credit") or 0)
        except (ValueError, TypeError):
            credit = 0

        grade = s.get("grade")

        subjects.append(
            Subject(
                subject_code=subject_code,
                subject_name=subject_name,
                max_marks=default_max,
                obtained_marks=obtained_marks,
                grade=grade,
                credit=credit,
                is_practical=is_practical,
                ese_marks=ese,
                ia_marks=ia,
            )
        )

    return subjects


def normalize_result(raw: dict) -> RawResult:
    """
    Map real BEU API 'data' keys to clean RawResult schema.

    Real API structure (inside 'data'):
      - redg_no, name, father_name, mother_name
      - college_name, course, semester ("II"), exam_held
      - theorySubjects: [{code, name, ese, ia, total, grade, credit}, ...]
      - practicalSubjects: [{code, name, ese, ia, total, grade, credit}, ...]
      - sgpa: ["8.4", "7.6", "-", "-", "-", "-", "-", "-"]  (array of 8)
      - cgpa: "8"
      - fail_any: "PASS" or "FAIL"
    """
    # Parse subjects
    theory = _parse_subjects(raw.get("theorySubjects", []), is_practical=False)
    practical = _parse_subjects(raw.get("practicalSubjects", []), is_practical=True)
    all_subjects = theory + practical

    # Parse semester (roman numeral string → int)
    sem_str = raw.get("semester", "I")
    semester_int = semester_roman_to_int(str(sem_str))

    # Parse SGPA — it's an array of 8 strings, one per semester
    sgpa_array = raw.get("sgpa", [])
    sgpa = None
    if isinstance(sgpa_array, list) and semester_int <= len(sgpa_array):
        sgpa_val = sgpa_array[semester_int - 1]
        try:
            if sgpa_val and sgpa_val != "-":
                sgpa = float(sgpa_val)
        except (ValueError, TypeError):
            sgpa = None

    # Parse CGPA
    cgpa = None
    try:
        cgpa_val = raw.get("cgpa")
        if cgpa_val and str(cgpa_val) != "-":
            cgpa = float(cgpa_val)
    except (ValueError, TypeError):
        cgpa = None

    return RawResult(
        reg_no=str(raw.get("redg_no") or raw.get("rollNo") or ""),
        student_name=raw.get("name") or raw.get("studentName"),
        father_name=raw.get("father_name"),
        mother_name=raw.get("mother_name"),
        college_name=raw.get("college_name"),
        course=raw.get("course"),
        semester=semester_int,
        sgpa=sgpa,
        cgpa=cgpa,
        overall_status=raw.get("fail_any"),
        subjects=all_subjects,
    )


async def fetch_and_normalize(reg_no: str, semester: int) -> RawResult:
    """
    1. Check cache
    2. If miss: call_beu_api → normalize_result → set_cached → return
    3. If hit: return cached RawResult
    """
    cache_key = f"result:{reg_no}:{semester}"
    cached = await get_cached(cache_key)

    if cached:
        logger.debug(f"Cache hit: {cache_key}")
        return RawResult(**cached)

    logger.debug(f"Cache miss — calling BEU API: {cache_key}")
    try:
        raw_api_data = await call_beu_api(reg_no, semester)
    except httpx.HTTPError as e:
        raise BEUAPIException(f"Failed to communicate with BEU API: {e}")
    except ResultNotFoundException:
        raise

    normalized = normalize_result(raw_api_data)

    await set_cached(
        cache_key, normalized.model_dump(), ttl_seconds=settings.cache_ttl_seconds
    )
    return normalized
