# \file
# \brief generic function to walk collection trees
# \author Ton Smeele
# \copyright Copyright (c) 2015, Utrecht university. All rights reserved
# \license GPLv3, see LICENSE

test {
	uuTreeWalk(*direction, *topLevelCollection, *ruleToProcess);
}


# \brief walks through a collection tree and perform an arbitrary action
# 
# \param[in] direction           can be "forward" or "reverse" 
#                                forward means process collection itself, then childs
#                                reverse means process childs first
#                                reverse is useful e.g. to delete collection trees
# \param[in] topLevelCollection  pathname of the root of the tree, must be collection
#                                NB: the root itself will not be processed, only children
# \param[in] ruleToProcess       name of the rule that can perform an action on tree items
#                                The rule should expect the following parameters:
#                                  itemPath  = full iRODS path to the collection/object
#                                  itemName  = last part of the itemPath
#                                  itemIsCollection = true if the item is a collection
#                                  scopedBuffer = in/out Key-Value variable
#                                       the buffer is maintained by treewalk and passed
#                                       on to the processing rule. can be used by the rule
#                                       to communicate data to subsequent rule invocations
#


uuTreeWalk(*direction, *topLevelCollection, *ruleToProcess) {

	*buffer."path" = *topLevelCollection;

	uuTreeWalkCollection(
			*direction,
			*topLevelCollection,
			*buffer, 
			*ruleToProcess
	);
}

uuTreeGetLastSegment(*path, *segment) {
	*pathPart = trimr(*path, "/");
	*segment = substr(*path, strlen(*pathPart) + 1, strlen(*path));
}

uuTreeWalkCollection(
			*direction,
			*path,
			*buffer, 
			*ruleToProcess
	) {
	uuTreeGetLastSegment(*path, *collection);
	if (*direction == "forward") {
		# first process this collection itself
		eval("{ *ruleToProcess(\*path,\*collection,true,\*buffer); }");
		# and the dataobjects located directly within the collection
		foreach (*row in SELECT DATA_NAME WHERE COLL_NAME = *path) {
			msiGetValByKey(*row, "DATA_NAME", *dataObject);
			eval("{ *ruleToProcess(\*path,\*dataObject,false,\*buffer); }");
		}
		# then increase depth to walk through the subcollections
		foreach (*row in SELECT COLL_NAME WHERE COLL_PARENT_NAME = *path) {
			msiGetValByKey(*row, "COLL_NAME", *subCollectionPath);
			uuTreeWalkCollection(
					*direction,
					*subCollectionPath,
					*buffer, 
					*ruleToProcess
			);
		}
	}
	if (*direction == "reverse") {
		# first deal with any subcollections within this collection
		foreach (*row in SELECT COLL_NAME WHERE COLL_PARENT_NAME = *path) {
			msiGetValByKey(*row, "COLL_NAME", *subCollectionPath);
			uuTreeWalkCollection(
					*direction, 
					*subCollectionPath, 
					*buffer,
					*ruleToProcess
			);
		}
		# when done then process the dataobjects directly located within this collection
		foreach (*row in SELECT DATA_NAME WHERE COLL_NAME = *path) {
			msiGetValByKey(*row, "DATA_NAME", *dataObject);
			eval("{ *ruleToProcess(\*path,\*dataObject,false,\*buffer); }");
		}
		# and lastly process the collection itself
		eval("{ *ruleToProcess(\*path,\*collection,true,\*buffer); }");
	}
}



input *direction="forward",*topLevelCollection="/tsm/home/rods",*ruleToProcess="myRule"
output ruleExecOut
