from typing import Union

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
#from aws import assume_role, create_iam_user
from helpers import aws

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/aws/account/credentials/{account_alias}")
def create_credentials_in_aws(account_alias: str):
    aws_role_name_to_create = "glueops-captain-role"
    env_file = aws.account_setup(account_alias, aws_role_name_to_create)
    
  
    return PlainTextResponse(env_file)

