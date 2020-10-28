import genquery

from rules_uu.util import *


def intake_youth_dataset_counts_per_study(ctx, study_id):
    """"Get the counts of datasets wave/experimenttype.

    In the vault a dataset is always located in a folder.
    Therefore, looking at the folders only is enough.

    :param ctx:      Combined type of a callback and rei struct
    :param study_id: Unique identifier op study

    :returns: Dict with counts of datasets wave/experimenttype
    """
    zone = user.zone(ctx)

    result = genquery.row_iterator("COLL_NAME, COLL_PARENT_NAME, META_COLL_ATTR_NAME, META_COLL_ATTR_VALUE",
                                   "COLL_NAME = '/{}/home/grp-vault-{}%' AND META_COLL_ATTR_NAME IN ('dataset_id', 'dataset_date_created', 'wave', 'version', 'experiment_type', 'pseudocode')'".format(zone, study_id),
                                   genquery.AS_LIST, ctx)

    datasets = {}
    # Construct all datasets.
    for row in result:
        dataset = row[0]
        attribute_name = row[2]
        attribute_value = row[3]

        if attribute_name in ['dataset_date_created', 'wave', 'version', 'experiment_type']:
            if attribute_name in ['version', 'experiment_type']:
                datasets[dataset][attribute_name] = attribute_value.lower()
            else:
                datasets[dataset][attribute_name] = attribute_value

    dataset_type_counts = {}
    # Loop through datasets and count wave and experimenttype.
    for dataset in datasets:
        # Meta attribute 'dataset_date_created' defines that a folder holds a complete set.
        if datasets[dataset]['dataset_date_created']:
            type = datasets[dataset]['experiment_type']
            wave = datasets[dataset]['wave']
            version = datasets[dataset]['version']

            if dataset_type_counts[type][wave][version]:
                dataset_type_counts[type][wave][version] += 1
            else:
                dataset_type_counts[type][wave][version] = 1

    return dataset_type_counts
