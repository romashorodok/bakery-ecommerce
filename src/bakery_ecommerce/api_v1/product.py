import fastapi


api = fastapi.APIRouter()


@api.get(path="/products")
def products():
    pass
    return {"product_list": []}


def register_handler(router: fastapi.APIRouter):
    router.include_router(api)
