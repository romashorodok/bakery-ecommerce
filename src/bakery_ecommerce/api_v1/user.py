import fastapi
from pydantic import BaseModel


api = fastapi.APIRouter()

route = "/users"


class UserCreateRequest(BaseModel):
    first_name: str
    last_name: str
    password: str
    email: str


@api.post(path=f"{route}")
async def user_create(request: UserCreateRequest):
    pass


def register_handler(router: fastapi.APIRouter):
    router.include_router(api)
