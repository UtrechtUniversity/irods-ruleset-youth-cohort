import genquery
from rules_uu.util import *


def intake_dataset_set_status(ctx, collection, dataset_id, status):
    return True


def intake_dataset_lock(ctx, collection, dataset_id):
    return True


def intake_dataset_unlock(ctx, collection, dataset_id):
    return True


def intake_dataset_freeze(ctx, collection, dataset_id):
    return True


def intake_dataset_melt(ctx, collection, dataset_id):
    return True


def intake_dataset_object_get_status(ctx, path):
    """Get the status of an object in a dataset.

    :param ctx:  Combined type of a callback and rei struct
    :param path: Path of dataset object

    :returns: Tuple booleans indicating if the object is locked or frozen
    """
    locked = False
    frozen = False

    if collecton.exists(ctx, path):
        attribute_names = genquery.row_iterator("META_COLL_ATTR_NAME",
                                                "COLL_NAME = '{}'".format(path),
                                                genquery.AS_LIST, ctx)
    else:
        coll_name, data_name = pathutil.chop(path)
        attribute_names = genquery.row_iterator("META_DATA_ATTR_NAME",
                                                "COLL_NAME = '{}' AND DATA_NAME = '{}'".format(coll_name, data_name),
                                                genquery.AS_LIST, ctx)

    for row in attribute_names:
        attribute_name = row[0]
        if attribute_name in ["to_vault_lock", "to_vault_freeze"]:
            locked = True

            if attribute_name == "to_vault_freeze":
                frozen = True
                break

    return locked, frozen
