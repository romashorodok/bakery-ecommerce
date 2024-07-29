from sqlalchemy.orm import MappedColumn, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property

from bakery_ecommerce.internal.store.persistence.base import PersistanceBase, ScalarID

import bcrypt


class User(PersistanceBase, ScalarID):
    __tablename__ = "users"

    first_name: MappedColumn[str] = mapped_column()
    last_name: MappedColumn[str] = mapped_column()
    email: MappedColumn[str] = mapped_column()
    _hash: MappedColumn[str] = mapped_column("hash")

    @hybrid_property
    def hash(self) -> str:
        return self._hash

    @hash.inplace.setter
    def _hash_setter(self, value: str):
        self._hash = bcrypt.hashpw(value.encode(), bcrypt.gensalt()).decode()

    def validate_hash(self, password: str):
        return bcrypt.checkpw(password.encode(), self._hash.encode())

    def __repr__(self) -> str:
        return f"User(id={self.id}, first_name={self.first_name}, last_name={self.last_name}, email={self.email}, _hash={self._hash})"
