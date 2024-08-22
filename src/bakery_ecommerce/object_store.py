from abc import ABC, abstractmethod
from datetime import timedelta
import json
from typing import override

from minio import Minio


class ObjectStore(ABC):
    @abstractmethod
    def connect(self): ...

    @abstractmethod
    def get_presigned_put_url(self, bucket: str, file: str) -> str: ...

    @abstractmethod
    def create_bucket_if_not_exist(self, bucket: str): ...


def readonly_policy(bucket: str) -> str:
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket}/*",
                },
            ],
        }
    )


class MinioStore(ObjectStore):
    def __init__(
        self,
        host: str = "localhost:9001",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        tls: bool = False,
    ) -> None:
        self.__host = host
        self.__access_key = access_key
        self.__secret_key = secret_key
        self.__tls = tls

    @override
    def connect(self):
        self.__conn = Minio(
            self.__host, self.__access_key, self.__secret_key, secure=self.__tls
        )

    @override
    def create_bucket_if_not_exist(self, bucket: str):
        found = self.__conn.bucket_exists(bucket)
        if not found:
            self.__conn.make_bucket(bucket)

    @override
    def get_presigned_put_url(self, bucket: str, file: str) -> str:
        self.create_bucket_if_not_exist(bucket)
        self.__conn.set_bucket_policy(bucket, readonly_policy(bucket))
        # NOTE: Minio provide url with X-Amz-Credential
        return self.__conn.presigned_put_object(
            bucket, file, expires=timedelta(minutes=5)
        )
