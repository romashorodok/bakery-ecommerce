from sqlalchemy.orm import Mapped, mapped_column
from . import base


# class User(base.PersistanceBase, base.ScalarID):
#     __tablename__ = "users"
#
#     first_name: Mapped[str] = mapped_column()
#     last_name: Mapped[str] = mapped_column()
#     password: Mapped[str] = mapped_column()
