ExportDatasetErrorsAndWarnings {
   ## OVERRULE PARAMS FOR NOW as I wasn't able to add multiple input params 
   *userNameParam="datamanager";
#   *studyParam="test";

   # Possibly use uuClientFullName as user, or $userNameClienterNameClient;  ????????????????????????
   # writeLine("stdout", "uuClientFullName: " ++ uuClientFullName);


   # Initialisation of variables based on command line parameters
   *user = *userNameParam;
   *study = *studyParam;
   *datamanagerGroup = 'grp-datamanager-' ++ *study;
   *studyFolder = "/" ++ $rodsZoneClient ++ "/"  ++ 'home/grp-intake-' ++ *studyParam;

#   writeLine('stdout', 'User: ' ++ *user);
#   writeLine('stdout', 'Study: ' ++ *study);
#   writeLine('stdout', 'Datamanager group: ' ++ *datamanagerGroup);
#   writeLine('stdout', 'Study folder: ' ++ *studyFolder);
#   writeLine('stdout', '-------------------------------------------------------------------');

   # Check whether user is a datamanager for the study involved
   *isDatamanager = false;
   foreach (*row in
            SELECT USER_NAME
            WHERE  USER_TYPE            = 'rodsgroup'
                    AND USER_NAME = *datamanagerGroup ) {

                uuGroupUserExists(*datamanagerGroup, *user, true, *membership)
                if (*membership) {
                        *isDatamanager = true;
                }
   }

   if (!*isDatamanager) {
	writeLine("stdout", 'Not the datamanager of curent group');
        succeed; # the journey ends here 
   }

   # Collect all data

   
   writeLine('stdout', "Wave,Experiment type,Pseudocode,Version,Bestand,Errors,Warnings");

   # At first find datasets, designated by presence of metadata attribute 'dataset_toplevel'.
   # The value of the datasetId is combination of wepv and path to make it unique.
   foreach(*row in SELECT COLL_ID, META_COLL_ATTR_NAME, META_COLL_ATTR_VALUE WHERE COLL_NAME like '*studyFolder%%' AND META_COLL_ATTR_NAME='dataset_toplevel') {
       msiGetValByKey(*row, "META_COLL_ATTR_VALUE", *datasetId);
#       writeLine("stdout", "dataset_toplevel: " ++ *datasetId); 

       # Collect all data objects with a given datasetId
       # And per data object find out whether it contains errors or warnings in its metadata       
       foreach(*row2 in SELECT META_DATA_ATTR_NAME, META_DATA_ATTR_VALUE, DATA_NAME, DATA_ID, COLL_NAME WHERE META_DATA_ATTR_VALUE='*datasetId') {
          msiGetValByKey(*row2, "DATA_NAME", *dataName);
          msiGetValByKey(*row2, "COLL_NAME", *collName);
          msiGetValByKey(*row2, "DATA_ID", *dataId);
	 
          # Given 1 object step thtough all its metadata attributes. 

          msiString2KeyValPair("", *kvp);

	  # build list of all attributes that are involved
          *attrList = list('wave', 'experiment_type', 'pseudocode', 'version', 'error', 'warning');
	  # initialize all attributes to empty strings
	  foreach (*attr in *attrList) {
              *kvp."*attr" = '';
          }
          
          foreach(*row3 in SELECT META_DATA_ATTR_NAME, META_DATA_ATTR_VALUE WHERE DATA_ID=*dataId ) {
              msiGetValByKey(*row3, "META_DATA_ATTR_NAME", *attrName);
              msiGetValByKey(*row3, "META_DATA_ATTR_VALUE", *attrValue);

#	      writeLine('stdout', 'LOGGING: ' ++ *attrName ++ ': ' ++ *attrValue);
 
              foreach (*attr in *attrList) {
                  #writeLine('stdout', 'attrLIST: ' ++ *attr);
                  if (*attrName==*attr) {
		      if (*attr=='error' || *attr=='warning') { # must be concatination as there can be more errors/warnings on 1 data object
		      	  if (strlen(*kvp."*attr")>0) {
		              *kvp."*attr" =  *kvp."*attr" ++ ' - ' ++ *attrValue;
			  }
			  else {
                              *kvp."*attr" = *attrValue;
			  }
		      }
		      else {
                          *kvp."*attr" = *attrValue;
		      }
                  }
              }
          }
	  # Add data object to file - only if errors or warnins present.
	  if (strlen(*kvp.'error')>0 || strlen(*kvp.'warning')>0) {
	      *dataPath = *collName ++ '/' ++ *dataName;
              writeLine('stdout', *kvp."wave" ++ "," ++ *kvp."experiment_type" ++ "," ++ *kvp."pseudocode"++ "," ++ *kvp."version" ++ "," ++ *dataPath ++ "," ++ *kvp."error" ++ "," ++ *kvp."warning");
          }
       }
   }
}


input *studyParam="test"
output ruleExecOut

