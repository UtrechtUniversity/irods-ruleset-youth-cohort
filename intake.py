# -*- coding: utf-8 -*-
"""Functions for revision management."""

__copyright__ = 'Copyright (c) 2019-2020, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import os
import time
import irods_types

# from util import *
# from util.query import Query

__all__ = ['api_intake_list_studies',
           'api_intake_list_unrecognized_unscanned_files',
           'api_intake_list_datasets',
           'api_intake_scan_for_datasets',
# ???           'api_intake_get_unrecognized_count',  ???
           'api_intake_lock_dataset',
           'api_intake_unlock_dataset',
           'api_intake_dataset_get_details',
           'api_intake_dataset_add_comment',
           'api_intake_report_vault_dataset_counts_per_study',
           'api_intake_report_vault_aggregated_info',
           'api_intake_report_export_study_data']


@api.make()
def api_intake_list_studies(ctx):
    """
    Get list of all studies current user is involved in
    """
    return 'HALLO'


@api.make()
def api_intake_list_unrecognized_unscanned_files(ctx, coll):
    """
    Get list of all unrecognized or unscanned files for given path

    :param coll: collection to find unrecognized and unscanned files in
    """
    return 'HALLO'


@api.make()
def api_intake_list_datasets(ctx, coll):
    """
    Get list of datasets for given path
    :param coll: collection from which to list all datasets 
    """
    return 'HALLO'


@api.make()
def api_intake_scan_for_datasets(ctx, coll):
    """
    The toplevel of a dataset can be determined by attribute 'dataset_toplevel' and can either be a collection or a data_object
    :param coll: collection to scan for datasets
    """
    return 'HALLO'


# @api.make()
# def api_intake_get_unrecognized_count(ctx, study_id): # ???
#    """
#    Deze vervalt volgens mij
#    """


@api.make()
def api_intake_lock_dataset(ctx, path, dataset_id): 
    """
    Lock a dataset to mark as an indication it can be 'frozen' for it to progress to vault
    Lock = datamanager only
    :param coll: collection for which to lock a specific dataset id
    :param dataset_id: id of the dataset to be locked
    """
    return 'HALLO'


@api.make()
def api_intake_unlock_dataset(ctx, path, dataset_id):
    """
    Unlock a dataset to remove the indication so it can be 'frozen' for it to progress to vault
    Unlock = datamanager only
    :param coll: collection for which to lock a specific dataset id
    :param dataset_id: id of the dataset to be unlocked
    """
    return 'HALLO'


@api.make()
def api_intake_dataset_get_details(ctx, dataset_id):
    """
    Get all details for a dataset (errors/warnings, scanned by who/when, comments, file tree)
    1) Errors/warnings
    2) Comments
    3) Tree view of files within dataset.
    :param dataset_id: id of the dataset to get details for
    """
    return 'HALLO'


@api.make()
def api_intake_dataset_add_comment(ctx, dataset_id, comment):
    """
    Add a comment to the comment section of a dataset 
    :param dataset_id: id of the dataset to add a comment to
    """
    return 'HALLO'


# Reporting / export functions
@api.make()
def  api_intake_report_vault_dataset_counts_per_study(ctx, study_id):
    """
    Get the count of datasets wave/experimenttype
    In the vault a dataset is always located in a folder.
    Therefore, looking at the folders only is enough
    :param study_id: id of the study involved
    """
    return 'HALLO'


@api.make()
def  api_intake_report_vault_aggregated_info(ctx, study_id):
    """
    Collects the following information for Raw, Processed datasets. Including a totalisation of this all
    (Raw/processed is kept in VERSION)

    -Total datasets
    -Total files
    -Total file size
    -File size growth in a month
    -Datasets growth in a month
    -Pseudocodes  (distinct)
    :param study_id: id of the study involved
    """
    return 'HALLO'


@api.make()
def api_intake_report_export_study_data(ctx, study_id):
    """
    Find all datasets in the vault for $studyID.
    Include file count and total file size as well as dataset meta data version, experiment type, pseudocode and wave
    :param study_id: id of the study involved
    """
    return 'HALLO'

