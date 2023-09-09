import time
from typing import Dict
from decouple import config
import jwt
from decouple import config
import json

from fastapi import HTTPException

secret_key = "-----BEGIN RSA PRIVATE KEY-----\nMIICXQIBAAKBgQDVdhz4aAk5fXlvHiYWS374iaByfOeblDJaICm57Phwb7sKEey3\n3jXLKTLE4jJ5WWzH/v28QtypgTkz13wsySuSr/phoupmxbUP6KowWCjUM4CxM7Hb\ndIQ8t9HFZF7uDjQGM2LfB6Z3fqvY7cDF4cOOj+JHU3JU3ex7SVHP8Z7iJwIDAQAB\nAoGADnOpsHOytC63ivtajsXbuc3vi/DC6XiWFB37VTgi9dHKsvrVsPkdYTzP0B6U\nVjzkrYGpAhbww5UZH1ZmdM3F4k/abJoJQ8Ftm6qJISiZ9rVoGcizwLy3sBV/o8he\n6sOWJDf9iR9+PtZUoTbr0hg2Oy8fWHbnsl/rryEU7m05jAkCQQDqw2hkH9tSKAc7\n+wf+0ba0isdT7WBLRUSx2lyFKCLpIyFxyQr9cKRqnm/ARmv2mMuqS4yCld5iK3IO\n5eRo2Jm7AkEA6MVmfwPoPsuSVJfdpbk9Q/Kr61VjxE9du1KrZUK6nU+tw4Tgu0KO\ncZwBaETOz2VqfDRD8kIbsOOmsiN7P2LMhQJAbIrukCR+hgzF04CsYK/btrvXj0FY\nXVTofwbD8jjtczdv9ikK8MUM79LTPmYQ8tIQkGsfyxy51k/aC3NVWPiUkwJBALxY\nhg/+dFzjUds7KvDey3EAmhWI+XouEhTx1pfP/7osb9jF2yYKu8G3zve0vXbZg+lO\nTTBoR4nBGvAHf8GRSxUCQQCwU/blrOem/k+XwxoU4ygW40PNR7C0OkILLKGtJCRD\n81hfoEtUKvvM3Vgte7y5H9sfMarmzEdqg2mMWM60IWhT\n-----END RSA PRIVATE KEY-----"
public_key = "-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDVdhz4aAk5fXlvHiYWS374iaBy\nfOeblDJaICm57Phwb7sKEey33jXLKTLE4jJ5WWzH/v28QtypgTkz13wsySuSr/ph\noupmxbUP6KowWCjUM4CxM7HbdIQ8t9HFZF7uDjQGM2LfB6Z3fqvY7cDF4cOOj+JH\nU3JU3ex7SVHP8Z7iJwIDAQAB\n-----END PUBLIC KEY-----"
payload = {
    "username": "",
    "expires": 0.0
}


def signJWT(username: str):
    payload["username"] = username
    payload["expires"] = time.time() + 600
    token = jwt.encode(payload, secret_key, algorithm='RS256')
    return token


def verifyJWT(token: str, username: str):
    try:
        decoded_payloads = jwt.decode(token, public_key, algorithms=["RS256"])
    except:
        raise HTTPException(status_code=400, detail="Invalid token")

    if not decoded_payloads["username"] == username:
        raise HTTPException(status_code=400, detail="wrong token owner")
    if decoded_payloads["expires"] < time.time():
        raise HTTPException(status_code=400, detail="token expired")
