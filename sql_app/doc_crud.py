from datetime import datetime

import bcrypt as bcrypt
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from sql_app import models, schemas


def get_doc_by_id(db: Session, doc_id: str, user_id: int):
    file = db.query(models.Document).filter(models.Document.doc_id == doc_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            headers={"WWW-Authenticate": "Basic"},
        )
    if file.user_id != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
        )
    return file


def get_docs(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Document).filter(models.Document.user_id == user_id).offset(skip).limit(limit).all()


def upload_doc(db: Session, metaData: schemas.DocMetaData):
    db_doc = models.Document(doc_id=metaData.doc_id,
                             name=metaData.name, user_id=metaData.user_id,
                             data_created=datetime.now(), s3_bucket_path=metaData.s3_bucket_path
                             )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc


def delete_doc(db: Session, doc_id: str, user_id: int):
    file = db.query(models.Document).filter(models.Document.doc_id == doc_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            headers={"WWW-Authenticate": "Basic"},
        )
    if file.user_id != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
        )
    db.query(models.Document).filter(models.Document.doc_id == doc_id).delete()
    db.commit()
    return
