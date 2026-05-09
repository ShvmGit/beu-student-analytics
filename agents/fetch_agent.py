from schemas.agent_schema import FetchRequest, FetchError
from schemas.result_schema import RawResult
from services.validator import validate_registration_number, validate_semester
from services.beu_api import fetch_and_normalize, BEUAPIException, ResultNotFoundException

class FetchAgent:
    async def run(self, request: FetchRequest) -> RawResult | FetchError:
        # 1. Validate reg_no format
        valid, msg = validate_registration_number(request.reg_no)
        if not valid:
            return FetchError(error_type="invalid_reg_no", message=msg)

        # 2. Validate semester
        valid, msg = validate_semester(request.semester)
        if not valid:
            return FetchError(error_type="invalid_reg_no", message=msg)

        # 3. Fetch (cache-aware)
        try:
            return await fetch_and_normalize(request.reg_no, request.semester)
        except BEUAPIException as e:
            return FetchError(error_type="api_unavailable", message=str(e))
        except ResultNotFoundException:
            return FetchError(
                error_type="result_not_found",
                message="No result found for this registration number and semester."
            )
        except Exception as e:
            return FetchError(
                error_type="parse_error",
                message=f"An unexpected error occurred: {str(e)}"
            )
