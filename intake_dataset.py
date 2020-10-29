import genquery

from rules_uu.util import *


def intake_youth_get_datasets_in_study(ctx, study_id):
    """"Get the of datasets (with relevant metadata) in a study.

    Retrieved metadata:
    - 'dataset_date_created'
    - 'wave'
    - 'version'
    - 'experiment_type'

    :param ctx:      Combined type of a callback and rei struct
    :param study_id: Unique identifier op study

    :returns: Dict with datasets and relevant metadata.
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

        if attribute_name in ['dataset_date_created', 'wave', 'version', 'experiment_type', 'pseudocode']:
            if attribute_name in ['version', 'experiment_type']:
                datasets[dataset][attribute_name] = attribute_value.lower()
            else:
                datasets[dataset][attribute_name] = attribute_value

    return datasets


def intake_youth_dataset_counts_per_study(ctx, study_id):
    """"Get the counts of datasets wave/experimenttype.

    In the vault a dataset is always located in a folder.
    Therefore, looking at the folders only is enough.

    :param ctx:      Combined type of a callback and rei struct
    :param study_id: Unique identifier op study

    :returns: Dict with counts of datasets wave/experimenttype
    """
    datasets = intake_youth_get_datasets_in_study(ctx, study_id)

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


def vault_aggregated_ingo(ctx, study_id):
    """Collects aggregated information for raw and processed datasets.

    Collects the following information for RAW and PROCESSED datasets.
    Including a totalisation of this all (raw/processed is kept in VERSION)
        - Total datasets
        - Total files
        - Total file size
        - File size growth in a month
        - Datasets growth in a month
        - Pseudocodes  (distinct)

    :param ctx:      Combined type of a callback and rei struct
    :param study_id: Unique identifier op study

    :returns: Dict with aggregated information for raw and processed datasets
    """
    datasets = intake_youth_get_datasets_in_study(ctx, study_id)

    dataset_count = {'raw': 0, 'processed': 0}
    dataset_growth = {'raw': 0, 'processed': 0}
    dataset_file_count = {'raw': 0, 'processed': 0}
    dataset_file_size = {'raw': 0, 'processed': 0}
    dataset_file_growth = {'raw': 0, 'processed': 0}
    dataset_pseudocodes = {'raw': [], 'processed': []}

    last_month = 30 * 24 * 3600

    dataset_paths = []
    for dataset in datasets:
        # Meta attribute 'dataset_date_created' defines that a folder holds a complete set.
        if datasets[dataset]['dataset_date_created']:
            dataset_paths.append(dataset)

            version = datasets[dataset]['version']
            if version in ['raw', 'processed']:
                dataset_count[version] += 1

            date_created = datasets[dataset]['dataset_date_created']
            if date_created - last_month >= 0:
                dataset_growth[version] += 1

            pseudocode = datasets[dataset]['pseudocode']
            if pseudocode not in dataset_pseudocodes[version]:
                dataset_pseudocodes[version].append(pseudocode)

    zone = user.zone(ctx)
    result = genquery.row_iterator("DATA_NAME", "COLL_NAME, DATA_SIZE, COLL_CREATE_TIME",
                                   "COLL_NAME = '/{}/home/grp-vault-{}%'".format(zone, study_id),
                                   genquery.AS_LIST, ctx)

    for row in result:
        coll_name = row[1]
        data_size = row[2]
        coll_create_time = row[3]

        # Check whether the file is part of a dataset.
        part_of_dataset = False
        for dataset in dataset_paths:
            if coll_name in dataset:
                part_of_dataset = True
                break

        # File is part of dataset.
        if part_of_dataset:
            version = datasets[dataset]['version']

            dataset_file_count[version] += 1
            dataset_file_size[version] += data_size

            if coll_create_time - last_month >= 0:
                dataset_file_growth[version] += 1

        return {
            'total': {
                'totalDatasets': dataset_count['raw'] + dataset_count['processed'],
                'totalFiles': dataset_file_count['raw'] + dataset_file_count['processed'],
                'totalFileSize': dataset_file_size['raw'] + dataset_file_size['processed'],
                'totalFileSizeMonthGrowth': dataset_file_growth['raw'] + dataset_file_growth['processed'],
                'datasetsMonthGrowth': dataset_file_growth['raw'] + dataset_file_growth['processed'],
                'distinctPseudoCodes': len(dataset_pseudocodes['raw']) + len(dataset_pseudocodes['processed']),
            },
            'raw': {
                'totalDatasets': dataset_count['raw'],
                'totalFiles': dataset_file_count['raw'],
                'totalFileSize': dataset_file_size['raw'],
                'totalFileSizeMonthGrowth': dataset_file_growth['raw'],
                'datasetsMonthGrowth': dataset_file_growth['raw'],
                'distinctPseudoCodes': len(dataset_pseudocodes['raw']),
            },
            'notRaw': {
                'totalDatasets': dataset_count['processed'],
                'totalFiles': dataset_file_count['processed'],
                'totalFileSize': dataset_file_size['processed'],
                'totalFileSizeMonthGrowth': dataset_file_growth['processed'],
                'datasetsMonthGrowth': dataset_file_growth['processed'],
                'distinctPseudoCodes': len(dataset_pseudocodes['processed']),
            },
        }
