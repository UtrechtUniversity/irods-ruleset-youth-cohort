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

# \brief Splits a file name into a base name and a file extension.
#
# \param[in]  fileName
# \param[out] baseName
# \param[out] extension
# 
uuChopFileExtension(*fileName, *baseName, *extension) {
	*baseName  = "";
	*extension = "";

	if (*fileName like "*.*") {
		*baseName  = trimr(*fileName, ".");
		*extension = substr(*fileName, strlen(*baseName) + 1, strlen(*fileName));
	} else {
		*baseName = *fileName;
	}
}

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

	if (errorcode(msiGetValByKey(*foundKvs, "hour", *value)) == 0) {
		*date =    *date
		        ++ *kvList."hour"
		        ++ *kvList."minute"
		        ++ *kvList."second";
	} else {
		*date = *date ++ "000000";
	}

	kvList."meta_date"       = *date;
	kvList."meta_pseudocode" = *kvList."pseudocode";
	kvList."meta_wave"       = *kvList."wave";
}

# \brief Check whether the tokens gathered so far are enough to indentify a dataset.
#
# \param[in] kvList a list of tokens
#
uuYcTokensIdentifyDataset(*kvList) =
	   errorcode(msiGetValByKey(*foundKvs, "pseudocode", *value)) == 0
	&& errorcode(msiGetValByKey(*foundKvs, "year",       *value)) == 0
	&& errorcode(msiGetValByKey(*foundKvs, "wave",       *value)) == 0;

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
	writeLine("stdout", "Extract from <*name>");
	uuChopFileExtension(*name, *baseName, *extension);

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
