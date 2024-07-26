import fastapi
from typing import Annotated
from pydantic import BaseModel

from bakery_ecommerce import internal, dependencies

api = fastapi.APIRouter()


@api.get(path="/products")
async def product_list(
    get_product_list: Annotated[
        internal.product.GetProductList, fastapi.Depends(dependencies.get_product_list)
    ],
    page: int = 0,
    page_size: int = 20,
):
    product_list = await get_product_list.execute(
        internal.product.GetProductListParams(
            page=page,
            page_size=page_size,
        )
    )

    return {"product_list": product_list}


class ProductCreateRequest(BaseModel):
    name: str


@api.post(path="/products")
async def product_create(
    request: ProductCreateRequest,
    create_product: Annotated[
        internal.product.CreateProduct, fastapi.Depends(dependencies.create_product)
    ],
):
    product = await create_product.execute(
        internal.product.CreateProductParams(name=request.name)
    )
    return {"product": product}


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
