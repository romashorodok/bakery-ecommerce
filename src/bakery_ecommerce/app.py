import fastapi
import fastapi.middleware.cors


from . import api_v1
from . import dependencies


app = fastapi.FastAPI(
    lifespan=dependencies.lifespan,
)


origins = ["*"]

app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

__api_v1 = fastapi.APIRouter(prefix="/api")
api_v1.product.register_handler(__api_v1)
api_v1.identity.register_handler(__api_v1)

app.include_router(__api_v1)
