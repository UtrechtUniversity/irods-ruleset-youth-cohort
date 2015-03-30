# \file
# \brief ycPolicies.r   Youth Cohort specific policies
# \author Ton Smeele
# \copyright Copyright (c) 2015, Utrecht university. All rights reserved
# \license GPLv3, see LICENSE
#
#test {
#	writeLine("stdout","hi");
#}

#

acPreprocForDataObjOpen {
	ON (($writeFlag == "1") && ($objPath like '/$rodsZoneClient/home/grp-intake-*')) {
		uuYcObjectIsLocked(*objPath, *locked);
	if (*locked) {
		cut;
		msiOprDisallowed;
	}
}

acDataDeletePolicy {
	ON ($objPath like '/$rodsZoneClient/home/grp-intake-*') {
		uuYcObjectIsLocked(*objPath, *locked);
	if (*locked) {
		cut;
		msiDeleteDisallowed();
	}
}

#acPreProcForFilePathReg {}
#	ON ($objPath like '/$rodsZoneClient/home/grp-intake-*') {
#		uuYcIntakeLockCheck($objPath);
#	}

#acPreProcForCreate {  # 1
#	ON ($objPath like '/$rodsZoneClient/home/grp-intake-*') {
#		uuYcIntakeLockCheck($objPath);
#	}
#}

#acPreProcForCollCreate {}
#	}

acPreProcForRmColl {
	ON ($objPath like '/$rodsZoneClient/home/grp-intake-*') {
		uuYcObjectIsLocked(*objPath, *locked);
	if (*locked) {
		cut;
		msiOprDisallowed;
	}
}

acPreProcForObjRename(*source, *destination) {
	ON (*source like '/$rodsZoneClient/home/grp-intake-*') {
		uuYcObjectIsLocked(*source, *locked);
	if (*locked) {
		cut;
		msiOprDisallowed;
	}
}

uuYcObjectIsLocked(*objPath, *locked) {
	msiGetObjType(*objPath, *objType);
	*locked = false;
	if (*objType == '-d') {
		msiSplitPath(*objPath, *collection, *dataName);
		foreach (*row in SELECT META_DATA_ATTR_VALUE
					WHERE COLL_NAME = '*collection'
					  AND DATA_NAME = '*dataName'
					  AND META_DATA_ATTR_NAME = 'to_vault_lock'
			) {
			*locked = true;
			break;
		}
	} else {
		foreach (*row in SELECT META_COLL_ATTR_VALUE
					WHERE COLL_NAME = '*objPath'
					  AND META_COLL_ATTR_NAME = 'to_vault_lock'
			) {
			*locked = true;
			break;
		}
	}
}

#input null
#output ruleExecOut
