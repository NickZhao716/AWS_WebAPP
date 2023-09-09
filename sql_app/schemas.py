from typing import List, Union, Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    verify: Optional[int]


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int


class UserToShow(User):
    account_created: str
    account_updated: str


class TokenResponse(BaseModel):
    token: str


class TokenResponse(BaseModel):
    token: str


class TokenRequest(BaseModel):
    username: str
    password: str


class DocData(BaseModel):
    doc_id: str
    user_id: str
    name: str
    data_created: str
    s3_bucket_path: str


class DocMetaData(BaseModel):
    doc_id: str
    user_id: str
    name: str
    s3_bucket_path: str
