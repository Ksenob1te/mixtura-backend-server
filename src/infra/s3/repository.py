from io import BytesIO
from pathlib import Path
from typing import Union
import aioboto3
from botocore.config import Config

from ..env_config import env


class S3BucketService:
    def __init__(self, bucket_name: str, endpoint: str, access_key: str, secret_key: str) -> None:
        self.bucket_name = bucket_name
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.config = Config(signature_version="s3v4")
        self._session = aioboto3.Session()

    async def upload_file_object(self, prefix: str, source_file_name: str, content: Union[str, bytes]) -> None:
        destination_path = str(prefix + "/" + source_file_name)
        if isinstance(content, bytes):
            buffer = BytesIO(content)
        else:
            buffer = BytesIO(content.encode("utf-8"))
        async with self._session.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=self.config,
        ) as client:
            await client.upload_fileobj(buffer, self.bucket_name, destination_path)

    async def list_objects(self, prefix: str) -> list[str]:
        async with self._session.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=self.config,
        ) as client:
            paginator = client.get_paginator("list_objects_v2")
            keys = []
            async for result in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                for obj in result.get("Contents", []):
                    keys.append(obj["Key"])
            return keys

    async def delete_file_object(self, prefix: str, source_file_name: str) -> None:
        path_to_file = str(Path(prefix, source_file_name))
        async with self._session.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=self.config,
        ) as client:
            await client.delete_object(Bucket=self.bucket_name, Key=path_to_file)

    async def get_file_object(self, path_to_file: str) -> bytes:
        async with self._session.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=self.config,
        ) as client:
            response = await client.get_object(Bucket=self.bucket_name, Key=path_to_file)
            body = response.get('Body')
            data = await body.read()
            return data


minio_manager = S3BucketService(bucket_name=env.minio.bucket_name, endpoint=env.minio.endpoint,
                                access_key=env.minio.access_key, secret_key=env.minio.secret_key)
