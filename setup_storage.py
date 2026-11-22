"""Cria os buckets bronze, silver e gold no RustFS. Pode rodar mais de uma vez."""

from botocore.exceptions import ClientError

import config
import storage


def main():
    s3 = storage.cliente()
    existentes = {b["Name"] for b in s3.list_buckets()["Buckets"]}
    for bucket in (config.BUCKET_BRONZE, config.BUCKET_SILVER, config.BUCKET_GOLD):
        if bucket in existentes:
            print(f"  bucket {bucket} já existe")
            continue
        try:
            s3.create_bucket(Bucket=bucket)
            print(f"  bucket {bucket} criado")
        except ClientError as erro:
            if erro.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
                raise


if __name__ == "__main__":
    main()
