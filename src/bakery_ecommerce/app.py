import fastapi

from . import api_v1
from . import dependencies


app = fastapi.FastAPI(
    lifespan=dependencies.lifespan,
)

__api_v1 = fastapi.APIRouter(prefix="/api")
api_v1.product.register_handler(__api_v1)
api_v1.identity.register_handler(__api_v1)

app.include_router(__api_v1)
