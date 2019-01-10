#Author Niek Bats

randomCollCopy {
    #changes YYYY-MM-DD.hh:mm:ss into seconds since epoch format
    msiHumanToSystemTime(*datefrom, *datefrom)
    msiHumanToSystemTime(*datetill, *datetill)
 
    *pseudoList = split(*pseudoCodes,',');
    foreach(*ps in *pseudoList) {
        writeLine('stdout', *ps);
    }

    *datasetList = list(); # Uniquely holds all found datasets. 

    foreach(*row in SELECT COLL_OWNER_ZONE) {
        *zone=*row.COLL_OWNER_ZONE;
        foreach(*row2 in SELECT COLL_NAME
                   WHERE COLL_NAME like '/*zone/home/grp-intake-%'
                   AND META_COLL_ATTR_NAME = 'wave'
                   AND META_COLL_ATTR_VALUE = *wave
                   # AND COLL_CREATE_TIME between *datefrom *datetill
                   #datefrom must be the same amount of digits as datetill
                   #wont be a problem if chosing times from yodas existence till future
                   ) {
            *name=*row2.COLL_NAME;
	    # Now check experiment type.
	    # And then check against 1 or more pseudo codes.	
            foreach(*row3 in SELECT COLL_CREATE_TIME
                        WHERE COLL_NAME = *name
                        AND META_COLL_ATTR_NAME = 'experiment_type'
                        AND META_COLL_ATTR_VALUE = *experiment
                        ) {
                *collCreateTime=int(*row3.COLL_CREATE_TIME);
               
 	        # now check against whether 1 of N pseudocodes is present.
                # If so, then this dataset conforms to requirements and can be added to datasetList.
		*pseudoFound = false;
                foreach(*pc in *pseudoList) {
                    foreach(*row4 in SELECT COLL_CREATE_TIME 
			       WHERE COLL_NAME = *name
                               AND META_COLL_ATTR_NAME = 'pseudocode'
                               AND META_COLL_ATTR_VALUE = *pc ) {
                        *pseudoFound = true;
                        writeLine('stdout', *pc);

                    }

		    if (*pseudoFound) {
                        break;
                    }
                }

                if (*pseudoFound) { # check wether not in datasetList yet
                    *inList = false;
                    foreach(*datasetName in *datasetList) {
                        if (*datasetName == *name) {
                            *inList = true;
                            break;
                        }
                    }
                    if (!*inList) {
                        *datasetList = cons(*name, *datasetList);
                    }  
                }
            }
        }
    }

    writeLine('stdout', '----');
    # Loop through all names and write them into the array that is in the shell script 
    foreach(*datasetName in *datasetList) {
        writeLine('stdout', *datasetName);
    }
}

input *wave="15y", *experiment="discount", *pseudoCodes="aA20134,aA20234", *datefrom="2000-01-01.00:00:00", *datetill="2020-12-31.00:00:00"
output ruleExecOut
