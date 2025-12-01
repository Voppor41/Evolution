import os
from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from dotenv import load_dotenv


load_dotenv()

SECRETE_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTE = 30

def create_access_token(data:dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTE)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, SECRETE_KEY, algorithm=ALGORITHM)

    return encode_jwt
