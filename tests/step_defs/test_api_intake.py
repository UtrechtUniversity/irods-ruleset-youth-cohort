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


@given('the Yoda intake API is queried for all studies involved', target_fixture="api_response")
def api_provenance_log(user):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_list_studies",
    #    {}
    #)


@given('the Yoda intake API is queried for all unrecognized and unscanned files for collection "<collection>"', target_fixture="api_response")
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


@then(parsers.parse('the response status code is "{code:d}"'))
def api_response_code(api_response, code):
    http_status, _ = api_response
    assert http_status == code
