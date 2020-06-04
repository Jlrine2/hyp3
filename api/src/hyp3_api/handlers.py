import json
from os import environ

from flask_cors import CORS
from hyp3_api import STEP_FUNCTION_CLIENT, DYNAMODB_RESOURCE, connexion_app
from boto3.dynamodb.conditions import Key


def submit_job(body, user):
    body['user_id'] = user
    print(body)

    job = STEP_FUNCTION_CLIENT.start_execution(
        stateMachineArn=environ['STEP_FUNCTION_ARN'],
        input=json.dumps(body, sort_keys=True),
    )
    job_id = job['executionArn'].split(':')[-1]
    return {
        'jobId': job_id,
    }


def list_jobs(user):
    table = DYNAMODB_RESOURCE.Table(environ['TABLE_NAME'])
    response = table.query(IndexName='user_id', KeyConditionExpression=Key('user_id').eq(user))
    return {'jobs': response['Items']}


connexion_app.add_api('openapi-spec.yml')
CORS(connexion_app.app, origins=r'https?://([-\w]+\.)*asf\.alaska\.edu', supports_credentials=True)
