import fastapi
import fastapi.middleware.cors

from . import api_v1
from . import dependencies

from dotenv import load_dotenv

load_dotenv()

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
api_v1.catalog.register_handler(__api_v1)
api_v1.front_page.register_handler(__api_v1)
api_v1.cart.register_handler(__api_v1)
api_v1.payment.register_handler(__api_v1)

app.include_router(__api_v1)
