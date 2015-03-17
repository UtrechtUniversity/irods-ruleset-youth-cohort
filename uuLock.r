# \file
# \brief Locking functions
# \author Ton Smeele
# \copyright Copyright (c) 2015, Utrecht university. All rights reserved
# \license GPLv3, see LICENSE
#

#test {
#	uuLock("/tsm/home/rods",*result);
#	writeLine("stdout","lock result = *result");
#	uuUnlock("/tsm/home/rods");
#	writeLine("stdout","and unlocked again");
#}



# \brief uuLock  obtain a lock on a collection
# 
# \param[in] collection  name of the collection to be locked 
# \param[out] result     true = locked, false = lock failed (e.g. in use) 
#
uuLock(*collection, *result) {
	msiGetIcatTime(*dateTime, "unix");
	*lockId = $userNameClient ++ ":" ++ *dateTime;
	# let everyone know we need a lock	
	# NB: a race condition could happen when another process owned by 
	#     the same user requests a lock at the very same second.
	#     to minimize the risk we include username in the lockid
	msiString2KeyValPair("uuLockRequest=*lockId",*kvLockRequest);
	msiAssociateKeyValuePairsToObj(*kvLockRequest, *collection, "-C");
	# check upstream and on collection itself if lock (request) exists
	*path = "";
	*lockFound = false;
	foreach (*segment in split(*collection, '/')) { 
		*path = "*path/*segment";
		writeLine("stdout","testing for lock in path=*path=");
		if (*path != *collection) {
			uuLockExists(*path, *lockFound);
			if (*lockFound) {
				writeLine("stdout","lock found upstream at *path");
				break;
			}
		} else {
			# TODO check collection itself yet ignore our own request
			foreach (*row in SELECT META_COLL_ATTR_NAME,META_COLL_ATTR_VALUE
				WHERE COLL_NAME = *collection
		   	AND META_COLL_ATTR_NAME LIKE "uuLock%"
				) {
				msiGetValByKey(*row, "META_COLL_ATTR_NAME", *key);
				msiGetValByKey(*row, "META_COLL_ATTR_VALUE", *value);
				if ("*key=*value" != "uuLockRequest=*lockId"){
					*lockFound = true;
				}
			}	
		}
	}
	if (!*lockFound) {
		# also check downstream if other have (requested) a lock
		# we can check all subcollections in one go
		foreach (*rows in SELECT META_COLL_ATTR_NAME,COLL_NAME
					WHERE  COLL_PARENT_NAME LIKE '*collection%' 
					AND META_COLL_ATTR_NAME LIKE 'uuLock%'
			){
			# SELECT does not support 'OR' construct, therefore we need to
			# check and ignore collections that start with similar prefix
			# yet are in a different tree
			#    e.g. /zone/home/col/col2  and /zone/home/cola/col2
			#         both cases col2 appears to have parent "col%"
			msiGetValByKey(*rows, "COLL_NAME", *thisCollection);
			if (*thisCollection like "*collection/\*") {
				# we have an existing lock
				writeLine("stdout","downstream lock found");
				*lockFound = true;
				break;
			}
		}
	}
	if (*lockFound) {
		*result = false;
		# retract our lock request, someone else got a lock
		msiRemoveKeyValuePairsFromObj(*kvLockRequest, *collection, "-C");
	} else {
		# change our request into a real lock
		msiString2KeyValPair("uuLocked=*lockId",*kvLock);
		msiAssociateKeyValuePairsToObj(*kvLock, *collection, "-C");
		msiRemoveKeyValuePairsFromObj(*kvLockRequest, *collection, "-C");
		*result = true;
	}
}

#
# \brief  uuUnlock   unlocks a collection
#
# \param[in] collection  name of the collection to unlock
uuUnlock(*collection) {
	# NB: always succeeds regardless if lock actually exists 
	foreach (*rows in SELECT META_COLL_ATTR_VALUE
				WHERE COLL_NAME = '*collection' 
				AND META_COLL_ATTR_NAME = 'uuLocked'
		){
		# should return max 1 row, otherwise we have multiple locks??
		msiGetValByKey(*rows,"META_COLL_ATTR_VALUE",*lockValue);
		msiString2KeyValPair("uuLocked=*lockValue",*kvLocked);
		msiRemoveKeyValuePairsFromObj(*kvLocked, *collection, "-C")
	}
}

# \brief see if a collection has a lock on it
#
# \param[in] collection  name of the collection
# \param[out] result     true if collection has a lock(request)
uuLockExists(*collection, *result) {
	# NB: reports true for both existing locks and lock requests
	*result = false;
	msiGetIcatTime(*currentTime, "unix");
	foreach (*row in SELECT META_COLL_ATTR_NAME,META_COLL_ATTR_VALUE
			WHERE COLL_NAME = *collection
		   AND META_COLL_ATTR_NAME LIKE "uuLock%"
		) {
		# rows found means there is an existing lock (request)
		# our last hope is that this is an expired request that we can ignore 
		msiGetValByKey(*row,"META_COLL_ATTR_NAME",*lockKey);
		msiGetValByKey(*row,"META_COLL_ATTR_VALUE",*lockValue);
		writeLine("stdout","x=*lockKey and y=*lockValue");
		*lockTime = double(uuLockGetDateTime(*lockValue));
		if ( 
			    ((*lockTime + 5 * 60) < *currentTime)
			 && (*lockKey == "lockRequest")
			) {
			# cleanup lock requests older than 5 minutes
			writeLine("stdout","need to cleanup lock *lockKey=*lockValue");
		   msiString2KeyValPair("*lockKey=*lockValue",*kvExpiredLock);
		   msiRemoveKeyValuePairsFromObj(*kvExpiredLock, *collection, "-C");
		} else {
			# there is a valid existing lock 
			*result = true;
		}
	}
}

# \brief function to get the username part of a lock
#
# \param[in] lock  name of the lock
# \return username
uuLockGetUser(*lock) = substr(*lock,0,
								strlen(*lock) - strlen(triml(*lock,":")) -1);

# \brief fucntion to get the datestamp part of a lock
# 
# \param[in] lock  name of the lock
# \return datetimestamp (in seconds since epoch)
uuLockGetDateTime(*lock) = triml(*lock,":");


#input null
#output ruleExecOut
