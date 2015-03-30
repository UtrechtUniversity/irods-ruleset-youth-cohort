# \file
# \brief move selected datasets from intake area to the vault area
#        to be executed by background process with write access to vault
# \author Ton Smeele
# \copyright Copyright (c) 2015, Utrecht university. All rights reserved
# \license GPLv3, see LICENSE
#
test {
	*vaultCollection = "/tsm/home/rods";
#	uuYcDatasetLock("/tsm/home/rods", "y", *result);
#	uuYcDatasetLock("/tsm/home/rods/bla", "x", *result);
#	uuYcObjectIsLocked("/tsm/home/rods/bla",true,*locked,*frozen);
#	uuYcObjectIsLocked("/tsm/home/rods/core.re",false,*locked,*frozen);
#	writeLine("stdout","lockstatus is *locked *frozen");
	uuYc2Vault(*intakeCollection, *vaultCollection, *status);
	writeLine("stdout","result of yc2Vault is *status");
}


# \brief
#
# \param[in] path  pathname of the tree-item
# \param[in] name  segment of path, name of collection or data object
# \param[in] isCol  true if the object is a collection, otherwise false
# \param[in,out] buffer
#
#uuTreeMyRule(*parent, *objectName, *isCol, *buffer) {
#	writeLine("stdout","parent      = *parent");
#	writeLine("stdout","name        = *objectName");
#	writeLine("stdout","isCol       = *isCol");
#	writeLine("stdout","buffer[path]= " ++ *buffer."path");
#	if (*isCol) {
#	   *buffer."path" = *buffer."path"++"=";
#	}
#}


uuYcDatasetCollectionMove2Vault(*topLevelCollection, *datasetId, *status) {
	writeLine("stdout","moving dataset-typeA *datasetId from *topLevelCollection to vault");
#	uuTreeWalk("forward",*topLevelCollection,"ycMoveDatasets2Vault");
	*intakeCollection = "/tsm/home/rods";
	*status = 0;
}

uuYcDatasetObjectsOnlyMove2Vault(*topLevelCollection, *datasetId, *status) {
	writeLine("stdout","moving dataset-typeB *datasetId from *topLevelCollection to vault");
	*status = 0;
}



# \brief move all locked datasets to the vault
#
# \param[in]  intakeCollection  pathname root of intake area
# \param[in]  vaultCollection   pathname root of vault area
# \param[out] status            result of operation either "ok" or "error"
#
uuYc2Vault(*intakeCollection, *vaultCollection, *status) {
	# 1. add to_vault_freeze metadata lock to the dataset
	# 2. check that dataset does not yet exist in the vault
	# 3. copy dataset to vault with its metadata
	# 4. remove dataset from intake
	# upon any error:
	# - delete partial data from vault
	# - add error to intake dataset metadata
	# - remove locks on intake dataset (to_vault_freeze, to_vault_lock)
	*status = 0; # 0 is success, nonzero is error
	*datasets_moved = 0;

	# note that we have to allow for multiple types of datasets:
	#    type A: a single toplevel collection with a tree underneath
	#    type B: one or more datafiles located within the same collection
	# processing varies slightly between them, so process each type in turn
	#
	# TYPE A:
	foreach (*row in SELECT COLL_NAME, META_COLL_ATTR_VALUE
				WHERE META_COLL_ATTR_NAME = 'dataset_toplevel') {
		msiGetValByKey(*row, "COLL_NAME", *topLevelCollection);
		msiGetValByKey(*row, "META_COLL_ATTR_VALUE", *datasetId);
		uuYcObjectIsLocked(*topLevelCollection, true, *locked, *frozen);
		if (*locked) {
			uuYcDatasetFreeze(*topLevelCollection, *datasetId, *status);
			if (*status == 0) {
				# datset frozen, now move to fault and remove from intake area
				uuYcDatasetCollectionMove2Vault(*topLevelCollection, *datasetId, *status);
				if (*status == 0) {
					*datasets_moved = *datasets_moved + 1;
				}
			}
		}
	}
	# TYPE B:
	foreach (*row in SELECT COLL_NAME, META_DATA_ATTR_VALUE
				WHERE META_DATA_ATTR_NAME = 'dataset_toplevel') {

		msiGetValByKey(*row, "COLL_NAME", *topLevelCollection);
		msiGetValByKey(*row, "META_DATA_ATTR_VALUE", *datasetId);
		# check if to_vault_lock exists on all the dataobjects of this dataset
		*allLocked = true;
		foreach (*dataRow in SELECT DATA_NAME
						WHERE COLL_NAME = '*topLevelCollection'
						  AND META_DATA_ATTR_NAME = 'dataset_toplevel'
						  AND META_DATA_ATTR_VALUE = '*datasetId'
			) {
			msiGetValByKey(*dataRow, "DATA_NAME", *dataName);
			uuYcObjectIsLocked("*topLevelCollection/*dataName", false, *locked, *frozen);
			*allLocked = *allLocked && *locked;
		}
		if (*allLocked) {
			uuYcDatasetFreeze(*topLevelCollection, *datasetId, *status);
			if (*status == 0) {
				# dataset frozen, now move to fault and remove from intake area
				uuYcDatasetObjectsOnlyMove2Vault(*topLevelCollection, *datasetId, *status);
				if (*status == 0) {
					*datasets_moved = *datasets_moved + 1;
				}
			}
		}
	}
	if (*datasets_moved > 0) {
		writeLine("stdout","moved in total *datasets_moved dataset(s) to the vault");
	}
}

input null
output ruleExecOut
