from fastapi import Request, APIRouter
from fastapi.responses import Response

from optimade.server.routers.utils import BASE_URL_PREFIXES

router = APIRouter(redirect_slashes=True)


class CsvResponse(Response):
    media_type = "text/csv; header=present"


@router.get(
    "/versions",
    tags=["Versions"],
    response_class=CsvResponse,
)
def get_versions(request: Request) -> CsvResponse:
    """Respond with the text/csv representation for the served versions."""
    version = BASE_URL_PREFIXES["major"].replace("/v", "")
    response = f"version\n{version}"
    return CsvResponse(content=response)
