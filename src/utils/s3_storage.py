import boto3
from botocore.config import Config
from utils.config import get_settings

settings = get_settings()


class StorageService:

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url = settings.S3_ENDPOINT,
            aws_access_key_id = settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key = settings.S3_SECRET_ACCESS_KEY,
            region_name = settings.S3_REGION,
            config = Config(
                signature_version = "s3v4",
                s3={'addressing_style': 'path'}
            ),
        )

        self.bucket = settings.S3_BUCKET_NAME

    def upload_file( self, file, object_key: str, content_type: str):
        
        self.client.upload_fileobj(
            file,
            self.bucket,
            object_key,
            ExtraArgs={
                "ContentType": content_type
            }
        )

        return object_key

    def generate_url( self, object_key: str):
        url = self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": object_key
            },
            ExpiresIn=604800  # 7 days (Maximum allowed by AWS S3 signature v4)
        )

        return url

storage = StorageService()