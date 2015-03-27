# \file
# \brief     Youth Cohort - Intake dataset scanner.
# \author    Chris Smeele
# \copyright Copyright (c) 2015, Utrecht University. All rights reserved.
# \license   GPLv3, see LICENSE.txt.

#test {
#	#*kvList."." = "";
#	#uuYcExtractTokensFromFileName(*name, *name, true, *kvList);
#	uuYcIntakeScan(*root);
#	uuYcIntakeCommentAdd(*root, "1w-Echo-A12345-raw", "Hello, world!");
#	#uuYcIntakeCommentAdd(*root, "10m-Echo-A12345-raw", "Hello, world!");
#}

# TODO: Move uu generic rules to irods-ruleset-uu.

# \brief Chop part of a string based on a split character.
#
# if leftToRight is true, *head will contain *string up to the first *splitChar,
# and *tail will contain the rest of the string.
# Otherwise, *tail will contain the part of the string from the last *splitChar.
# and *head will contain the rest of the string.
#
# *string is not modified.
#
# \param[in]  string
# \param[out] head
# \param[out] tail
# \param[in]  splitChar   the character on which to split the string
# \param[in]  leftToRight true if we should chop from the left side
#
uuChop(*string, *head, *tail, *splitChar, *leftToRight) {
	if (*string like "**splitChar*") {
		if (*leftToRight) {
			*tail =  triml(*string, *splitChar);
			*head = substr(*string, 0, strlen(*string) - strlen(*tail) - 1);
		} else {
			*head =  trimr(*string, *splitChar);
			*tail = substr(*string, strlen(*head) + 1, strlen(*string));
		}
	} else {
		# No *splitChar in *string.
		*head = if *leftToRight then ""      else *string;
		*tail = if *leftToRight then *string else "";
	}
}

# \brief Split a file name into a base name and a file extension.
#
# \param[in]  fileName
# \param[out] baseName
# \param[out] extension
#
uuChopFileExtension(*fileName, *baseName, *extension) {
	uuChop(*fileName, *baseName, *extension, ".", false);
}

# \brief Split a path into a base name and a path.
#
# \param[in]  fileName
# \param[out] parent
# \param[out] baseName
#
uuChopPath(*path, *parent, *baseName) {
	if (*path like regex "^/[^/]*$") {
		# *path is "/" or a top level directory.
		*baseName = if strlen(*path) > 1 then substr(*path, 1, strlen(*path)) else "/";
		*parent   = "/";
	} else {
		uuChop(*path, *parent, *baseName, "/", false);
	}
}

# \brief Clears a kv-list's contents.
#
# Note: This needs to be a separate function in order to prevent scope issues.
#
# \param kvList
#
uuKvClear(*kvList) {
	#*empty."." = ".";
	#*kvList = *empty;
	*kvList."." = ".";
	foreach (*key in *kvList) {
		*kvList.*key = ".";
	}
}

# \brief Clone a key-value list.
#

# The destination list is cleared before copying.
#
# \param[in]  source
# \param[out] dest
#
uuKvClone(*source, *dest) {
	uuKvClear(*dest);
	foreach (*key in *source) {
		*dest.*key = *source.*key;
	}
}

# \brief Merge two key-value lists.
#
# list1 is copied to result, and any key in list2 that was not present in list1
# is added to the result.
#
# \param[in]  list1
# \param[in]  list2
# \param[out] result
#
uuKvMerge(*list1, *list2, *result) {
	uuKvClear(*result);
	uuKvClone(*list1, *result);

	foreach (*key in *list2) {
		*bool = false;
		uuKvExists(*result, *key, *bool)
		if (!*bool) {
			*result.*key = *list2.*key;
		}
	}
}

# \brief Check if a key exists in a key-value list.
#
# \param[in]  kvList
# \param[in]  key
# \param[out] bool
#
uuKvExists(*kvList, *key, *bool) {
	#if (errorcode(*kvList.*key) == 0) {
		*bool = (*kvList.*key != '.');
	#} else {
	#	*bool = false;
	#}
}
#uuKvExists(*kvList, *key) =
#	(errorcode(*kvList.*key) == 0);


# \brief Sets metadata on an object.
#
# \param[in] path
# \param[in] key
# \param[in] value
# \param[in] type  either "-d" for data objects or "-C" for collections
uuSetMetaData(*path, *key, *value, *type) {
	msiAddKeyVal(*kv, *key, *value);
	#errorcode(msiAddKeyVal(*kv, *key, *value));
	#*kv.*key = *value;
	msiAssociateKeyValuePairsToObj(*kv, *path, *type);
}


