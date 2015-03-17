# \file
# \brief     Youth Cohort - Intake dataset scanner.
# \author    Chris Smeele
# \copyright Copyright (c) 2015, Utrecht University. All rights reserved.
# \license   GPLv3, see LICENSE.txt.

test {
	#*kvList."." = "";
	#uuYcExtractTokensFromFileName(*name, *name, true, *kvList);
	uuYcIntakeScan(*root);
}

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
uuChopFileExtension(*fileName, *baseName, *extension) =
	uuChop(*fileName, *baseName, *extension, ".", false);

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

uuKvExists(*kvList, *key, *bool) {
	#if (errorcode(*kvList.*key) == 0) {
		*bool = (*kvList.*key != '.');
	#} else {
	#	*bool = false;
	#}
}

# \brief Check if a key exists in a key-value list.
#
# \param[in] kvList
# \param[in] key
#
uuKvExists_old(*kvList, *key) =
	(errorcode(*kvList.*key) == 0);


uuYcDoSetMetaData(*path, *key, *value, *type) {
	# FIXME use associate instead of set to allow multiple errors / warnings per object.
	msiAddKeyVal(*kv, *key, *value);
	writeLine("stdout", "SET ========================= *path - *key => *value");
	msiPrintKeyValPair("stdout", *kv);
	errorcode(msiSetKeyValuePairsToObj(*kv, *path, *type));
	writeLine("stdout", "END ============================");
}

uuYcIntakeApplyMetaData(*scope, *path, *isCollection) {

	writeLine("stdout", "WRITING METADATA TO *path *isCollection");

	uuYcDoSetMetaData(
		*path,
		"wave",
		*scope."meta_wave",
		if *isCollection then "-C" else "-d"
	);
	uuYcDoSetMetaData(
		*path,
		"experiment_type",
		*scope."meta_experiment_type",
		if *isCollection then "-C" else "-d"
	);
	uuYcDoSetMetaData(
		*path,
		"pseudocode",
		*scope."meta_pseudocode",
		if *isCollection then "-C" else "-d"
	);
}

uuYcDoRemoveMetaData(*path, *key, *value, *type) {
	msiAddKeyVal(*kv, *key, *value);
	writeLine("stdout", "REMOVE ========================= *path - *key => *value");
	msiPrintKeyValPair("stdout", *kv);
	#msiRemoveKeyValuePairsFromObj(*kv, *path, *type);
	errorcode(msiRemoveKeyValuePairsFromObj(*kv, *path, *type));
	writeLine("stdout", "END ============================");
}

uuYcRemoveDatasetMetaData(*path, *isCollection) {

	if (*isCollection) {
		msiMakeGenQuery("COLL_ID, META_COLL_ATTR_NAME, META_COLL_ATTR_VALUE", "COLL_NAME = '*path' AND META_COLL_ATTR_NAME IN ('wave', 'experiment_type', 'pseudocode')", *genQIn);
		msiExecGenQuery(*genQIn, *genQOut);

		writeLine("stdout", "");
		writeLine("stdout", "STUFF......................");
		foreach(*row in *genQOut) {
			if (
				   *row."META_COLL_ATTR_NAME" == "wave"
				|| *row."META_COLL_ATTR_NAME" == "experiment_type"
				|| *row."META_COLL_ATTR_NAME" == "pseudocode"
			) {
				writeLine("stdout", "*path HAS METADATA ATTR <" ++ *row."META_COLL_ATTR_NAME" ++ ">, REMOVING");
				uuYcDoRemoveMetaData(*path, *row."META_COLL_ATTR_NAME", *row."META_COLL_ATTR_VALUE", "-C");
			}
		}
	} else {
		uuChopPath(*path, *parent, *baseName);
		msiMakeGenQuery("DATA_ID, META_DATA_ATTR_NAME, META_DATA_ATTR_VALUE", "DATA_NAME = '*baseName' AND META_DATA_ATTR_NAME IN ('wave', 'experiment_type', 'pseudocode')", *genQIn);
		msiExecGenQuery(*genQIn, *genQOut);

		writeLine("stdout", "");
		writeLine("stdout", "STUFF...................... REMOVE FROM *path");
		foreach(*row in *genQOut) {
			if (
				   *row."META_DATA_ATTR_NAME" == "wave"
				|| *row."META_DATA_ATTR_NAME" == "experiment_type"
				|| *row."META_DATA_ATTR_NAME" == "pseudocode"
			) {
				writeLine("stdout", "*path HAS METADATA ATTR <" ++ *row."META_DATA_ATTR_NAME" ++ ">, REMOVING");
				uuYcDoRemoveMetaData(*path, *row."META_DATA_ATTR_NAME", *row."META_DATA_ATTR_VALUE", "-d");
			}
		}
	}
}

