# -*- coding: utf-8 -*-
"""Functions for revision management."""

__copyright__ = 'Copyright (c) 2019-2020, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import os
import time
import irods_types
import re

from rules_uu.util import *
from rules_uu.util.query import Query
from rules_uu.folder import *

__all__ = ['api_intake_list_studies',
           'api_intake_list_dm_studies',
           'api_intake_count_total_files',
           'api_intake_list_unrecognized_files',
           'api_intake_list_datasets',
           'api_intake_scan_for_datasets',
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
    groups = []
    user_name = user.name(ctx)
    user_zone = user.zone(ctx)

    iter = genquery.row_iterator(
        "USER_GROUP_NAME",
        "USER_NAME = '" + user_name + "' AND USER_ZONE = '" + user_zone + "'",
        genquery.AS_LIST, ctx
    )

    for row in iter:
        if row[0].startswith('grp-intake-'):
            groups.append(row[0][11:])

    groups.sort()
    return groups


@api.make()
def api_intake_list_dm_studies(ctx):
    """ Return list of studies current user is datamanager of """
    datamanager_groups = []
    user_name = user.name(ctx)
    user_zone = user.zone(ctx)

    iter = genquery.row_iterator(
        "USER_GROUP_NAME",
        "USER_NAME = '" + user_name + "' AND USER_ZONE = '" + user_zone + "'",
        genquery.AS_LIST, ctx
    )

    for row in iter:
        if row[0].startswith('grp-intake-'):
            study = row[0][11:]
            # Is a member of this study ... check whether member of corresponding datamanager group
            iter2 = genquery.row_iterator(
                "USER_NAME",
                "USER_TYPE = 'rodsgroup' AND USER_NAME like 'datamanager-" + study + "'",
                genquery.AS_LIST, ctx
            )
            for row2 in iter2:
                datamanager_group = row2[0]
                if user.is_member_of(ctx, datamanager_group): 
                    datamanager_groups.append(study)

    return datamanager_groups


@api.make()
def api_intake_count_total_files(ctx, coll):
    """ get the total count of all files in coll """

    log.write(ctx, coll)
    # Include coll name as equal names do occur and genquery delivers distinct results.
    iter = genquery.row_iterator(
        "COLL_NAME, DATA_NAME",
        "COLL_NAME like '" + coll + "%'",
        genquery.AS_LIST, ctx
    )

    count = 0
    for row in iter:
        log.write(ctx, row[0] + '/' + row[1])
        count += 1

    log.write(ctx, str(count))
        
    return count



@api.make()
def api_intake_list_unrecognized_files(ctx, coll):
    """
    Get list of all unrecognized files for given path including relevant metadata

    :param coll: collection to find unrecognized and unscanned files in
    """
    log.write(ctx, coll)
    # Include coll name as equal names do occur and genquery delivers distinct results.
    iter = genquery.row_iterator(
        "COLL_NAME, DATA_NAME, COLL_CREATE_TIME, DATA_OWNER_NAME",
        "COLL_NAME like '" + coll + "%' AND META_DATA_ATTR_NAME = 'unrecognized'",
        genquery.AS_LIST, ctx
    )

    files = []
    for row in iter:
        # Error is hardcoded! (like in the original) and initialize attributes already as empty strings.
        file_data = {"name": row[1],
                     "path": row[0],
                     "date": row[2],
                     "creator": row[3],
                     "error": 'Experiment type, wave or pseudocode is missing from path',
                     "experiment_type": '',
                     "pseudocode": '',
                     "wave": '',
                     "version": ''
        }
        # per data object get relevent metadata (experiment type, version, wave, pseudocode) if present
        iter2 = genquery.row_iterator(
            "META_DATA_ATTR_NAME, META_DATA_ATTR_VALUE",
            "COLL_NAME = '" + row[0] + "' AND DATA_NAME = '" + row[1] +"' AND META_DATA_ATTR_NAME in ('experiment_type', 'pseudocode', 'wave', 'version')",
            genquery.AS_LIST, ctx
        )
        for row2 in iter2:
            log.write(ctx, row2[0])
            file_data[row2[0]] = row2[1]

        files.append(file_data) 

    return files


@api.make()
def api_intake_list_datasets(ctx, coll):
    """
    Get list of datasets for given path.
    A dataset is distinguished by attribute name 'dataset_toplevel' which can either reside on a collection or a data object.
    That is why 2 seperate queries have to be performed.
    :param coll: collection from which to list all datasets
    """
    
    datasets = []
    """
    dataset = {}
    
    dataset['dataset_id'] = '123455'
    dataset['path'] = coll
    dataset['wave'] = '1'
    dataset['expType'] = '2'   ### DIT MOET experiment_type worden voor gemak en consistentie
    dataset['pseudocode'] = '3'
    dataset['version'] = '4'
    dataset['datasetStatus'] = 'scanned'
    dataset['datasetCreateName'] = '==UNKNOWN=='
    dataset['datasetCreateDate'] = 0
    dataset['datasetErrors'] = 0
    dataset['datasetWarnings'] = 0
    dataset['datasetComments'] = 0
    dataset['objects'] = 5
    dataset['objectErrors'] = 0
    dataset['objectWarnings'] = 0

    datasets.append(dataset)

    dataset = {}
    dataset['dataset_id'] = '22123455'
    dataset['path'] = coll + 'blabla'
    dataset['wave'] = '1'
    dataset['expType'] = '2'   ### DIT MOET experiment_type worden voor gemak en consistentie
    dataset['pseudocode'] = '3'
    dataset['version'] = '4'
    dataset['datasetStatus'] = 'scanned'
    dataset['datasetCreateName'] = '==UNKNOWN=='
    dataset['datasetCreateDate'] = 0
    dataset['datasetErrors'] = 100
    dataset['datasetWarnings'] = 101
    dataset['datasetComments'] = 0
    dataset['objects'] = 10
    dataset['objectErrors'] = 10
    dataset['objectWarnings'] = 11
    
    datasets.append(dataset)

    return datasets

    """

    log.write(ctx, coll)


    # 1) Query for datasets distinguished by collections
#      "COL_META_COLL_ATTR_VALUE" => NULL,
#      "COL_COLL_NAME" => NULL
#        $condition->add('COL_COLL_NAME', 'like', $referencePath . '%');
#        $condition->add('COL_META_COLL_ATTR_NAME', '=', 'dataset_toplevel');

    iter = genquery.row_iterator(
        "META_COLL_ATTR_VALUE, COLL_NAME",
        "COLL_NAME like '" + coll + "%' AND META_COLL_ATTR_NAME = 'dataset_toplevel' ", 
        genquery.AS_LIST, ctx
    )
    for row in iter:
        dataset = get_dataset_details(ctx, row[0], row[1])
        datasets.append(dataset)


    # 2) Query for datasets distinguished dataobjects
#    "COL_META_DATA_ATTR_VALUE" => NULL,
#     "COL_COLL_NAME" => NULL,
#    $condition->add('COL_COLL_NAME', 'like', $referencePath . '/%');
#    $condition->add('COL_META_DATA_ATTR_NAME', '=', 'dataset_toplevel');

    iter = genquery.row_iterator(
        "META_DATA_ATTR_VALUE, COLL_NAME",
        "COLL_NAME like '" + coll + "%' AND META_DATA_ATTR_NAME = 'dataset_toplevel' ",
        genquery.AS_LIST, ctx
    )
    for row in iter:
        dataset = get_dataset_details(ctx, row[0], row[1])
        datasets.append(dataset)

    # 3) extra query for datasets that fall out of above query due to 'like' in query
#    "COL_META_DATA_ATTR_VALUE" => NULL,
#    "COL_COLL_NAME" => NULL,
#    $condition->add('COL_COLL_NAME', '=', $referencePath);
#    $condition->add('COL_META_DATA_ATTR_NAME', '=', 'dataset_toplevel');

    iter = genquery.row_iterator(
        "META_DATA_ATTR_VALUE, COLL_NAME",
        "COLL_NAME = '" + coll + "' AND META_DATA_ATTR_NAME = 'dataset_toplevel' ",
        genquery.AS_LIST, ctx
    )
    for row in iter:
        dataset = get_dataset_details(ctx, row[0], row[1])
        datasets.append(dataset)

    return datasets


def get_dataset_details(ctx, dataset_id, path):
    """ get details of dataset based on dataset_id (dataset['dataset_id'])
    :param dataset_id    id of dataset
    :param path          path to dataset
    """
    # Inialise all attributes
    dataset = {"dataset_id": dataset_id,
               "path": path
    }

    # uuYcDatasetParseId(*id, *idComponents){
    #    *idParts = split(*id, "\t");
    #    *idComponents."wave"            = elem(*idParts, 0);
    #    *idComponents."experiment_type" = elem(*idParts, 1);
    #    *idComponents."pseudocode"      = elem(*idParts, 2);
    #    *idComponents."version"         = elem(*idParts, 3);
    #    *idComponents."directory"       = elem(*idParts, 4);

    # Parse dataset_id to get WEPV-items individually
    dataset_parts = dataset_id.split('\t')
    dataset['wave'] = dataset_parts[0]
    dataset['expType'] = dataset_parts[1]
    dataset['experiment_type'] = dataset_parts[1]
    dataset['pseudocode'] = dataset_parts[2]
    dataset['version'] = dataset_parts[3]
    directory = dataset_parts[4] # HIER WORDT NIKS MEE GEDAAN - toch ff zo laten

    dataset['datasetStatus'] = 'scanned'
    dataset['datasetCreateName'] = '==UNKNOWN=='
    dataset['datasetCreateDate'] = 0
    dataset['datasetErrors'] = 0
    dataset['datasetWarnings'] = 0
    dataset['datasetComments'] = 0
    dataset['objects'] = 0
    dataset['objectErrors'] = 0
    dataset['objectWarnings'] = 0

    tl_info = get_dataset_toplevel_objects(ctx, path, dataset_id)
    is_collection = tl_info['is_collection']
    tl_objects = tl_info['objects']

    if is_collection:
        """ dataset is based on a collection """
        tl_collection = tl_objects[0]
        iter = genquery.row_iterator(
            "COLL_NAME, COLL_OWNER_NAME, COLL_CREATE_TIME",
            "COLL_NAME = '" + tl_collection + "' ",
            genquery.AS_LIST, ctx
        )
        for row in iter:
            dataset['datasetCreateName'] = row[1]
            dataset['datasetCreateDate'] = row[2]

        iter = genquery.row_iterator(
            "COLL_NAME, META_COLL_ATTR_NAME, count(META_COLL_ATTR_VALUE)",
            "COLL_NAME = '" + tl_collection + "' ",
            genquery.AS_LIST, ctx
        )
        for row in iter:
            if row[1] == 'dataset_error':
                dataset['datasetErrors'] += int(row[2])
            if row[1] == 'dataset_warning':
                dataset['datasetWarnings'] += int(row[2])
            if row[1] == 'comment':
                dataset['datasetComments'] += int(row[2])
            if row[1] == 'to_vault_freeze':
                dataset['datasetStatus'] = 'frozen'
            if row[1] == 'to_vault_lock':
                dataset['datasetStatus'] = 'locked'

        iter = genquery.row_iterator(
            "COLL_NAME, META_COLL_ATTR_NAME, META_COLL_ATTR_VALUE",
            "COLL_NAME = '" + tl_collection + "' ",
            genquery.AS_LIST, ctx
        )
        for row in iter:
            if row[1] == 'object_count':
                dataset['objects'] += int(row[2])
            if row[1] == 'object_errors':
                dataset['objectErrors'] += int(row[2])
            if row[1] == 'object_warnings':
               dataset['objectWarnings'] += int(row[2])
    else:
        """ dataset is based on a dataobject
        Step through all data objects as found in tlObjects """
        objects = 0
        object_errors = 0
        object_warnings = 0
        for tl_object in tl_objects:

            # split tl_object
            log.write(ctx, tl_object)
            tlo = pathutil.chop(tl_object)
            log.write(ctx, tlo)
            parent = tlo[0]
            base_name = tlo[1]

            objects += 1
            if objects == 1:
                iter = genquery.row_iterator(
                    "DATA_OWNER_NAME, DATA_CREATE_TIME",
                    "COLL_NAME = '" +  parent + "' and DATA_NAME = '" + base_name + "' ",
                    genquery.AS_LIST, ctx
                )
                for row in iter:
                    dataset['datasetCreateName'] = row[0]
                    dataset['datasetCreateDate'] = row[1]

            iter = genquery.row_iterator(
                "META_DATA_ATTR_NAME, META_DATA_ATTR_VALUE",
                "COLL_NAME = '" +  parent + "' and DATA_NAME = '" + base_name + "' ",
                genquery.AS_LIST, ctx
            )
            for row in iter:
                if row[0] == 'error':
                    object_errors += 1
                if row[0] == 'warning':
                    object_warnings += 1
                if objects == 1:
                    if row[0] == 'dataset_error':
                        dataset['datasetErrors'] += int(row[1])
                    if row[0] == 'dataset_warning':
                        dataset['datasetWarnings'] += int(row[1])
                    if row[0] == 'comment':
                        dataset['datasetComments'] += int(row[1])
                if row[0] == 'to_vault_freeze':
                    dataset['datasetStatus'] = 'frozen'
                if row[0] == 'to_vault_lock':
                    dataset['datasetStatus'] = 'locked'
        ## HDR-klopt dit??
        dataset['objects'] = objects
        dataset['objectErrors'] = object_errors
        dataset['objectWarnings'] = object_warnings

    return dataset


def get_dataset_toplevel_objects(ctx, root, dataset_id):
    """ returns dict with toplevel object paths and whether is collection based dataset 
    if is a collection - only one object is returned (collection path)
    if not a collection- all objects are returned with full object path

    :param root - path to a dataset
    :dataset_id - id of the dataset
    """
    log.write(ctx, '****************** IN GET DATASET TOPLEVEL')
    log.write(ctx, root)
    log.write(ctx, dataset_id)
    iter = genquery.row_iterator(
        "COLL_NAME",
        "COLL_NAME LIKE '" + root + "%' AND META_COLL_ATTR_NAME = 'dataset_toplevel' "
        "AND META_COLL_ATTR_VALUE = '" + dataset_id + "'",
        genquery.AS_LIST, ctx
    )
    for row in iter:
        return {'is_collection': True,
                'objects': [row[0]]}

    # For dataobject situation gather all object path strings as a list
    iter = genquery.row_iterator(
        "DATA_NAME, COLL_NAME",
        "COLL_NAME = '" + root + "' AND META_DATA_ATTR_NAME = 'dataset_toplevel' "
        "AND META_DATA_ATTR_VALUE = '" + dataset_id + "'",
        genquery.AS_LIST, ctx
    )
    objects = []
    for row in iter:
        objects.append(row[1] + '/' + row[0])
    return {'is_collection': False,
            'objects': objects}

# ========================================================================================= SCANNING
@api.make()
def api_intake_scan_for_datasets(ctx, coll):
    """ The toplevel of a dataset can be determined by attribute 'dataset_toplevel' and can either be a collection or a data_object
    :param coll: collection to scan for datasets
    """

    # folder.set_status(coll, 'lock')
   
    # The dataset collection, or the first parent of a data-object dataset object.
    # Incorporated into the dataset_id.
    # *scope."dataset_directory"    = ".";

    # Extracted WEPV, as found in pathname components.
    # *scope."wave"            = ".";
    # *scope."experiment_type" = ".";
    # *scope."pseudocode"      = ".";
    # *scope."version"         = ".";
   
    # MOET DIT ECHT!!?? 
    scope = {"wave": "",
             "experiment_type": "",
             "preudocode": ""}
             # "version": "."}

    log.write(ctx, "BEFORE SCAN coll: " + coll)
    intake_scan_collection(ctx, coll, scope, False)
    log.write(ctx, "AFTER SCAN")
    log.write(ctx, "BEFORE CHECK")
    intake_check_datasets(ctx, coll)
    log.write(ctx, "AFTER CHECK")
    log.write(ctx, "TOTALLY FINISHED ***********************************************")

    return {"proc_status": "OK"}

    # folder.set_status(coll, 'unlocked')


def dataset_get_ids(ctx, coll):
    """ Find dataset ids under coll 

    :param[in]  root
    returns ids  a list of dataset ids
    """
    data_ids = []

    # Get distinct data_ids
    iter = genquery.row_iterator(
        "META_DATA_ATTR_VALUE",
        "COLL_NAME = '" + coll + "' AND META_DATA_ATTR_NAME = 'dataset_id' ",
        genquery.AS_LIST, ctx
    )
    for row in iter:
        if row[0]:
            data_ids.append(row[0])

    # Get distinct data_ids
    iter = genquery.row_iterator(
        "META_DATA_ATTR_VALUE",
        "COLL_NAME LIKE '" + coll + "%' AND META_DATA_ATTR_NAME = 'dataset_id' ",
        genquery.AS_LIST, ctx
    )
    for row in iter:
        if row[0]: # CHECK FOR DUPLICATES???
            data_ids.append(row[0])

    log.write(ctx, "DATASET_IDS ****************************************")
    log.write(ctx, data_ids)
    return data_ids


#====================== DATASET CHECKS
def intake_check_datasets(ctx, root):
    """ Run checks on all datasets under root.

    :param[in] root
    """
    dataset_ids = dataset_get_ids(ctx, root)
    for dataset_id in dataset_ids:
        intake_check_dataset(ctx, root, dataset_id)


"""
uuYcIntakeCheckDatasets(*root) {
	uuYcDatasetGetIds(*root, *ids);
	foreach (*id in *ids) {
		uuYcDatasetIsLocked(*root, *id, *isLocked, *isFrozen);
		if (*isLocked || *isFrozen) {
			writeLine("stdout", "Skipping checks for dataset id <*id> (locked)");
		} else {
			writeLine("stdout", "Checking dataset id <*id>");
			uuYcIntakeCheckDataset(*root, *id);
		}
	}
}
"""

def intake_check_dataset(ctx, root, dataset_id):
    """ Run checks on the dataset specified by the given dataset id.

    This function adds warnings and errors to objects within the dataset.

    :param[in] root
    :param[in] id
    """
    tl_info = get_dataset_toplevel_objects(ctx, root, dataset_id)
    is_collection = tl_info['is_collection']
    tl_objects = tl_info['objects']

    intake_check_generic(ctx, root, dataset_id, tl_objects, is_collection)

    id_components = dataset_parse_id(dataset_id)

    # specific check
    if id_components["experiment_type"] == "echo" or 1 == 1:
        intake_check_et_echo(ctx, root, dataset_id, tl_objects, is_collection)  # toplevels

    for tl in tl_objects:
        # Save the aggregated counts of #objects, #warnings, #errors on object level

        count = get_aggregated_object_count(ctx, dataset_id, tl)
        if is_collection:
            avu.set_on_coll(ctx, tl, "object_count", str(count))
        else:
            avu.set_on_data(ctx, tl, "object_count", str(count))

        count = get_aggregated_object_error_count(ctx, dataset_id, tl)
        if is_collection:
            avu.set_on_coll(ctx, tl, "object_errors", str(count))
        else:
            avu.set_on_data(ctx, tl, "object_errors", str(count))

        count = get_aggregated_object_warning_count(ctx, dataset_id, tl)
        if is_collection:
            avu.set_on_coll(ctx, tl, "object_warnings", str(count))
        else:
            avu.set_on_data(ctx, tl, "object_warnings", str(count))


def intake_check_generic(ctx, root, dataset_id, toplevels, is_collection): 
    """ Run checks that must be applied to all datasets regardless of WEPV values.

    :param[in] root
    :param[in] dataset_id           the dataset id to check
    :param[in] toplevels    a list of toplevel objects for this dataset id
    :param[in] isCollection
    """
    # Check validity of wav
    waves = ["20w", "30w","0m", "5m", "10m", "3y", "6y", "9y", "12y", "15y"]
    components = dataset_parse_id(dataset_id)
    if components['wave'] not in waves:
        dataset_add_error(ctx, toplevels, is_collection, "The wave '" + components['wave'] + "' is not in the list of accepted waves")


def intake_check_et_echo(ctx, root, dataset_id, toplevels, is_collection):
    """ Run checks specific to the Echo experiment type.
    :param[in] root
    :param[in] id           the dataset id to check
    :param[in] toplevels    a list of toplevel objects for this dataset id
    :param[in] is_collection
    """
    log.write(ctx, "**********************************IN CHECK ECHO")

    objects = get_rel_paths_objects(ctx, root, dataset_id)

    try:
        if is_collection:
            dataset_parent = toplevels[0]
        else:
            dataset_parent = pathutil.dirname(toplevels[0])
    except Exception as e:
        log.write(ctx, "EXCEPTION IN CHECK_ET_ECHO")
        log.write(ctx, root)
        log.write(ctx, toplevels)
        dataset_parent = root

    intake_check_file_count(ctx, dataset_parent, toplevels, is_collection, objects, 'I0000000.index.jpg', '(.*/)?I[0-9]{7}\.index\.jpe?g', 13, -1)
    intake_check_file_count(ctx, dataset_parent, toplevels, is_collection, objects, 'I0000000.raw', '(.*/)?I[0-9]{7}\.raw', 7, -1)
    intake_check_file_count(ctx, dataset_parent, toplevels, is_collection, objects, 'I0000000.dcm', '(.*/)?I[0-9]{7}\.dcm', 6, -1)
    intake_check_file_count(ctx, dataset_parent, toplevels, is_collection, objects, 'I0000000.vol', '(.*/)?I[0-9]{7}\.vol', 6, -1)


def get_rel_paths_objects(ctx, root, dataset_id):
    """Get a list of relative paths to all data objects in a dataset.
    :param[in]  root
    :param[in]  dataset_id
    returns a list of objects of relative object paths (e.g. file1.dat, some-subdir/file2.dat...)
    """
    log.write(ctx, "**********************************IN GET REL PATHS")


    tl_info = get_dataset_toplevel_objects(ctx, root, dataset_id)
    is_collection = tl_info['is_collection']
    tl_objects = tl_info['objects']

    log.write(ctx, root)
    log.write(ctx, dataset_id)
    log.write(ctx, is_collection)
    log.write(ctx, tl_objects)

    rel_path_objects = []

    # get the correct parent_collection
    try:
        if is_collection:
            parent_coll = tl_objects[0]
        else:
            parent_coll = pathutil.dirname(tl_objects[0])
    except Exception as e:
        parent_coll = '/'

    iter = genquery.row_iterator(
        "DATA_NAME, COLL_NAME",
        "COLL_NAME = '" + parent_coll + "' AND META_DATA_ATTR_NAME = 'dataset_id' AND META_DATA_ATTR_VALUE = '" + dataset_id + "' ",
        genquery.AS_LIST, ctx
    )
    for row in iter:
        # add objects residing in parent_coll directly to list
        log.write(ctx, "DIRECT " + row[0])
        rel_path_objects.append(row[0])


    iter = genquery.row_iterator(
        "DATA_NAME, COLL_NAME",
        "COLL_NAME LIKE '" + parent_coll + "%' AND META_DATA_ATTR_NAME = 'dataset_id' AND META_DATA_ATTR_VALUE = '" + dataset_id + "' ",
        genquery.AS_LIST, ctx
    )
    for row in iter:
        # Add objects including relative paths
        rel_path_objects.append(row[1][len(parent_coll):] + '/' + row[0])

    log.write(ctx, rel_path_objects)
    return rel_path_objects


def intake_check_file_count(ctx, dataset_parent, toplevels, is_collection_toplevel, objects, pattern_human, pattern_regex, min, max):
    """ Check if a certain filename pattern has enough occurrences in a dataset.

    Adds a warning if the match count is out of range.

    NOTE: Currently, patterns must match the full relative object path.
       At the time of writing, Echo is the only experiment type we run this
       check for, and it is a flat dataset without subdirectories, so it makes
       no difference there.

       For other experiment types it may be desirable to match patterns with
       basenames instead of paths. In this case the currently commented-out
       code in this function can be used.

    :param[in] datasetParent        either the dataset collection or the first parent of a data-object dataset toplevel
    :param[in] toplevels            a list of toplevel objects
    :param[in] isCollectionToplevel
    :param[in] objects              a list of dataset object paths relative to the datasetParent parameter
    :param[in] patternHuman         a human-readable pattern (e.g.: 'I0000000.raw')
    :param[in] patternRegex         a regular expression that matches filenames (e.g.: 'I[0-9]{7}\.raw')
    :param[in] min                  the minimum amount of occurrences. set to -1 to disable minimum check.
    :param[in] max                  the maximum amount of occurrences. set to -1 to disable maximum check.
    """

    count = 0
    for path in objects:
        if re.match(pattern_regex, path) is not None:
            count += 1

    if min!=-1 and count < min:
        text = "Expected at least " + str(min) + " files of type '" + pattern_human + "', found " + str(count)
        dataset_add_warning(ctx, toplevels, is_collection_toplevel, text)
    if max!=-1 and count > max:
        text = "Expected at most " + str(max) + " files of type '" + pattern_human + "', found " + str(count)
        dataset_add_warning(ctx, toplevels, is_collection_toplevel, text)

####################################################################################### Intake_SCAN_COLLECTION


def intake_scan_collection(ctx, root, scope, in_dataset): 
    """Recursively scan a directory in a Youth Cohort intake.

    :param[in] root      the directory to scan
    :param[in] scope     a scoped kvlist buffer
    :param[in] inDataset whether this collection is within a dataset collection
    """

    # Scan files under root
    iter = genquery.row_iterator(
        "DATA_NAME, COLL_NAME",
        "COLL_NAME = '" + root + "'",
        genquery.AS_LIST, ctx
    )
    for row in iter:
        # chop file extension ???? HIER WORDT NIKS MEE GEDAAN
        # uuChopFileExtension(*item>DATANAME, baseName, extension) ??? baseName en extension komen niet terug in oorspronkeljike functie

        path = row[1] + '/' + row[0]

        # Determene lock state for object (no collectoin
        locked_state = object_is_locked(ctx, path, False) 

        if not (locked_state['locked'] or locked_state['frozen']):
            remove_dataset_metadata(ctx, path, False)
            scan_mark_scanned(ctx, path, False)
            if not scan_filename_is_valid(ctx, row[0]):
                avu.set_on_data(ctx, path, "error", "File name contains disallowed characters")
        if in_dataset:
            # ApplyDatasetMetadata(sub_scope, path, false, false) @TODO  # WAT IS SCOPE/SUBSCOPE???
            apply_dataset_metadata(ctx, path, scope, False, False)
        else:
            log.write(ctx, 'DATAOBJECT')
            log.write(ctx, row[1])
            log.write(ctx, row[0])

            subscope = intake_extract_tokens_from_filename(ctx, row[1], row[0], False, scope)

            if intake_tokens_identify_dataset(subscope):
		# We found a top-level dataset data object.
                subscope["dataset_directory"] = row[1]
                apply_dataset_metadata(ctx, path, subscope, False, True)
            else:
                apply_partial_metadata(ctx, subscope, path, False)
                avu.set_on_data(ctx, path, "unrecognized", "Experiment type, wave or pseudocode missing from path")

    # Scan collections under root
    iter = genquery.row_iterator(
        "COLL_NAME",
        "COLL_PARENT_NAME = '" + root + "'",
        genquery.AS_LIST, ctx
    )
    for row in iter:
        path = row[0]

        dirname = pathutil.basename(path)
        log.write(ctx, "SCAN COLLECTIONS UNDER ROOT")
        log.write(ctx, path)
        log.write(ctx, dirname)

        if dirname is not '/':        
            # get locked /frozen status 
            locked_state = object_is_locked(ctx, path, True)

            if not (locked_state['locked'] or locked_state['frozen']):
                remove_dataset_metadata(ctx, path, True)

                if not scan_filename_is_valid(ctx, dirname):
                    avu.set_on_coll(ctx, path, "error", "Directory name contains disallowed characters")
            
                subscope = scope
                child_in_dataset = in_dataset

                if in_dataset: # initially is False
                    apply_dataset_metadata(ctx, path, scope, True, False)
                    scan_mark_scanned(ctx, path, True)
                else:
                    # uuYcIntakeExtractTokensFromFileName(*item."COLL_NAME", *dirName, true, *subScope);
                    # sub_scope wordt gevuld via extract tokens
                    log.write(ctx, 'COLLECTION')
                    log.write(ctx, path)
                    log.write(ctx, dirname)
                    subscope = intake_extract_tokens_from_filename(ctx, path, dirname, True, subscope)

                    if intake_tokens_identify_dataset(subscope):
                        child_in_dataset = True
                        # We found a top-level dataset collection.
                        subscope["dataset_directory"] = path;
                        apply_dataset_metadata(ctx, path, subscope, True, True)
                    else:
                        apply_partial_metadata(ctx, subscope, path, True)
                # Go a level deeper
                intake_scan_collection(ctx, path, subscope, child_in_dataset)


def scan_filename_is_valid(ctx, name):
    """ Check if a file or directory name contains invalid characters """
    
    log.write(ctx, name)
    log.write(ctx, re.match('^[a-zA-Z0-9_.-]+$', name) is not None)
    return (re.match('^[a-zA-Z0-9_.-]+$', name) is not None)


def object_is_locked(ctx, path, is_collection):
    """ Returns whether given object in path (collection or dataobject) is locked or frozen """

    locked_state = {"locked": False,
                    "frozen": False}

    if is_collection:
        iter = genquery.row_iterator(
            "META_COLL_ATTR_NAME",
            "COLL_NAME = '" + path + "'",
            genquery.AS_LIST, ctx
        )
        for row in iter:
            if row[0] in ['to_vault_lock', 'to_vault_freeze']:
                locked_state['locked'] = True
                if row[0] == 'to_vault_freeze':
                    locked_state['frozen'] = True
    else:
        parent_coll = pathutil.dirname(path)
        iter = genquery.row_iterator(
            "META_DATA_ATTR_NAME",
            "COLL_NAME = '" + parent_coll + "'",
            genquery.AS_LIST, ctx
        )
        for row in iter:
            if row[0] in ['to_vault_lock', 'to_vault_freeze']:
                locked_state['locked'] = True
                if row[0] == 'to_vault_freeze':
                    locked_state['frozen'] = True

    return locked_state


def intake_tokens_identify_dataset(tokens):
    """ Check whether the tokens gathered so far are sufficient for indentifyng a dataset.
       returns whether complete or not.

    :param[in]  tokens a key-value list of tokens
    """
    required = ['wave', 'experiment_type', 'pseudocode'] # version is optional

    complete = False
    for req_token in required:
        if req_token not in tokens:
            return False
    return True


# ===================================== extract
def intake_extract_tokens_from_filename(ctx, path, name, is_collection, scoped_buffer):
    """ Extract one or more tokens from a file / directory name and add dataset
    information as metadata.

    :param[in]     path
    :param[in]     name
    :param[in]     isCollection
    :param[in]     scoped_buffer 
    returns extended scope buffer
    """
    # chop of extension

    log.write(ctx, name)
    # base_name = '.'.join(name.split('.'))[:-1]
    base_name = name.rsplit('.', 1)[0]
    parts = base_name.split('_')
    for part in parts:
        subparts = part.split('-')
        for subpart in subparts:
            scoped_buffer.update(intake_extract_tokens(ctx, subpart))
    log.write(ctx, base_name)
    log.write(ctx, scoped_buffer)
    return scoped_buffer


def intake_extract_tokens(ctx, string):
    """ Extract tokens from a string and return as dict.

    :param[in] string
    """
    exp_types = ["pci",
                 "echo",
                 "facehouse",
                 "faceemo",
                 "coherence",
                 "infprogap",
                 "infsgaze",
                 "infpop",
                 # "mriinhibition",
                 # "mriemotion",
                 # "mockinhibition",
                 "chprogap",
                 "chantigap",
                 "chsgaze",
                 "pciconflict",
                 "pcivacation",
                 "peabody",
                 "discount",
                 "cyberball",
                 "trustgame",
                 "other",
                 # MRI:
                 "inhibmockbehav",
                 "inhibmribehav",
                 "emotionmribehav",
                 "emotionmriscan",
                 "anatomymriscan",
                 "restingstatemriscan",
                 "dtiamriscan",
                 "dtipmriscan",
                 "mriqcreport",
                 "mriqceval",
                 "vasmri",
                 "vasmock",
                 #
                 "looklisten",
                 "handgame",
                 "infpeabody",
                 "delaygratification",
                 "dtimriscan",
                 "inhibmriscan",
                 # 16-Apr-2019 fbyoda email request new exp type:
                 "chdualet"]

    str_lower = string.lower()
    str_upper = string.upper()

    foundKVs = {}
    if re.match('^[0-9]{1,2}[wmy]$', str_lower) is not None:
        # String contains a wave.
        # Wave validity is checked later on in the dataset checks.
        foundKVs["wave"] = str_lower
    elif re.match('^[bap][0-9]{5}$', str_lower) is not None:
        # String contains a pseudocode.
        foundKVs["pseudocode"] = str_upper[0:len(string)]
    elif re.match('^[Vv][Ee][Rr][A-Z][a-zA-Z0-9-]*$', string) is not None:
        foundKVs["version"] = string[3:len(string)]
    else:
        if string in exp_types:
            foundKVs["experiment_type"] = string

    return foundKVs


# ======================================================================

def remove_dataset_metadata(ctx, path, is_collection):
    """ Remove all intake metadata from dataset """
    intake_metadata = ["wave",
                       "experiment_type",
                       "pseudocode",
                       "version",
                       "dataset_id",
                       "dataset_toplevel",
                       "error",
                       "warning",
                       "dataset_error",
                       "dataset_warning",
                       "unrecognized",
                       "object_count",
                       "object_errors",
                       "object_warnings"]
                        
    # Add the following two lines to remove accumulated metadata during testing.
    # "comment"
    # "scanned"]

    if is_collection:
        iter = genquery.row_iterator(
            "COLL_ID, META_COLL_ATTR_NAME, META_COLL_ATTR_VALUE",
            "COLL_NAME = '" + path + "'",
            genquery.AS_LIST, ctx
        )
    else:
        iter = genquery.row_iterator(
            "DATA_ID, META_DATA_ATTR_NAME, META_DATA_ATTR_VALUE",
            "COLL_NAME = '" + pathutil.dirname(path) + "' AND DATA_NAME = '" + pathutil.basename(path) + "'",
            genquery.AS_LIST, ctx
        )

    for row in iter:
        for md_key in intake_metadata:
            if is_collection:
                log.write(ctx, md_key + ' => ' + path)
                try:
                    avu.rmw_from_coll(ctx, path, md_key, '%')
                except Exception as e:
                    continue
            else:
                try:
                    avu.rmw_from_data(ctx, path, md_key, '%')
                except Exception as e:
                    continue


def scan_mark_scanned(ctx, path, is_collection):
    """ Sets the username of the scanner and a timestamp as metadata on the scanned object.

    :param[in] path
    :param[in] is_collection
    """
    #import datetime
    # Get datetime of tomorrow.
    #tomorrow = datetime.date.today() + datetime.timedelta(1)

    # Convert tomorrow to unix timestamp.
    #return int(tomorrow.strftime("%s"))

    timestamp = int(time.time())
    user_and_timestamp = user.name(ctx) + ':' + str(timestamp) #str(datetime.date.today())

    if is_collection:
        log.write(ctx, 'SCANNED COLL: ' + user_and_timestamp)
        log.write(ctx, 'PATH: ' + path)
        avu.set_on_coll(ctx, path, 'scanned', user_and_timestamp)
    else:
        log.write(ctx, 'SCANNED DATA: ' + user_and_timestamp)
        log.write(ctx, 'PATH: ' + path)
        avu.set_on_data(ctx, path, 'scanned', user_and_timestamp)


#--======================================= apply metadata (dataset or partial)
def apply_dataset_metadata(ctx, path, scope, is_collection, is_top_level):
    """ Apply dataset metadata to an object in a dataset.

    :param[in] path         path to the object
    :param[in] scope        a scanner scope containing WEPV values
    :param[in] is_collection whether the object is a collection
    :param[in] is_top_level   if true, a dataset_toplevel field will be set on the object
    """

#    if is_collection:
#        avu.set_on_coll(ctx, )
#    else:
#        avu.set_on_data(ctx, )

    if not "version" in scope:
        version = "Raw"
    else:
        version = scope["version"]
        
    subscope = {"wave": scope["wave"],
                "experiment_type":  scope["experiment_type"],
                "pseudocode": scope["pseudocode"],
                "version": version,
                "directory": scope["dataset_directory"],

    }
    log.write(ctx, '*************************** MAKE ID *********************************')
    log.write(ctx, subscope)

    subscope["dataset_id"] = dataset_make_id(subscope)

    # add all keys to this to this level

    for key in subscope:
        if subscope[key]:
            if is_collection:
                avu.set_on_coll(ctx, path, key, subscope[key])
            else:
                avu.set_on_data(ctx, path, key, subscope[key])

    if is_top_level:
        # Add dataset_id to dataset_toplevel 
        if is_collection:
            avu.set_on_coll(ctx, path, 'dataset_toplevel', subscope["dataset_id"])
        else:
            avu.set_on_data(ctx, path, 'dataset_toplevel', subscope["dataset_id"])


def apply_partial_metadata(ctx, scope, path, is_collection):
    """ Apply any available id component metadata to the given object.
    To be called only for objects outside datasets. When inside a dataset
    (or at a dataset toplevel), use intake_apply_dataset_metadata() instead.

    :param[in] scope        a scanner scope containing some WEPV values
    :param[in] path         path to the object
    :param[in] is_collection whether the object is a collection
    """
    keys = ['wave', 'experiment_type', 'pseudocode', 'version']
    for key in keys:
        if key in scope:
            log.write(ctx, key)
            log.write(ctx, scope)
            if scope[key]:
                if is_collection:
                    avu.set_on_coll(ctx, path, key, scope[key])
                else:
                    avu.set_on_data(ctx, path, key, scope[key])


# ================= WARNING AND ERROR LOGGING
def dataset_add_warning(ctx, top_levels, is_collection_toplevel, text):
    """ Add a dataset warning to all given dataset toplevels.
    :param[in] toplevels
    :param[in] isCollectionToplevel
    :param[in] text
    """
    for tl in top_levels:
        if is_collection_toplevel:
            avu.set_on_coll(ctx, tl, "dataset_warning", text)
        else:
            avu.set_on_data(ctx, tl, "dataset_warning", text)


def dataset_add_error(ctx, top_levels, is_collection_toplevel, text):
    """ Add a dataset error to all given dataset toplevels.
    :param[in] toplevels
    :param[in] isCollectionToplevel
    :param[in] text
    """
    for tl in top_levels:
        if is_collection_toplevel:
            avu.set_on_coll(ctx, tl, "dataset_error", text)
        else:
            avu.set_on_data(ctx, tl, "dataset_error", text)


# ==================================== Aggregated counts
def get_aggregated_object_count(ctx, dataset_id, tl_collection):
    """ return total amounts of objects """
    return len(list(genquery.row_iterator(
        "DATA_ID",
        "COLL_NAME like '" + tl_collection + "%' AND META_DATA_ATTR_NAME = 'dataset_id' "
        "AND META_DATA_ATTR_VALUE = '" + dataset_id + "' ",
        genquery.AS_LIST, ctx
    )))
    return count + len(list(genquery.row_iterator(
        "DATA_ID",
        "COLL_NAME = '" + tl_collection + "' AND META_DATA_ATTR_NAME = 'dataset_id' "
        "AND META_DATA_ATTR_VALUE = '" + dataset_id + "' ",
        genquery.AS_LIST, ctx
    )))


def get_aggregated_object_error_count(ctx, dataset_id, tl_collection):
    """ return total amounts of object errors """
    return len(list(genquery.row_iterator(
        "DATA_ID",
        "COLL_NAME like '" + tl_collection + "%' AND META_DATA_ATTR_NAME = 'error' ",
        genquery.AS_LIST, ctx
    )))

    return count + len(list(genquery.row_iterator(
        "DATA_ID",
        "COLL_NAME = '" + tl_collection + "' AND META_DATA_ATTR_NAME = 'error' ",
        genquery.AS_LIST, ctx
    )))


def get_aggregated_object_warning_count(ctx, dataset_id, tl_collection):
    """ return total amounts of object warnings """
    return len(list(genquery.row_iterator(
        "DATA_ID",
        "COLL_NAME like '" + tl_collection + "%' AND META_DATA_ATTR_NAME = 'warning' ",
        genquery.AS_LIST, ctx
    )))

    return count + len(list(genquery.row_iterator(
        "DATA_ID",
        "COLL_NAME = '" + tl_collection + "' AND META_DATA_ATTR_NAME = 'warning' ",
        genquery.AS_LIST, ctx
    )))


# ================= DATASET ID UTILS
def dataset_make_id(scope):
    """ Construct a dateset based on WEPV and directory """
    return scope['wave'] + '\t' + scope['experiment_type'] + '\t' + scope['pseudocode'] + '\t' + scope['version'] + '\t' + scope['directory']


def dataset_parse_id(dataset_id):
    """ Parse a dataset into its consructive data """
    dataset_parts = dataset_id.split('\t')
    dataset = {}
    dataset['wave'] = dataset_parts[0]
    dataset['experiment_type'] = dataset_parts[1]  ## IS DIT NOG ERGENS GOED VOOR 
    dataset['expType'] = dataset_parts[1]
    dataset['pseudocode'] = dataset_parts[2]
    dataset['version'] = dataset_parts[3]
    dataset['directory'] = dataset_parts[4] # HIER WORDT NIKS MEE GEDAAN - toch ff zo laten

    return dataset

# ============================================================================ END OF SCANNING


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
def api_intake_dataset_add_comment(ctx, coll, dataset_id, comment):
    """ Add a comment to a dataset
    :param coll
    :param dataset_id: id of the dataset to add a comment to
    :param comment comment as added by user
    """
    # Authorisation still to be added. Or NOT? As irods will interfere?

    tl_info = get_dataset_toplevel_objects(ctx, coll, dataset_id)
    is_collection = tl_info['is_collection']
    tl_objects = tl_info['objects'] 

    #from datetime import datetime

    # now = datetime.now()
    timestamp = int(time.time()) # int(datetime.timestamp(datetime.now()))

    comment_data = user.name(ctx) + ':' + str(timestamp) + ':' + comment

    for tl in tl_objects:
        if is_collection:
            avu.associate_to_coll(ctx, tl, 'comment', comment_data)
        else:
            avu.associate_to_data(ctx, tl, 'comment', comment_data)

    return 'COMMENT OK'


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