# \brief Removes metadata from an object.
#
# \param[in] path
# \param[in] key
# \param[in] value
# \param[in] type  either "-d" for data objects or "-C" for collections
uuRemoveMetaData(*path, *key, *value, *type) {
	msiAddKeyVal(*kv, *key, *value);
	#errorcode(msiAddKeyVal(*kv, *key, *value));
	#*kv.*key = *value;
	msiRemoveKeyValuePairsFromObj(*kv, *path, *type);
}

# \brief Generate a dataset identifier based on WEPV values.
#
# \param[in]  idComponents a kvList containing WEPV values
# \param[out] id a dataset id string
#
uuYcIntakeDatasetMakeId(*idComponents, *id){
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
uuYcIntakeDatasetParseId(*id, *idComponents){
	*idParts = split(*id, "-");
	*idComponents."wave"            = elem(*idParts, 0);
	*idComponents."experiment_type" = elem(*idParts, 1);
	*idComponents."pseudocode"      = elem(*idParts, 2);
	*idComponents."version"         = elem(*idParts, 3);
}

# \brief Apply dataset metadata to an object in a dataset.
#
# \param[in] scope        a scanner scope containing WEPV values
# \param[in] path         path to the object
# \param[in] isCollection whether the object is a collection
# \param[in] isToplevel   if true, a dataset_toplevel field will be set on the object
#
uuYcIntakeScanApplyDatasetMetaData(*scope, *path, *isCollection, *isToplevel) {

	*type = if *isCollection then "-C" else "-d";

	uuSetMetaData(*path, "wave",            *scope."meta_wave",            *type);
	uuSetMetaData(*path, "experiment_type", *scope."meta_experiment_type", *type);
	uuSetMetaData(*path, "pseudocode",      *scope."meta_pseudocode",      *type);
	uuSetMetaData(*path, "version",         *scope."meta_version",         *type);

	*idComponents."wave"            = *scope."meta_wave";
	*idComponents."experiment_type" = *scope."meta_experiment_type";
	*idComponents."pseudocode"      = *scope."meta_pseudocode";
	*idComponents."version"         = *scope."meta_version";

	uuYcIntakeDatasetMakeId(*idComponents, *datasetId);

	uuSetMetaData(
		*path,
		"dataset_id",
		*datasetId,
		*type
	);

	if (*isToplevel) {
		uuSetMetaData(*path, "dataset_toplevel", *datasetId, *type);
	}
}

# \brief Remove some dataset metadata from an object.
#
# See the function definition for a list of removed metadata fields.
#
# \param[in] path         path to the object
# \param[in] isCollection whether the object is a collection
#
uuYcRemoveDatasetMetaData(*path, *isCollection) {
	if (*isCollection) {
		msiMakeGenQuery("COLL_ID, META_COLL_ATTR_NAME, META_COLL_ATTR_VALUE", "COLL_NAME = '*path'", *genQIn);
	} else {
		uuChopPath(*path, *parent, *baseName);
		msiMakeGenQuery(
			"DATA_ID, META_DATA_ATTR_NAME, META_DATA_ATTR_VALUE",
			"DATA_NAME = '*baseName' AND COLL_NAME = '*parent'",
			*genQIn
		);
	}

	msiExecGenQuery(*genQIn, *genQOut);

	foreach (*row in *genQOut) {
		*type      = if *isCollection then "-C" else "-d";
		*attrName  = if *isCollection then *row."META_COLL_ATTR_NAME"  else *row."META_DATA_ATTR_NAME";
		*attrValue = if *isCollection then *row."META_COLL_ATTR_VALUE" else *row."META_DATA_ATTR_VALUE";

		if (
			   *attrName == "wave"
			|| *attrName == "experiment_type"
			|| *attrName == "pseudocode"
			|| *attrName == "version"
			|| *attrName == "dataset_id"
			|| *attrName == "dataset_toplevel"
			|| *attrName == "error"
			|| *attrName == "warning"
			#|| *attrName == "comment"
			#|| *attrName == "scanned"
		) {
			uuRemoveMetaData(*path, *attrName, *attrValue, *type);
		}
	}
}

# \brief Convert tokens to metadata.
#
# This allows for metadata that is spread over different path components, like dates.
#
# \param[in,out] kvList
#
uuYcTokensToMetaData(*kvList) {
	*kvList."meta_wave"            = *kvList."wave";
	*kvList."meta_experiment_type" = *kvList."experiment_type";
	*kvList."meta_pseudocode"      = *kvList."pseudocode";

	uuKvExists(*kvList, "version", *bool);
	if (*bool) {
		*kvList."meta_version" = *kvList."version";
	} else {
		*kvList."meta_version" = "raw";
	}
}

# \brief Check whether the tokens gathered so far are sufficient for indentifyng a dataset.
#
# \param[in]  tokens a key-value list of tokens
# \param[out] complete
#
uuYcTokensIdentifyDataset(*tokens, *complete) {
	*toCheck = list(
		"wave",
		"experiment_type",
		"pseudocode"
		# "version" is optional.
	);

	*complete = true;
	foreach (*check in *toCheck) {
		*bool = false;
		uuKvExists(*tokens, *check, *bool);
		if (!*bool) {
			*complete = false;
			break;
		}
	}
}
#uuYcTokensIdentifyDataset(*tokens) =
#	   uuKvExists(*tokens, "wave")
#	&& uuKvExists(*tokens, "experiment_type")
#	&& uuKvExists(*tokens, "pseudocode");


# \brief Extract tokens from a string.
#
# \param[in] string
# \param[in] kvList a list of tokens and metadata already detected
#
uuYcExtractTokens(*string, *kvList) {

	*foundKvs."." = ".";

	if (*string like regex ``^-?[0-9]{1,2}[wmj]$``) {
		# TODO: Optional: List-of-value-ify.

		# String contains a wave.
		*foundKvs."wave" = *string;

	# NOTE: Experiment dates currently cannot be extracted from paths.
	#
	#} else if (*string like regex ``^(Y[0-9]{4}M[0-9]{2}|D[0-9]{2}|[0-9]{8}(\.[0-9]{4}([0-9]{2})?)?)$``) {
	#
	#	# String contains (part of) a date, and possibly a time.
	#	if (*string like regex ``^Y[0-9]{4}M[0-9]{2}$``) {
	#		# Y....M../D.. format, year + month part.
	#		*foundKvs."year"  = substr(*string, 1, 5);
	#		*foundKvs."month" = substr(*string, 6, 8);
	#	} else if (*string like regex ``D[0-9]{2}``) {
	#		# Y....M../D.. format, day part.
	#		*foundKvs."day" = substr(*string, 1, 3);
	#	} else {
	#		# YYYYMMDD format.
	#		# Extract year, month and day first.
	#		*foundKvs."year"  = substr(*string, 0, 4);
	#		*foundKvs."month" = substr(*string, 4, 6);
	#		*foundKvs."day"   = substr(*string, 6, 8);

	#		# Check if a time was given.
	#		if (*string like regex ``.*\..*``) {
	#			*foundKvs."hour"   = substr(*string, 9,  11);
	#			*foundKvs."minute" = substr(*string, 11, 13);
	#			if (*string like regex ``.*\.[0-9]{6}$``) {
	#				*foundKvs."second" = substr(*string, 13, 15);
	#			} else {
	#				*foundKvs."second" = "00";
	#			}
	#		}
	#	}
	#	#if (errorcode(msiGetValByKey(*foundKvs, "hour", *value)) == 0) {
	#	#	# A time can only be given in combination with a YYYYMMDD date,
	#	#	# so if we don't have a time here, we can set it to 00:00:00.
	#	#	*foundKvs."hour"   = "00";
	#	#	*foundKvs."minute" = "00";
	#	#	*foundKvs."second" = "00";
	#	#}

	} else if (*string like regex ``^[AB][0-9]{5}$``) {
		# String contains a pseudocode.
		*foundKvs."pseudocode" = substr(*string, 0, 6);
	} else if (*string like regex ``^V_[a-zA-Z0-9_]+$``) {
		*foundKvs."version" = substr(*string, 2, strlen(*string));
	} else {
		*experimentTypes = list(
			'PCI',
			'Echo',
			'ET',
			'EEG'
		);
		*etDetected = false;

		foreach (*type in *experimentTypes) {
			if (*string == *type) {
				*foundKvs."experiment_type" = *type;
				*etDetected = true;
				break;
			}
		}

		if (!*etDetected) {
			#writeLine("stdout", "  - no pattern recognized");
		}
	}

	#foreach (*key in *foundKvs) {
	#	if (*kvList.*key != ".") {
	#		writeLine("stdout", "  - FOUND: *key: <" ++ *foundKvs.*key ++ ">");
	#	}
	#}

	*result."." = ".";
	uuKvMerge(*kvList, *foundKvs, *result);
	*kvList = *result;

	#foreach (*key in *kvList) {
	#	if (*kvList.*key != ".") {
	#		writeLine("stdout", "  - GOT:   *key: <" ++ *kvList.*key ++ ">");
	#	}
	#}

	uuYcTokensIdentifyDataset(*kvList, *bool);
	if (*bool) {
		#writeLine("stdout",
		#	"======= DATASET GET: "
		#	++   "W<" ++ *kvList."wave"
		#	++ "> E<" ++ *kvList."experiment_type"
		#	++ "> P<" ++ *kvList."pseudocode"
		#	++ ">"
		#);
		uuYcTokensToMetaData(*kvList);
	}
}

# \brief Extract one or more tokens from a file / directory name and add dataset
#        information as metadata.
#
# \param[in]     path
# \param[in]     name
# \param[in]     isCollection
# \param[in,out] scopedBuffer
#
uuYcExtractTokensFromFileName(*path, *name, *isCollection, *scopedBuffer) {
	uuChopFileExtension(*name, *baseName, *extension);
	#writeLine("stdout", "Extract tokens from <*baseName>");

	*parts = split(*baseName, "-");
	foreach (*part in *parts) {
		#writeLine("stdout", "- <*part>");
		uuYcExtractTokens(*part, *scopedBuffer);
	}
}

# \brief Mark an object as scanned.
#
# Sets the username of the scanner and a timestamp as metadata on the scanned object.
#
# \param[in] path
# \param[in] isCollection
#
uuYcIntakeScanMarkScanned(*path, *isCollection) {
	msiGetIcatTime(*timestamp, "unix");
	# NOTE: Commented out for debugging.
	#uuSetMetaData(
	#	*path,
	#	"scanned",
	#	"$userNameClient:*timestamp",
	#	if *isCollection then "-C" else "-d"
	#);
}

# \brief Mark a data object as not belonging to a dataset.
#
# \param[in] path
#
uuYcIntakeScanMarkUnusedFile(*path) {
	uuSetMetaData(*path, "error", "Experiment type, wave or pseudocode missing from path", "-d");
}

# \brief Recursively scan a directory in a Youth Cohort intake.
#
# \param[in] root      the directory to scan
# \param[in] scope     a scoped kvlist buffer
# \param[in] inDataset whether this collection is within a dataset collection
#
uuYcIntakeScanCollection(*root, *scope, *inDataset) {

	# Scan files under *root.
	foreach (*item in SELECT DATA_NAME, COLL_NAME WHERE COLL_NAME = *root) {

		uuChopFileExtension(*item."DATA_NAME", *baseName, *extension);
		#writeLine("stdout", "");
		#writeLine("stdout", "Scan file " ++ *item."DATA_NAME");

		*path = *item."COLL_NAME" ++ "/" ++ *item."DATA_NAME";

		uuYcRemoveDatasetMetaData(*path, false);
		uuYcIntakeScanMarkScanned(*path, false);

		if (*inDataset) {
			uuYcIntakeScanApplyDatasetMetaData(*scope, *path, false, false);
		} else {
			*subScope."." = ".";
			uuKvClone(*scope, *subScope);
			uuYcExtractTokensFromFileName(*item."COLL_NAME", *item."DATA_NAME", false, *subScope);

			uuYcTokensIdentifyDataset(*subScope, *bool);
			if (*bool) {
				# We found a top-level dataset data object.
				uuYcTokensToMetaData(*subScope);
				uuYcIntakeScanApplyDatasetMetaData(*subScope, *path, false, true);
			} else {
				uuYcIntakeScanMarkUnusedFile(*path);
			}
		}
	}

	# Scan collections under *root.
	foreach (*item in SELECT COLL_NAME WHERE COLL_PARENT_NAME = *root) {
		uuChopPath(*item."COLL_NAME", *parent, *dirName);
		if (*dirName != "/") {
			#writeLine("stdout", "");
			#writeLine("stdout", "Scan dir " ++ *dirName);

			*path = *item."COLL_NAME";

			uuYcRemoveDatasetMetaData(*path, true);

			*childInDataset = *inDataset;
			if (*inDataset) {
				uuYcIntakeScanApplyDatasetMetaData(*scope, *path, true, false);
				uuYcIntakeScanMarkScanned(*path, true);
			} else {
				*subScope."." = ".";
				uuKvClone(*scope, *subScope);
				uuYcExtractTokensFromFileName(*item."COLL_NAME", *dirName, true, *subScope);

				uuYcTokensIdentifyDataset(*subScope, *bool);
				if (*bool) {
					*childInDataset = true;
					# We found a top-level dataset collection.
					uuYcTokensToMetaData(*subScope);
					uuYcIntakeScanApplyDatasetMetaData(*subScope, *path, true, true);
				}
			}

			uuYcIntakeScanCollection(*item."COLL_NAME", *subScope, *childInDataset);
		}
	}
}

# \brief Find dataset ids under *root.
#
# \param[in]  root
# \param[out] ids  a list of dataset ids
#
uuYcIntakeGetDatasetIds(*root, *ids) {
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
uuYcIntakeDatasetGetToplevelObjects(*root, *id, *objects, *isCollection) {
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
	writeLine("stdout", "Got dataset toplevel objects for <*id>: *objectsString");
}

# \brief Run checks on the dataset specified by the given dataset id.
#
# This function adds warnings and errors to objects within the dataset.
#
# \param[in] root
# \param[in] id
#
uuYcIntakeCheckDataset(*root, *id) {
	uuYcIntakeDatasetGetToplevelObjects(*root, *id, *toplevels, *isCollection);
	uuYcIntakeDatasetParseId(*id, *idComponents);

	# TODO: Determine which checks to run based on *idComponents."experiment_type".
	# TODO: Run checks.
}

# \brief Run checks on all datasets under *root.
#
# \param[in] root
#
uuYcIntakeCheckDatasets(*root) {
	uuYcIntakeGetDatasetIds(*root, *ids);
	foreach (*id in *ids) {
		writeLine("stdout", "Scanning dataset id <*id>");
		uuYcIntakeCheckDataset(*root, *id);
	}
}

# \brief Detect datasets under *root and check them.
#
# \param[in] root
#
uuYcIntakeScan(*root, *status) {

	*status = 1;

	uuLock(*root, *lockStatus);
	writeLine("stdout", "lockstatus: *lockStatus");
	if (*lockStatus == 0) {
		# Pre-define all used KVs to avoid hackery in uuKvExists().
		*scope."." = ".";

		# Extracted WEPV, translated to metadata values (translation is necessary for date/time values).
		*scope."meta_wave"            = ".";
		*scope."meta_experiment_type" = ".";
		*scope."meta_pseudocode"      = ".";
		*scope."meta_version"         = ".";

		# Extracted WEPV, as found in pathname components.
		*scope."wave"            = ".";
		*scope."experiment_type" = ".";
		*scope."pseudocode"      = ".";
		*scope."version"         = ".";

		#*scope."year"   = ".";
		#*scope."month"  = ".";
		#*scope."day"    = ".";
		#*scope."hour"   = ".";
		#*scope."minute" = ".";
		#*scope."second" = ".";
		#*scope."date"   = ".";

		uuYcIntakeScanCollection(*root, *scope, false);
		uuYcIntakeCheckDatasets(*root);

		uuUnlock(*root);
		*status = 0;
	} else {
		*status = 2;
	}
}

# \brief Adds a comment to the dataset specified by *datasetId.
#
# \param[in] root
# \param[in] datasetId
# \param[in] message
#
uuYcIntakeCommentAdd(*root, *datasetId, *message) {
	msiGetIcatTime(*timestamp, "unix");
	*comment = "$userNameClient:*timestamp:*message";

	uuYcIntakeDatasetGetToplevelObjects(*root, *datasetId, *toplevelObjects, *isCollection);

	foreach (*toplevel in *toplevelObjects) {
		msiAddKeyVal(*kv, "comment", "*comment");
		errorcode(msiAssociateKeyValuePairsToObj(*kv, *toplevel, if *isCollection then "-C" else "-d"));

		# This does not work for some reason.
		#uuSetMetaData(
		#	*toplevel,
		#	"comment",
		#	*comment,
		#	if *isCollection then "-C" else "-d"
		#);
	}
}

#input *root="/"
#output ruleExecOut