uuYcIntakeApplyNotice(*level, *message, *path, *isCollection) {

}


# \brief Convert tokens to metadata.
#
# Converts separate year/month/day/hour/minute/second keys to a single date string.
#
# \param[in] kvList
#
uuYcTokensToMetaData(*kvList) {
	#*date =    *kvList."year"
	#        ++ *kvList."month"
	#        ++ *kvList."day";

	#if (errorcode(msiGetValByKey(*kvList, "hour", *value)) == 0) {
	#	*date =    *date
	#	        ++ *kvList."hour"
	#	        ++ *kvList."minute"
	#	        ++ *kvList."second";
	#} else {
	#	*date = *date ++ "000000";
	#}

	#msiPrintKeyValPair("stdout", *kvList);

	*kvList."meta_experiment_type" = *kvList."experiment_type";
	*kvList."meta_pseudocode"      = *kvList."pseudocode";
	*kvList."meta_wave"            = *kvList."wave";
}

# \brief Check whether the tokens gathered so far are sufficient for indentifyng a dataset.
#
# \param[in] tokens a key-value list of tokens
#
#uuYcTokensIdentifyDataset(*tokens) =
#	   uuKvExists(*tokens, "wave")
#	&& uuKvExists(*tokens, "experiment_type")
#	&& uuKvExists(*tokens, "pseudocode");

uuYcTokensIdentifyDataset(*tokens, *complete) {
	*toCheck = list(
		"wave",
		"experiment_type",
		"pseudocode"
	);

	*complete = true;
	foreach (*check in *toCheck) {
		*bool = false;
		uuKvExists(*tokens, *check, *bool)
		if (!*bool) {
			*complete = false;
			break;
		}
	}
}

# \brief Extract tokens from a string.
#
# \param[in] string
# \param[in] kvList a list of tokens and metadata already detected
#
uuYcExtractTokens(*string, *kvList) {

	*foundKvs."." = ".";

	if (*string like regex ``^-?[0-9]{1,2}[wmj]$``) {
		# String contains a wave.
		*foundKvs."wave" = *string;
	} else if (*string like regex ``^(Y[0-9]{4}M[0-9]{2}|D[0-9]{2}|[0-9]{8}(\.[0-9]{4}([0-9]{2})?)?)$``) {
		# String contains (part of) a date, and possibly a time.
		if (*string like regex ``^Y[0-9]{4}M[0-9]{2}$``) {
			# Y....M../D.. format, year + month part.
			*foundKvs."year"  = substr(*string, 1, 5);
			*foundKvs."month" = substr(*string, 6, 8);
		} else if (*string like regex ``D[0-9]{2}``) {
			# Y....M../D.. format, day part.
			*foundKvs."day" = substr(*string, 1, 3);
		} else {
			# YYYYMMDD format.
			# Extract year, month and day first.
			*foundKvs."year"  = substr(*string, 0, 4);
			*foundKvs."month" = substr(*string, 4, 6);
			*foundKvs."day"   = substr(*string, 6, 8);

			# Check if a time was given.
			if (*string like regex ``.*\..*``) {
				*foundKvs."hour"   = substr(*string, 9,  11);
				*foundKvs."minute" = substr(*string, 11, 13);
				if (*string like regex ``.*\.[0-9]{6}$``) {
					*foundKvs."second" = substr(*string, 13, 15);
				} else {
					*foundKvs."second" = "00";
				}
			}
		}
		#if (errorcode(msiGetValByKey(*foundKvs, "hour", *value)) == 0) {
		#	# A time can only be given in combination with a YYYYMMDD date,
		#	# so if we don't have a time here, we can set it to 00:00:00.
		#	*foundKvs."hour"   = "00";
		#	*foundKvs."minute" = "00";
		#	*foundKvs."second" = "00";
		#}
	} else if (*string like regex ``^Y[0-9]{5}$``) {
		# String contains a pseudocode.
		*foundKvs."pseudocode" = substr(*string, 1, 6);
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
			writeLine("stdout", "  - no pattern recognized");
		}
	}

	foreach (*key in *foundKvs) {
		if (*key != ".") {
			writeLine("stdout", "  - FOUND: *key: <" ++ *foundKvs.*key ++ ">");
		}
	}

	*result."." = ".";
	uuKvMerge(*kvList, *foundKvs, *result);
	*kvList = *result;

	foreach (*key in *kvList) {
		if (*key != ".") {
			writeLine("stdout", "  - GOT:   *key: <" ++ *kvList.*key ++ ">");
		}
	}

	uuYcTokensIdentifyDataset(*kvList, *bool);
	if (*bool) {
		writeLine("stdout",
			"======= DATASET GET: "
			++   "W<" ++ *kvList."wave"
			++ "> E<" ++ *kvList."experiment_type"
			++ "> P<" ++ *kvList."pseudocode"
			++ ">"
		);
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
	writeLine("stdout", "Extract tokens from <*baseName>");

	*parts = split(*baseName, "-")
	foreach (*part in *parts) {
		writeLine("stdout", "- <*part>");
		uuYcExtractTokens(*part, *scopedBuffer);
	}
}

