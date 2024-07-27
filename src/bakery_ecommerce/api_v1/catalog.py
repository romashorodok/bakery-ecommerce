import fastapi

from bakery_ecommerce import internal, dependencies

api = fastapi.APIRouter()


@api.get(path="/")
async def catalog():
    pass
