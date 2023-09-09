import os
import io
import time

import bcrypt
from fastapi import Depends, FastAPI, HTTPException, Request, Header, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

import boto3
import logging

import statsd
from boto3.dynamodb.conditions import Key
from starlette import status

from dotenv import load_dotenv

from sql_app import crud, schemas, models, doc_crud
from sql_app.database import SessionLocal, engine
from sql_app.schemas import User, DocMetaData
from utils import jsonSchema, tokenValidation, PWOperations
from datetime import timedelta, datetime
from typing import Union
import json

import jsonschema

security = HTTPBasic()
models.Base.metadata.create_all(bind=engine)
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
statsdCL = statsd.StatsClient()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/healthz")
async def root():
    statsdCL.incr("Healthz")
    return {"message": "CYSE6225"}


@app.post("/v1/account", response_model=schemas.UserToShow)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    statsdCL.incr("Create_User")
    timer1 = statsdCL.timer("create_user_timer")
    timer1.start()
    jsonData = json.loads(user.json())
    is_valid = jsonSchema.validate_json(jsonData)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid email entered")
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        statsdCL.incr("Error Count")
        raise HTTPException(status_code=400, detail="Email already registered")
    pwdHashed = PWOperations.generatePWDHash(user.password)
    user.password = pwdHashed
    result = crud.create_user(db=db, user=user)

    token = tokenValidation.signJWT(result.username)
    # publish message
    sns_client = boto3.client("sns", region_name="us-west-1")
    SNSTopic = os.getenv('SNSTopic')
    email = str(result.username)
    url0 = ",http://demo.ethflybear.com/v1/verifyUserEmail/"
    url1 = url0 + email + "/"
    url2 = url1 + str(token)
    message = email + url2
    response = sns_client.publish(
        TopicArn=SNSTopic,
        Message=message
    )

    # insert into DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name="us-west-1")
    ttl = int(time.time()) + 120
    dynamodb.Table('csye6225').put_item(
        Item={
            "email": result.username,
            "token": token,
            "ttl" : ttl
        }
    )

    result_Toshow = schemas.UserToShow(id=result.id, first_name=result.first_name,
                                       last_name=result.last_name, username=result.username,
                                       account_created=result.account_created, account_updated=result.account_updated,
                                       verify=0)
    timer1.stop()
    return result_Toshow


