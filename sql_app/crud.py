from sqlalchemy.orm import Session
from datetime import datetime

from sql_app import models, schemas


def get_user(db: Session, account_id: int):
    return db.query(models.User).filter(models.User.id == account_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(username=user.username, password=user.password, first_name=user.first_name,
                          last_name=user.last_name, account_created=datetime.now(), account_updated=datetime.now()
                          , verify=0)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(user: schemas.UserBase, accountId: int, db: Session):
    updateInfo = user.dict().items()
    db_user = get_user(db, account_id=accountId)
    for key, value in updateInfo:
        setattr(db_user, key, value)
    setattr(db_user, 'account_updated', datetime.now())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
