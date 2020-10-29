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
def api_intake_list_studies(user):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_list_studies",
    #    {}
    #)


@given('the Yoda intake list unrecognized unscanned files API is queried with collection "<collection>"', target_fixture="api_response")
def api_intake_list_unrecognized_unscanned_files(user, collection):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_list_unrecognized_unscanned_files",
    #    {"coll": collecton}
    #)


@given('the Yoda intake list datasets API is queried with collection "<collection>"', target_fixture="api_response")
def api_intake_list_datasets(user, collection):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_list_datasets",
    #    {"coll": collecton}
    #)


@given('the Yoda intake scan for datasets API is queried with collection "<collection>"', target_fixture="api_response")
def api_intake_scan_for_datasets(user, collection):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_scan_for_datasets",
    #    {"coll": collecton}
    #)


@given('the Yoda intake lock API is queried with dataset id and collection "<collection>"', target_fixture="api_response")
def api_intake_lock_dataset(user, dataset_id, collection):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_lock_dataset",
    #    {"path": collecton, "dataset_id": dataset_id}
    #)


@given('the Yoda intake unlock API is queried with dataset id and collection "<collection>"', target_fixture="api_response")
def api_intake_unlock_dataset(user, dataset_id, collection):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_unlock_dataset",
    #    {"path": collecton, "dataset_id": dataset_id}
    #)

@given('the Yoda intake report vault dataset counts per study API is queried with study id "<study_id>"', target_fixture="api_response")
def api_intake_unlock_dataset(user, study_id):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_report_vault_dataset_counts_per_study",
    #    {"study_id": study_id}
    #)

@given('the Yoda intake report vault aggregated info API is queried with study id "<study_id>"', target_fixture="api_response")
def api_intake_report_vault_aggregated_info(user, study_id):
    return 200, {}
    #return api_request(
    #    user,
    #    "intake_report_vault_aggregated_info",
    #    {"study_id": study_id}
    #)

@then(parsers.parse('the response status code is "{code:d}"'))
def api_response_code(api_response, code):
    http_status, _ = api_response
    assert http_status == code


@given('dataset exists', target_fixture="dataset_id")
def dataset_exists(user):
    return "dataset id"
