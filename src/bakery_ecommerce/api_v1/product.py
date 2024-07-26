import fastapi
from typing import Annotated

from bakery_ecommerce import internal, dependencies

api = fastapi.APIRouter()


@api.get(path="/products")
def products():
    pass
    return {"product_list": []}


@api.get(path="/product")
async def product(
    name: str,
    product_by_name: Annotated[
        internal.product.GetProductByName,
        fastapi.Depends(dependencies.get_product_by_name),
    ],
    response: fastapi.Response,
):
    product = await product_by_name.execute(
        internal.product.GetProductByNameParams(name)
    )
    if not product:
        response.status_code = fastapi.status.HTTP_404_NOT_FOUND
        return {}
    return {"product": product}


def register_handler(router: fastapi.APIRouter):
    router.include_router(api)