@app.get("/v1/account/{user_id}", response_model=schemas.UserToShow)
def read_user(user_id: int, credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    statsdCL.incr("Get_User")
    db_user = crud.get_user(db, account_id=user_id)
    if db_user.verify == 0:
        raise HTTPException(status_code=400, detail="User not verified")
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not credentials.username == db_user.username:
        raise HTTPException(status_code=404, detail="wrong user ID")
    # if not credentials.password == db_user.password:
    if not PWOperations.checkPWD(credentials.password, db_user.password):
        raise HTTPException(status_code=400, detail="incorrect password")
    # tokenValidation.verifyJWT(token, username)
    result_Toshow = schemas.UserToShow(id=db_user.id, first_name=db_user.first_name,
                                       last_name=db_user.last_name, username=db_user.username,
                                       account_created=db_user.account_created, account_updated=db_user.account_updated,
                                       verify=db_user.verify)
    return result_Toshow


@app.put("/v1/account/{user_id}", response_model=schemas.UserToShow)
def update_user(user_id: int, user: schemas.UserBase, credentials: HTTPBasicCredentials = Depends(security),
                db: Session = Depends(get_db)):
    statsdCL.incr("Update_User")
    jsonData = json.loads(user.json())
    is_valid = jsonSchema.validate_json(jsonData)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid Json request")

    # tokenValidation.verifyJWT(token, user.username)
    db_user = crud.get_user(db, account_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not credentials.username == db_user.username:
        raise HTTPException(status_code=404, detail="wrong user ID")
    if not PWOperations.checkPWD(credentials.password, db_user.password):
        raise HTTPException(status_code=400, detail="incorrect password")
    crud.update_user(user, db_user.id, db)

    user_toShow = schemas.UserToShow(id=db_user.id, first_name=db_user.first_name,
                                     last_name=db_user.last_name, username=db_user.username,
                                     account_created=db_user.account_created, account_updated=db_user.account_updated)
    return user_toShow


@app.post("/v1/signIn/", response_model=schemas.TokenResponse)
def get_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                     db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=form_data.username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.password != form_data.password:
        raise HTTPException(status_code=400, detail="in-correct password")
    result_toShow = schemas.TokenResponse(token=tokenValidation.signJWT(db_user.username))
    return result_toShow


def get_bucket_name():
    bucketName = os.getenv('bucketName')
    bucketName = bucketName[13:]
    return bucketName


@app.post("/v1/documents/")
async def create_upload_file(file: UploadFile = File(...),
                             credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    statsdCL.incr("Upload_Doc")
    timer2 = statsdCL.timer("file_upload_timer")
    timer2.start()
    bucketName = get_bucket_name()
    db_user = crud.get_user_by_username(db, username=credentials.username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not credentials.username == db_user.username:
        raise HTTPException(status_code=404, detail="wrong user ID")
    if not PWOperations.checkPWD(str(credentials.password), db_user.password):
        raise HTTPException(status_code=400, detail="incorrect password")
    userID = db_user.id
    docID = file.filename + "__" + str(userID)
    metadata = DocMetaData(doc_id=docID, user_id=userID, name=file.filename, s3_bucket_path=bucketName)
    # upload to s3
    contents = file.file.read()
    temp_file = io.BytesIO()
    temp_file.write(contents)
    temp_file.seek(0)
    s3_client = boto3.client("s3")
    s3_client.upload_fileobj(temp_file, bucketName, docID)
    temp_file.close()
    timer2.stop()
    return doc_crud.upload_doc(db, metadata)


@app.get("/v1/documents/{doc_id}")
async def get_upload_file(doc_id: str, credentials: HTTPBasicCredentials = Depends(security),
                          db: Session = Depends(get_db)):
    statsdCL.incr("Get_One_File")
    db_user = crud.get_user_by_username(db, username=credentials.username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not credentials.username == db_user.username:
        raise HTTPException(status_code=404, detail="wrong user ID")
    if not PWOperations.checkPWD(credentials.password, db_user.password):
        raise HTTPException(status_code=400, detail="incorrect password")
    userID = db_user.id
    file = doc_crud.get_doc_by_id(db, doc_id=doc_id, user_id=userID)
    return file


@app.get("/v1/documents/")
async def get_upload_files_list(credentials: HTTPBasicCredentials = Depends(security),
                                db: Session = Depends(get_db)):
    statsdCL.incr("Get_File_List")
    db_user = crud.get_user_by_username(db, username=credentials.username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not credentials.username == db_user.username:
        raise HTTPException(status_code=404, detail="wrong user ID")
    if not PWOperations.checkPWD(credentials.password, db_user.password):
        raise HTTPException(status_code=400, detail="incorrect password")
    userID = db_user.id
    files = doc_crud.get_docs(db, user_id=userID)
    return files


@app.delete("/v1/documents/{doc_id}", status_code=204)
async def delete_upload_file(doc_id: str, credentials: HTTPBasicCredentials = Depends(security),
                             db: Session = Depends(get_db)):
    statsdCL.incr("Delete_File")
    db_user = crud.get_user_by_username(db, username=credentials.username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not credentials.username == db_user.username:
        raise HTTPException(status_code=404, detail="wrong user ID")
    if not PWOperations.checkPWD(credentials.password, db_user.password):
        raise HTTPException(status_code=400, detail="incorrect password")
    userID = db_user.id
    # delete s3
    doc_crud.delete_doc(db, doc_id=doc_id, user_id=userID)
    s3_client = boto3.client("s3")
    s3_client.delete_object(Bucket=get_bucket_name(), Key=doc_id)
    return


@app.get("/v1/verifyUserEmail/{email}/{token}", status_code=204)
def verify_email(email: str, token: str, db: Session = Depends(get_db)):
    dynamodb = boto3.resource('dynamodb', region_name="us-west-1")
    response = dynamodb.Table('csye6225').get_item(
        Key={'email': email}
    )
    item = response['Item']
    if item['token'] == token and item['ttl'] > int(time.time()):
        db_user = crud.get_user_by_username(db, username=email)
        user = schemas.UserBase(first_name=db_user.first_name,
                                last_name=db_user.last_name, username=db_user.username,
                                verify=1)
        # json_raw = '{"verify": 1}'
        # user_dict = json.loads(json_raw)
        # user = schemas.UserBase(**user_dict)
        crud.update_user(db=db, user=user, accountId=db_user.id)
        return {"message": "account verified"}
    elif item['ttl'] <= int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="verify link expired",
            headers={"WWW-Authenticate": "Basic"},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="invaild token",
            headers={"WWW-Authenticate": "Basic"},
        )
