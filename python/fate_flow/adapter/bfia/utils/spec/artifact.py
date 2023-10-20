from typing import Optional, Dict

from pydantic import BaseModel


class S3Address(BaseModel):
    url: str


class Engine(BaseModel):
    name: str = "s3"
    address: S3Address


class ArtifactAddress(BaseModel):
    name: str
    namespace: str


class Artifact(BaseModel):
    input: Dict[str, ArtifactAddress]
    output: Dict[str, ArtifactAddress]
