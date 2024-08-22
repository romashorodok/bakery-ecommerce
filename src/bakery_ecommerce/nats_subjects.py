import json
from dataclasses import dataclass
from typing import Self


@dataclass
class ProductImageTranscodingRequired:
    image_id: str

    def to_bytes(self) -> bytes:
        return json.dumps({"image_id": self.image_id}).encode()

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        data_dict = json.loads(data)
        return cls(**data_dict)
