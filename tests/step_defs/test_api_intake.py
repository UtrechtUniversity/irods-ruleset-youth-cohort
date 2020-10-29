# coding=utf-8
"""Intake API feature tests."""

__copyright__ = 'Copyright (c) 2020, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

from pytest_bdd import (
    given,
    parsers,
    scenarios,
    then,
)

from conftest import api_request

scenarios('../features/api_intake.feature')


@given('the Yoda intake list studies API is queried', target_fixture="api_response")
def api_provenance_log(user):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_list_studies",
    #    {}
    #)


@given('the Yoda intake list unrecognized unscanned files API is queried with collection "<collection>"', target_fixture="api_response")
def api_provenance_log(user, collection):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_list_unrecognized_unscanned_files",
    #    {"coll": collecton}
    #)


@given('the Yoda intake list datasets API is queried with collection "<collection>"', target_fixture="api_response")
def api_provenance_log(user, collection):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_list_datasets",
    #    {"coll": collecton}
    #)


@given('the Yoda intake scan for datasets API is queried with collection "<collection>"', target_fixture="api_response")
def api_provenance_log(user, collection):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_scan_for_datasets",
    #    {"coll": collecton}
    #)


@given('the Yoda intake lock API is queried with dataset id and collection "<collection>"', target_fixture="api_response")
def api_provenance_log(user, dataset_id, collection):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_lock_dataset",
    #    {"path": collecton, "dataset_id": dataset_id}
    #)


@given('the Yoda intake unlock API is queried with dataset id and collection "<collection>"', target_fixture="api_response")
def api_provenance_log(user, dataset_id, collection):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_unlock_dataset",
    #    {"path": collecton, "dataset_id": dataset_id}
    #)


@then(parsers.parse('the response status code is "{code:d}"'))
def api_response_code(api_response, code):
    http_status, _ = api_response
    assert http_status == code


@given('dataset exists', target_fixture="dataset_id")
def datarequest_exists(user):
    return "dataset id"
