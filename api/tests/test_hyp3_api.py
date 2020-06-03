from datetime import datetime
from json import dumps
from os import environ

import pytest
from botocore.stub import Stubber
from flask_api import status
from hyp3_api import STEP_FUNCTION_CLIENT, auth, connexion_app


AUTH_COOKIE = 'asf-urs'
JOBS_URI = '/jobs'


@pytest.fixture
def client():
    with connexion_app.app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def states_stub():
    with Stubber(STEP_FUNCTION_CLIENT) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def submit_job(client, granule, states_stub=None, email='john.doe@example.com'):
    if states_stub:
        add_response(states_stub, granule, email=email)
    payload = {
        'process_type': 'RTC_GAMMA',
        'email': email,
        'parameters': {
            'granule': granule
        }
    }
    return client.post(JOBS_URI, json=payload)


def add_response(states_stub, granule, job_id='myJobId', email='john.doe@example.com'):
    payload = {
        'email': email,
        'parameters': {
            'granule': granule,
        },
        'process_type': 'RTC_GAMMA',
        'jobDefinition': 'arn:aws:batch:us-west-2:1234:job-definition/hyp3-develop-rtc-gamma:1',
        'jobQueue': 'arn:aws:batch:us-west-2:1234:job-queue/hyp3-develop',
    }
    states_stub.add_response(
        method='start_execution',
        expected_params={
            'stateMachineArn': environ['STEP_FUNCTION_ARN'],
            'input': dumps(payload, sort_keys=True),
        },
        service_response={
            'executionArn': f'{environ["STEP_FUNCTION_ARN"]}:{job_id}',
            'startDate': datetime.utcnow(),
        },
    )


def login(client):
    client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie('user'))


def test_submit_job(client, states_stub):
    login(client)
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9', states_stub)
    assert response.status_code == status.HTTP_200_OK
    assert response.get_json() == {
        'jobId': 'myJobId',
    }


def test_not_logged_in(client):
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_invalid_cookie(client):
    client.set_cookie('localhost', AUTH_COOKIE, 'garbage I say!!! GARGBAGE!!!')
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_expired_cookie(client):
    client.set_cookie('localhost', AUTH_COOKIE, auth.get_mock_jwt_cookie('user', -1))
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_good_granule_names(client, states_stub):
    login(client)
    response = submit_job(client, 'S1B_IW_GRDH_1SDV_20200518T220541_20200518T220610_021641_02915F_82D9', states_stub)
    assert response.status_code == status.HTTP_200_OK

    response = submit_job(client, 'S1A_IW_GRDH_1SSH_20150609T141945_20150609T142014_006297_008439_B83E', states_stub)
    assert response.status_code == status.HTTP_200_OK


def test_bad_granule_names(client):
    login(client)
    response = submit_job(client, 'foo')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1A_IW_GRDH_1SSH_20150609T141945_20150609T142014_006297_008439_B83')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1A_IW_GRDH_1SSH_20150609T141945_20150609T142014_006297_008439_B83Ea')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1A_S3_GRDH_1SDV_20200516T173131_20200516T173140_032593_03C66A_F005')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1A_EW_GRDM_1SDH_20200518T172837_20200518T172941_032622_03C745_422A')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1A_IW_SLC__1SSH_20200518T142852_20200518T142919_032620_03C734_E5EE')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1B_IW_OCN__2SDV_20200518T220815_20200518T220851_021642_02915F_B404')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1B_S3_RAW__0SSV_20200518T185451_20200518T185522_021640_029151_BFBF')
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = submit_job(client, 'S1B_WV_SLC__1SSV_20200519T140110_20200519T140719_021651_0291AA_2A86')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_jobs_bad_method(client):
    response = client.get(JOBS_URI)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    response = client.put(JOBS_URI)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    response = client.delete(JOBS_URI)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    response = client.head(JOBS_URI)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_no_route(client):
    response = client.get('/no/such/path')
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_cors_no_origin(client):
    response = client.post(JOBS_URI)
    assert 'Access-Control-Allow-Origin' not in response.headers
    assert 'Access-Control-Allow-Credentials' not in response.headers


def test_cors_bad_origins(client):
    response = client.post(JOBS_URI, headers={'Origin': 'https://www.google.com'})
    assert 'Access-Control-Allow-Origin' not in response.headers
    assert 'Access-Control-Allow-Credentials' not in response.headers

    response = client.post(JOBS_URI, headers={'Origin': 'https://www.alaska.edu'})
    assert 'Access-Control-Allow-Origin' not in response.headers
    assert 'Access-Control-Allow-Credentials' not in response.headers


def test_cors_good_origins(client):
    response = client.post(JOBS_URI, headers={'Origin': 'https://search.asf.alaska.edu'})
    assert response.headers['Access-Control-Allow-Origin'] == 'https://search.asf.alaska.edu'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

    response = client.post(JOBS_URI, headers={'Origin': 'https://search-test.asf.alaska.edu'})
    assert response.headers['Access-Control-Allow-Origin'] == 'https://search-test.asf.alaska.edu'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'

    response = client.post(JOBS_URI, headers={'Origin': 'http://local.asf.alaska.edu'})
    assert response.headers['Access-Control-Allow-Origin'] == 'http://local.asf.alaska.edu'
    assert response.headers['Access-Control-Allow-Credentials'] == 'true'
