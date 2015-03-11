# \file
# \brief     Youth Cohort - Intake dataset scanner.
# \author    Chris Smeele
# \copyright Copyright (c) 2015, Utrecht University. All rights reserved.
# \license   GPLv3, see LICENSE.txt.

test {
	#*kvList."_" = "";
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
	*empty."_" = "";
	*kvList = *empty;
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
	# The user may have specified the same kv list for *list1 and *result,
	# so we cannot clear *result before backing up *list1.
	uuKvClone(*list1, *tempInput);
	uuKvClear(*result);
	*list1 = *tempInput;

	uuKvClone(*list1, *result);

	foreach (*key in *list2) {
		if (!uuKvExists(*result, *key)) {
			*result.*key = *list2.*key;
		}
	}
}

uuKvExists(*kvList, *key) =
	errorcode(*kvList.*key) == 0

# \brief Convert tokens to metadata.
#
# Converts separate year/month/day/hour/minute/second keys to a single date string.
#
# \param[in] kvList
#
uuYcTokensToMetaData(*kvList) {
	*date =    *kvList."year"
	        ++ *kvList."month"
	        ++ *kvList."day";

	#if (errorcode(msiGetValByKey(*kvList, "hour", *value)) == 0) {
	#	*date =    *date
	#	        ++ *kvList."hour"
	#	        ++ *kvList."minute"
	#	        ++ *kvList."second";
	#} else {
	#	*date = *date ++ "000000";
	#}

	kvList."meta_date"       = *date;
	kvList."meta_pseudocode" = *kvList."pseudocode";
	kvList."meta_wave"       = *kvList."wave";
}

# \brief Check whether the tokens gathered so far are sufficient for indentifyng a dataset.
#
# \param[in] tokens a key-value list of tokens
#
uuYcTokensIdentifyDataset(*tokens) =
	   uuKvExists(*tokens, "wave")
	&& uuKvExists(*tokens, "experiment_type")
	&& uuKvExists(*tokens, "pseudocode");

# \brief Extract tokens from a string.
#
# \param[in] string
# \param[in] kvList a list of tokens and metadata already detected
#
uuYcExtractTokens(*string, *kvList) {

	*foundKvs."_" = "";

	if (*string like regex ``^-?[0-9]{1,2}[wmy]$``) {
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
	} else if (*string like regex ``^y[0-9]{5}$``) {
		# String contains a pseudocode.
		*foundKvs."pseudocode" = substr(*string, 1, 6);
	} else {
		writeLine("stdout", "  - no pattern recognized");
	}
	
	if (uuYcTokensIdentifyDataset(*foundKvs)) {
		uuYcTokensToMetaData(*foundKvs);
	}

	foreach (*key in *foundKvs) {
		if (*key != "_") {
			writeLine("stdout", "  - *key: <" ++ *foundKvs.*key ++ ">");
		}
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

# \brief Recursively scan a directory in a Youth Cohort intake.
#
# \param[in] root          the directory to scan
# \param[in] scope         a scoped kvlist buffer
# \param[in] datasetBuffer a kvlist that contains properties related to this dataset
# \param[in] inDataset     a boolean indicating whether this directory is within a
#                          dataset (and appropriate metadata has been set in the
#                          datasetBuffer)
#
uuYcIntakeScanCollection(*root, *scope, *datasetBuffer, *inDataset) {
	foreach(*item in SELECT DATA_NAME, COLL_NAME WHERE COLL_NAME = *root) {

		uuChopFileExtension(*item."DATA_NAME", *baseName, *extension);
		writeLine("stdout", "");
		writeLine("stdout", "Scan file " ++ *item."DATA_NAME" ++ " (base: " ++ *baseName ++ ", extension: " ++ *extension ++ ")");
		writeLine("stdout", "---------------------------");

		*subScope = *scope;
		uuYcExtractTokensFromFileName(*item."COLL_NAME", *item."DATA_NAME", false, *subScope);
	}

	foreach(*item in SELECT COLL_NAME WHERE COLL_PARENT_NAME = *root) {
		if (*root == "/") {
			if (*item."COLL_NAME" == "/") { succeed(); }
			*dirName = *item."COLL_NAME";
		} else {
			*dirName = substr(*item."COLL_NAME", strlen(*root) + 1, strlen(*item."COLL_NAME"));
		}
		writeLine("stdout", "");
		writeLine("stdout", "Scan dir " ++ *dirName);
		writeLine("stdout", "---------------------------");

		*subScope = *scope;

		if (*inDataset) {
			# TODO
		} else {
			uuYcExtractTokensFromFileName(*item."COLL_NAME", *dirName, true, *subScope);
		}

		uuYcIntakeScanCollection(*item."COLL_NAME", *subScope, *datasetBuffer, *inDataset);
	}
}

uuYcIntakeScan(*root) {
	*scope."_"         = "";
	*datasetBuffer."_" = "";
	uuYcIntakeScanCollection(*root, *scope, *datasetBuffer, false);
}

input *name="25m_Echo_20150924", *root="/"
output ruleExecOut
