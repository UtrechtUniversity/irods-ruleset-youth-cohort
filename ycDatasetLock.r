# \file
# \brief lock/freeze and unlock/unfreeze datasets within a collection
# \author Ton Smeele
# \copyright Copyright (c) 2015, Utrecht university. All rights reserved
# \license GPLv3, see LICENSE
#

#test {
#*collection = "/tsm/home/rods";
#*datasetId = "y";
#uuYcDatasetUnlock(*collection, *datasetId, *result);
#writeLine("stdout","result = *result");
#}



uuYcDatasetLockChangeObject(*collection, *dataName, *isCollection, 
						 *lockName, *lockIt, *dateTime,*result) {
	if (*lockIt) {
		*objectType = "-d";
		*path = "*collection/*dataName";
		if (*isCollection) {
			*objectType = "-C";
			*path = *collection;
		}	
		msiString2KeyValPair("*lockName=*dateTime",*kvPair);
		*result = errorcode(msiSetKeyValuePairsToObj(*kvPair, *path, *objectType));
	} else {
		# NB: in order to remove the key we need to lookup its value(s)
		if (*isCollection) {
			# remove lock from collection
			foreach (*row in SELECT META_COLL_ATTR_VALUE 
									WHERE COLL_NAME = '*collection'
									  AND META_COLL_ATTR_NAME = '*lockName') {
				msiGetValByKey(*row, "META_COLL_ATTR_VALUE",*value);
				msiString2KeyValPair("*lockName=*value", *kvPair);
				*result = errorcode(
								msiRemoveKeyValuePairsFromObj(*kvPair, *collection, "-C")
								);
				if (*result != 0) {
					break;
				}
			}
		} else {
			# remove lock from data object
			foreach (*row in SELECT META_DATA_ATTR_VALUE
								WHERE DATA_NAME = '*dataName'
								  AND COLL_NAME = '*collection'
								  AND META_DATA_ATTR_NAME = '*lockName'
					) {
				msiGetValByKey(*row,"META_DATA_ATTR_VALUE",*value);
				msiString2KeyValPair("*lockName=*value",*kvPair);
				*result = errorcode(
								msiRemoveKeyValuePairsFromObj(
										*kvPair,
										"*collection/*dataName",
										"-d"
									)
								);
				if (*result != 0) {
					break;
				}
			}
		} # end else remove lock from dataobject
	} # end else remove lock
}

uuYcDatasetWalkVaultLock(*itemCollection, *itemName, *itemIsCollection, *buffer) {
	msiGetIcatTime(*dateTime,"unix");
	uuYcDatasetLockChangeObject(*itemCollection, *itemName, *itemIsCollection, 
						 "to_vault_lock", true, *dateTime, *result);
	*buffer."error" = str(*result);
}

uuYcDatasetWalkVaultUnlock(*itemCollection, *itemName, *itemIsCollection, *buffer) {
	msiGetIcatTime(*dateTime,"unix");
	uuYcDatasetLockChangeObject(*itemCollection, *itemName, *itemIsCollection, 
						 "to_vault_lock", false, *dateTime, *result);
	*buffer."error" = str(*result);
}

uuYcDatasetWalkFreezeLock(*itemCollection, *itemName, *itemIsCollection, *buffer) {
	msiGetIcatTime(*dateTime,"unix");
	uuYcDatasetLockChangeObject(*itemCollection, *itemName, *itemIsCollection, 
						 "to_vault_freeze", true, *dateTime, *result);
	*buffer."error" = str(*result);
}


uuYcDatasetWalkFreezeUnlock(*itemCollection, *itemName, *itemIsCollection, *buffer) {
	msiGetIcatTime(*dateTime,"unix");
	uuYcDatasetLockChangeObject(*itemCollection, *itemName, *itemIsCollection, 
						 "to_vault_freeze", false, *dateTime, *result);
	*buffer."error" = str(*result);
}



uuYcDatasetLockChange(*rootCollection, *datasetId, *lockName, *lockIt, *result){
   *result = "false";
	*lock = "Unlock";
	if (*lockIt) {
		*lock = "Lock";
	}
	*lockProcedure = "Vault";
	if (*lockName == "to_vault_freeze") {
		*lockProcedure = "Freeze";
	}
	# find the toplevel collection for this dataset
	uuYcDatasetGetTopLevel(*rootCollection, *datasetId, *collection, *isCollection);
	if (*collection != "") {
		# we found the dataset, now change the lock on each object
		if (*isCollection) {
			uuTreeWalk("forward", *collection, "uuYcDatasetWalk*lockProcedure*lock", *error);
			if (*error == "0") {
				*result = "true";
			}
		} else {
			# dataset is not a collection, let's find the objects and make the change
			msiGetIcatTime(*dateTime,"unix");
			*result = "true";
			foreach (*row in SELECT DATA_NAME 
						WHERE COLL_NAME = '*collection'
						  AND META_DATA_ATTR_NAME = 'dataset_toplevel'
						  AND META_DATA_ATTR_VALUE = '*datasetId'
				) {
				msiGetValByKey(*row,"DATA_NAME",*dataName);
				# now change it ....
				uuYcDatasetLockChangeObject(
							*collection, 
							*dataName, 
							false, 
						 	*lockName, 
							*lockIt, 
							*dateTime, 
							*error);
				if (*error != 0 ) {
					*result = "false";
					break;
				}
			}
		}

	} else {
		# result is false "dataset not found"
	}

}


# \brief uuYcDatasetLock locks (all objects of) a dataset
# 
# \param[in]  collection collection that may have datasets
# \param[in]  datasetId  identifier to depict the dataset
# \param[out] result     "true" upon success, otherwise "false"
#
uuYcDatasetLock(*collection, *datasetId, *result) {
	uuYcDatasetLockChange(*collection, *datasetId,"to_vault_lock", true, *result); 
}	

# \brief uuYcDatasetUnlock  unlocks (all objects of) a dataset
# 
# \param[in]  collection collection that may have datasets
# \param[in]  datasetId  identifier to depict the dataset
# \param[out] result     "true" upon success, otherwise "false"
#
uuYcDatasetUnlock(*collection, *datasetId, *result) {
	uuYcDatasetLockChange(*collection, *datasetId, "to_vault_lock", false, *result);
}

uuYcObjectIsLocked(*objectPath, *isCollection, *result) {
}

#input null
#output ruleExecOut
