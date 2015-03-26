# \file
# \brief title
# \author Ton Smeele
# \copyright Copyright (c) 2015, Utrecht university. All rights reserved
# \license GPLv3, see LICENSE

#test {
#	writeLine("stdout","intaker studies");
#	uuYcIntakerStudies(*studies);
#	writeLine("stdout","enlisted in: *studies");
#}


# \brief uuYcIntakerStudies  list of studies that the user is enlisted in
#            
# \param[out] studies  comma separated list of studies		
#
uuYcIntakerStudies(*studies){
	uuGroupMemberships($userNameClient,*groups);
	*studies="";
	*prefix="grp-intake-";
	foreach (*group in split(*groups,",")) {
		if (*group like "*prefix*") {
			*study = triml(*group,*prefix);
			*studies="*studies,*study";
		}
	}
	*studies=triml(*studies,",");
}

#input null
#output ruleExecOut
