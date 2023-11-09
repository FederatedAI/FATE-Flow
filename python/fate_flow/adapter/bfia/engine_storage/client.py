import boto3


class S3Client(object):

    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password

    def list_buckets(self):
        session = boto3.Session(aws_access_key_id=self.username, aws_secret_access_key=self.password)
        s3_client = session.client(service_name="s3", endpoint_url=self.url)
        return s3_client.list_buckets()

    def create_bucket(self, bucket_name):
        session = boto3.Session(aws_access_key_id=self.username, aws_secret_access_key=self.password)
        s3_client = session.client(service_name="s3", endpoint_url=self.url)
        s3_client.create_bucket(Bucket=bucket_name)

    def put_object(self, bucket: str, key: str, body: bytes):
        session = boto3.Session(aws_access_key_id=self.username, aws_secret_access_key=self.password)
        s3_client = session.client(service_name="s3", endpoint_url=self.url)
        s3_client.put_object(Bucket=bucket, Key=key, Body=body)

    def get_object(self, bucket: str, key: str):
        session = boto3.Session(aws_access_key_id=self.username, aws_secret_access_key=self.password)
        s3_client = session.client(service_name="s3", endpoint_url=self.url)
        return s3_client.get_object(Bucket=bucket, Key=key)

    def head_object(self, bucket: str, key: str):
        session = boto3.Session(aws_access_key_id=self.username, aws_secret_access_key=self.password)
        s3_client = session.client(service_name="s3", endpoint_url=self.url)

        return s3_client.head_object(Bucket=bucket, Key=key)

    def object_exist(self, bucket: str, key: str):
        try:
            self.head_object(bucket=bucket, key=key)
            return True
        except Exception as e:
            return False

    def upload_file(self, file_path: str, bucket: str, key: str):
        session = boto3.Session(aws_access_key_id=self.username, aws_secret_access_key=self.password)
        s3_client = session.client(service_name="s3", endpoint_url=self.url)
        s3_client.upload_file(Bucket=bucket, Key=key, Filename=file_path)

    def download_file(self, file_path: str, bucket: str, key: str):
        session = boto3.Session(aws_access_key_id=self.username, aws_secret_access_key=self.password)
        s3_client = session.client(service_name="s3", endpoint_url=self.url)
        s3_client.download_file(Bucket=bucket, Key=key, Filename=file_path)

    def delete_folder(self, bucket: str, key: str):
        s3 = boto3.resource(service_name='s3', endpoint_url=self.url,use_ssl=False, aws_access_key_id=self.username,
                            aws_secret_access_key=self.password)
        bucket = s3.Bucket(bucket)
        bucket.objects.filter(Prefix=key).delete()
