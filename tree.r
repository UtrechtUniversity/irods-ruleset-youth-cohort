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
	


}
