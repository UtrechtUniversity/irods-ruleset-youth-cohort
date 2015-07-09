# \file
# \brief     Youth Cohort - Intake check functions.
# \author    Chris Smeele
# \copyright Copyright (c) 2015, Utrecht University. All rights reserved.
# \license   GPLv3, see LICENSE

# \brief Add a dataset warning to all given dataset toplevels.
#
# \param[in] toplevels
# \param[in] isCollectionToplevel
# \param[in] text
#
uuYcIntakeCheckAddDatasetWarning(*toplevels, *isCollectionToplevel, *text) {
	msiAddKeyVal(*kv, "dataset_warning", *text);

	foreach (*toplevel in *toplevels) {
		msiAssociateKeyValuePairsToObj(*kv, *toplevel, if *isCollectionToplevel then "-C" else "-d");
	}
}

# \brief Add a dataset error to all given dataset toplevels.
#
# \param[in] toplevels
# \param[in] isCollectionToplevel
# \param[in] text
#
uuYcIntakeCheckAddDatasetError(*toplevels, *isCollectionToplevel, *text) {
	msiAddKeyVal(*kv, "dataset_error", *text);

	foreach (*toplevel in *toplevels) {
		msiAssociateKeyValuePairsToObj(*kv, *toplevel, if *isCollectionToplevel then "-C" else "-d");
	}
}

# Reusable check utilities {{{

# \brief Check if a certain filename pattern has enough occurrences in a dataset.
#
# Adds a warning if the match count is out of range.
#
# \param[in] datasetParent        either the dataset collection or the first parent of a data-object dataset toplevel
# \param[in] toplevels            a list of toplevel objects
# \param[in] isCollectionToplevel
# \param[in] objects              a list of dataset object paths relative to the datasetParent parameter
# \param[in] patternHuman         a human-readable pattern (e.g.: 'I0000000.raw')
# \param[in] patternRegex         a regular expression that matches filenames (e.g.: 'I[0-9]{7}\.raw')
# \param[in] min                  the minimum amount of occurrences. set to -1 to disable minimum check.
# \param[in] max                  the maximum amount of occurrences. set to -1 to disable maximum check.
#
uuYcIntakeCheckFileCount(*datasetParent, *toplevels, *isCollectionToplevel, *objects, *patternHuman, *patternRegex, *min, *max) {
	*count = 0;
	foreach (*path in *objects) {
		*name = *path;
		#if (*path like "*/*") {
		#	uuChopPath(*path, *parent, *name);
		#} else {
		#	*name = *path;
		#}
		if (*name like regex *patternRegex) {
			*count = *count + 1;
		}
	}

	if (*min != -1 && *count < *min) {
		uuYcIntakeCheckAddDatasetWarning(*toplevels, *isCollectionToplevel, "Expected at least *min files of type '*patternHuman', found *count");
	}
	if (*max != -1 && *count > *max) {
		uuYcIntakeCheckAddDatasetWarning(*toplevels, *isCollectionToplevel, "Expected at most *max files of type '*patternHuman', found *count");
	}
}

# }}}
# Generic checks {{{

uuYcIntakeCheckWaveValidity(*root, *id, *toplevels, *isCollectionToplevel) {
	uuYcDatasetParseId(*id, *idComponents);
	uuStrToLower(*idComponents."wave", *wave);

	*waves = list(
		"20w", "30w",
		"0m", "5m", "10m",
		"3y", "6y", "9y", "12y", "15y"
	);

	uuListContains(*waves, *wave, *waveIsValid);
	if (!*waveIsValid) {
		uuYcIntakeCheckAddDatasetError(*toplevels, *isCollectionToplevel, "The wave '*wave' is not in the list of accepted waves");
	}
}

# \brief Run checks that must be applied to all datasets regardless of WEPV values.
#
# \param[in] root
# \param[in] id           the dataset id to check
# \param[in] toplevels    a list of toplevel objects for this dataset id
# \param[in] isCollection
#
uuYcIntakeCheckGeneric(*root, *id, *toplevels, *isCollection) {
	uuYcIntakeCheckWaveValidity(*root, *id, *toplevels, *isCollection);
}

# }}}
# Experiment type specific checks {{{
# Echo {{{

# \brief Run checks specific to the Echo experiment type.
#
# \param[in] root
# \param[in] id           the dataset id to check
# \param[in] toplevels    a list of toplevel objects for this dataset id
# \param[in] isCollection
#
uuYcIntakeCheckEtEcho(*root, *id, *toplevels, *isCollection) {
	if (*isCollection) {
		*datasetParent = elem(*toplevels, 0);
	} else {
		uuChopPath(elem(*toplevels, 0), *dataObjectParent, *dataObjectName);
		*datasetParent = *dataObjectParent;
	}

	uuYcDatasetGetDataObjectRelPaths(*root, *id, *objects);

	uuYcIntakeCheckFileCount(*datasetParent, *toplevels, *isCollection, *objects, ``I0000000.index.tiff``, ``I[0-9]{7}\.index\.tiff``, 20, 33);
	uuYcIntakeCheckFileCount(*datasetParent, *toplevels, *isCollection, *objects, ``I0000000.raw``,        ``I[0-9]{7}\.raw``,         20, 33);
	uuYcIntakeCheckFileCount(*datasetParent, *toplevels, *isCollection, *objects, ``I0000000.usr``,        ``I[0-9]{7}\.usr``,         20, 33);

	uuYcIntakeCheckFileCount(*datasetParent, *toplevels, *isCollection, *objects, ``I0000000.vol``,        ``I[0-9]{7}\.vol``,          5, 10);
	uuYcIntakeCheckFileCount(*datasetParent, *toplevels, *isCollection, *objects, ``I0000000.dcm``,        ``I[0-9]{7}\.dcm``,          5, 10);
}

# }}}
# }}}
