# \file
# \brief     Youth Cohort - Intake check functions.
# \author    Chris Smeele
# \copyright Copyright (c) 2015, Utrecht University. All rights reserved.
# \license   GPLv3, see LICENSE

#test {
#	#uuYcDatasetGetDataObjectRelPaths(*root, "1w-Echo-A12345-raw", *objects);
#	#uuYcIntakeScan(*root, *status);
#	#uuYcIntakeCheckFileCount(*toplevelObjects, "I[0-9]{7}.dcm", 1, 33);
#
#	*id ="10m-Echo-A12345-raw"
#	uuYcDatasetGetToplevelObjects(*root, *id, *toplevels, *isCollection);
#	uuYcIntakeCheckEtEcho(*id, *toplevels, *isCollection);
#}

#uuYcIntakeCheckAddDataObjectWarning(*path, *text) {
#	msiAddKeyVal(*kv, *key, *value);
#	msiAssociateKeyValuePairsToObj(*kv, *path, "-d");
#}

uuYcIntakeCheckAddDatasetWarning(*toplevels, *isCollectionToplevel, *text) {
	msiAddKeyVal(*kv, "dataset_warning", *text);

	foreach (*toplevel in *toplevels) {
		msiAssociateKeyValuePairsToObj(*kv, *toplevel, if *isCollectionToplevel then "-C" else "-d");
	}
}

uuYcIntakeCheckFileCount(*datasetParent, *toplevels, *isCollectionToplevel, *objects, *regex, *min, *max) {
	*count = 0;
	foreach (*path in *objects){
		*name = *path;
		#if (*path like "*/*") {
		#	uuChopPath(*path, *parent, *name);
		#} else {
		#	*name = *path;
		#}
		#writeLine("stdout", *name);
		if (*name like regex *regex) {
			*count = *count + 1;
		}
	}

	if (*min != -1 && *count < *min) {
		uuYcIntakeCheckAddDatasetWarning(*toplevels, *isCollectionToplevel, "Expected at least *min files that match /*regex/, found *count");
	}
	if (*max != -1 && *count > *max) {
		uuYcIntakeCheckAddDatasetWarning(*toplevels, *isCollectionToplevel, "Expected at most *max files that match /*regex/, found *count");
	}
}

uuYcIntakeCheckEtEcho(*root, *id, *toplevels, *isCollection) {
	if (*isCollection) {
		*datasetParent = elem(*toplevels, 0);
	} else {
		uuChopPath(elem(*toplevels, 0), *dataObjectParent, *dataObjectName);
		*datasetParent = *dataObjectParent;
	}

	uuYcDatasetGetDataObjectRelPaths(*root, *id, *objects);

	uuYcIntakeCheckFileCount(*datasetParent, *toplevels, *isCollection, *objects, ``I[0-9]{7}\.index\.tiff``, 20, 33);
	uuYcIntakeCheckFileCount(*datasetParent, *toplevels, *isCollection, *objects, ``I[0-9]{7}\.raw``,         20, 33);
	uuYcIntakeCheckFileCount(*datasetParent, *toplevels, *isCollection, *objects, ``I[0-9]{7}\.usr``,         20, 33);

	uuYcIntakeCheckFileCount(*datasetParent, *toplevels, *isCollection, *objects, ``I[0-9]{7}\.vol``,          5, 10);
	uuYcIntakeCheckFileCount(*datasetParent, *toplevels, *isCollection, *objects, ``I[0-9]{7}\.dcm``,          5, 10);
}

#input *root="/nluu1ot/home/chris/intake"
#output ruleExecOut