uuYcIntakeScanMarkFilesWithoutDataset(*path) {
}

uuYcIntakeScanMarkUnusedFile(*path) {
	uuYcDoSetMetaData(*path, "error", "Experiment type, wave or pseudocode missing from path", "-d");
}

# \brief Recursively scan a directory in a Youth Cohort intake.
#
# \param[in] root          the directory to scan
# \param[in] scope         a scoped kvlist buffer
# \param[in] datasetBuffer a kvlist that contains properties related to this dataset
# \param[in] inDataset     a boolean indicating whether this directory is within a
#                          dataset (and appropriate metadata has been set in the
#                          datasetBuffer)
#
uuYcIntakeScanCollection(*root, *scope, *datasetBuffer, *inDataset, *containsDataset) {
	foreach(*item in SELECT DATA_NAME, COLL_NAME WHERE COLL_NAME = *root) {

		uuChopFileExtension(*item."DATA_NAME", *baseName, *extension);
		writeLine("stdout", "");
		writeLine("stdout", "Scan file " ++ *item."DATA_NAME");

		#msiString2KeyValPair("", *subScope);
		*subScope."." = ".";
		uuKvClone(*scope, *subScope);

		*path = *item."COLL_NAME" ++ "/" ++ *item."DATA_NAME";

		uuYcRemoveDatasetMetaData(*path, false);

		if (*inDataset) {
			# TODO
		} else {
			uuYcExtractTokensFromFileName(*item."COLL_NAME", *item."DATA_NAME", false, *subScope);

			# Note: '&&' does not short-circuit in iRODS. Better use nested ifs here.
			uuYcTokensIdentifyDataset(*subScope, *bool);
			if (*bool) {
				# We found a top-level data-set object.
				uuYcTokensToMetaData(*subScope);
				uuYcIntakeApplyMetaData(*subScope, *path, false);
			} else {
				uuYcIntakeScanMarkUnusedFile(*path);
			}
		}
	}

	foreach(*item in SELECT COLL_NAME WHERE COLL_PARENT_NAME = *root) {
		uuChopPath(*item."COLL_NAME", *parent, *dirName);
		if (*dirName != "/") {
			writeLine("stdout", "");
			writeLine("stdout", "Scan dir " ++ *dirName);

			#msiString2KeyValPair("", *subScope);
			*subScope."." = ".";
			uuKvClone(*scope, *subScope);

			*path = *item."COLL_NAME";

			uuYcRemoveDatasetMetaData(*path, true);

			if (*inDataset) {
				# TODO
			} else {
				uuYcExtractTokensFromFileName(*item."COLL_NAME", *dirName, true, *subScope);

				uuYcTokensIdentifyDataset(*subScope, *bool);
				if (*bool) {
					# We found a top-level data-set collection.
					uuYcTokensToMetaData(*subScope);
					uuYcIntakeApplyMetaData(*subScope, *path, true);
				}
			}

			uuYcIntakeScanCollection(*item."COLL_NAME", *subScope, *datasetBuffer, *inDataset, *containsDataset);
		}
	}
}

uuYcIntakeScan(*root) {
	*scope."." = ".";
	#uuKvClear(*scope);
	*datasetBuffer."." = ".";
	#uuKvClear(*datasetBuffer);

	*scope."."         = ".";
	*scope."wave"            = ".";
	*scope."experiment_type" = ".";
	*scope."pseudocode"      = ".";
	*scope."year"   = ".";
	*scope."month"  = ".";
	*scope."day"    = ".";
	*scope."hour"   = ".";
	*scope."minute" = ".";
	*scope."second" = ".";
	*scope."date"   = ".";

	*datasetBuffer."." = ".";

	uuYcIntakeScanCollection(*root, *scope, *datasetBuffer, false, *bool);
}

input *root="/"
output ruleExecOut
