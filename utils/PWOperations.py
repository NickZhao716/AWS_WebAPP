#!/usr/bin/python

import bcrypt


def generatePWDHash(passwd: str):
    salt = bcrypt.gensalt()
    pwdBytes = bytes(passwd, 'utf-8')
    hashed = bcrypt.hashpw(pwdBytes, salt)
    return hashed


def checkPWD(passwd: str, pwdHash: str):
    return bcrypt.checkpw(bytes(passwd, 'utf-8'), bytes(pwdHash, 'utf-8'))
