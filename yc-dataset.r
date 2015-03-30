# \file
# \brief     Youth Cohort - Dataset related functions.
# \author    Chris Smeele
# \copyright Copyright (c) 2015, Utrecht University. All rights reserved.
# \license   GPLv3, see LICENSE

# \brief Generate a dataset identifier based on WEPV values.
#
# \param[in]  idComponents a kvList containing WEPV values
# \param[out] id a dataset id string
#
uuYcDatasetMakeId(*idComponents, *id){
	*id =
		          *idComponents."wave"
		++ "-" ++ *idComponents."experiment_type"
		++ "-" ++ *idComponents."pseudocode"
		++ "-" ++ *idComponents."version"
}

# \brief Parse a dataset identifier and resturn WEPV values.
#
# \param[in]  id a dataset id string
# \param[out] idComponents a kvLIst containing WEPV values
#
uuYcDatasetParseId(*id, *idComponents){
	*idParts = split(*id, "-");
	*idComponents."wave"            = elem(*idParts, 0);
	*idComponents."experiment_type" = elem(*idParts, 1);
	*idComponents."pseudocode"      = elem(*idParts, 2);
	*idComponents."version"         = elem(*idParts, 3);
}

# \brief Find dataset ids under *root.
#
# \param[in]  root
# \param[out] ids  a list of dataset ids
#
uuYcDatasetGetIds(*root, *ids) {
	*idsString = "";
	foreach (*item in SELECT META_DATA_ATTR_VALUE WHERE COLL_NAME LIKE "*root" AND META_DATA_ATTR_NAME = 'dataset_id') {
		# Datasets directly under *root need to be checked for separately due to limitations on the general query system.
		if (strlen(*idsString) > 0) {
			*idsString = *idsString ++ ":";
		}
		*idsString = *idsString ++ *item."META_DATA_ATTR_VALUE";
	}
	foreach (*item in SELECT META_DATA_ATTR_VALUE WHERE COLL_NAME LIKE "*root/%" AND META_DATA_ATTR_NAME = 'dataset_id') {
		if (strlen(*idsString) > 0) {
			*idsString = *idsString ++ ":";
		}
		*idsString = *idsString ++ *item."META_DATA_ATTR_VALUE";
	}
	*ids = split(*idsString, ":");
}

# \brief Get a list of toplevel objects that belong to the given dataset id.
#
# \param[in]  root
# \param[in]  id
# \param[out] objects      a list of toplevel object paths
# \param[out] isCollection whether this dataset consists of a single toplevel collection
#
uuYcDatasetGetToplevelObjects(*root, *id, *objects, *isCollection) {
	*isCollection = false;

	*objectsString = "";
	foreach (*item in SELECT COLL_NAME WHERE COLL_NAME LIKE "*root/%" AND META_COLL_ATTR_NAME = 'dataset_toplevel' AND META_COLL_ATTR_VALUE = "*id") {
		*isCollection = true;
		*objectsString = *item."COLL_NAME";
	}
	if (!*isCollection) {
		foreach (*item in SELECT DATA_NAME, COLL_NAME WHERE COLL_NAME LIKE "*root" AND META_DATA_ATTR_NAME = 'dataset_toplevel' AND META_DATA_ATTR_VALUE = "*id") {
			# Datasets directly under *root need to be checked for separately due to limitations on the general query system.
			if (strlen(*objectsString) > 0) {
				*objectsString = *objectsString ++ ":";
			}
			*objectsString = *objectsString ++ *item."COLL_NAME" ++ "/" ++ *item."DATA_NAME";
		}
		foreach (*item in SELECT DATA_NAME, COLL_NAME WHERE COLL_NAME LIKE "*root/%" AND META_DATA_ATTR_NAME = 'dataset_toplevel' AND META_DATA_ATTR_VALUE = "*id") {
			if (strlen(*objectsString) > 0) {
				*objectsString = *objectsString ++ ":";
			}
			*objectsString = *objectsString ++ *item."COLL_NAME" ++ "/" ++ *item."DATA_NAME";
		}
	}
	*objects = split(*objectsString, ":");
	#writeLine("stdout", "Got dataset toplevel objects for <*id>: *objectsString");
}

uuYcDatasetIsLocked(*root, *id, *isLocked, *isFrozen) {
	uuYcDatasetGetToplevelObjects(*root, *id, *toplevelObjects, *isCollection);

	*isLocked = false;
	*isFrozen = false;
	foreach (*item in *toplevelObjects) {
		uuYcObjectIsLocked(*item, *isCollection, *isLocked, *isFrozen);
		if (*isLocked || *isFrozen) {
			break;
		}
	}
}
