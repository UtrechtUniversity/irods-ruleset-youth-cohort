# \file
# \brief     Youth Cohort - Dataset query related functions.
# \author    Ton Smeele
# \copyright Copyright (c) 2015, Utrecht University. All rights reserved.
# \license   GPLv3, see LICENSE

#test {
#  *root = "/nluu1ot/home/grp-intake-youth";
#  uuYcDatasetGetIds(*root, *ids);
#  foreach (*datasetId in *ids) { 
#     uuYcQueryDataset(*datasetId, *wave, *expType, *pseudocode, *version, 
#                      *datasetStatus, *datasetCreateName, *datasetCreateDate, 
#                      *datasetErrors, *datasetWarnings, *datasetComments,
#                      *objects, *objectErrors, *objectWarnings);
# 
#   writeLine("stdout", "datasetId = *datasetId");
#   writeLine("stdout", "wepv = *wave, *expType, *pseudocode, *version");
#   writeLine("stdout", "status = *datasetStatus, create = *datasetCreateName, date = *datasetCreateDate");
#   writeLine("stdout", "set errors/warnings/comments: *datasetErrors *datasetWarnings *datasetComments");
#   writeLine("stdout", "object errors/warnings/number: *objectErrors, *objectWarnings, *objects"); 
#   }
#}


# \brief query dataset overview information
#
# \param[in]  datasetid   unique id of the dataset
# \param[out] .... all other parameters, see below

uuYcQueryDataset(*datasetId, *wave, *expType, *pseudocode, *version, 
                 *datasetStatus, *datasetCreateName, *datasetCreateDate, 
                 *datasetErrors, *datasetWarnings, *datasetComments,
                 *objects, *objectErrors, *objectWarnings) {
   uuYcDatasetParseId(*datasetId, *idComponents);
   *wave       = *idComponents."wave";
   *expType    = *idComponents."experiment_type";
   *pseudocode = *idComponents."pseudocode";
   *version    = *idComponents."version";
   uuYcDatasetGetToplevelObjects(*idComponents."directory", *datasetId, *tlObjects, *isCollection);
   *datasetStatus   = "scanned";
   *datasetErrors   = 0;
   *datasetWarnings = 0;
   *datasetComments = 0;
   *objects         = 0;
   *objectErrors    = 0;
   *objectWarnings  = 0;
   *datasetCreateName = "==UNKNOWN==";
   *datasetCreateDate = 0;

   if (*isCollection) {
      *tlCollection = elem(*tlObjects, 0);
      foreach (*row in SELECT META_COLL_OWNER_NAME, META_COLL_CREATE_TIME
                       WHERE COLL_NAME = *tlCollection) {
         *datasetCreateName = *row."META_COLL_OWNER_NAME";
         *datasetCreateDate = *row."META_COLL_CREATE_TIME";
         break;
      };
      foreach (*row in SELECT META_COLL_ATTR_NAME, META_COLL_ATTR_VALUE
                       WHERE COLL_NAME = *tlCollection) {
         if (*row."META_COLL_ATTR_NAME" == "dataset_error") {
            *datasetErrors = *datasetErrors + 1;
         };
         if (*row."META_COLL_ATTR_NAME" == "dataset_warning") {
            *datasetWarnings = *datasetWarnings + 1;
         };
         if (*row."META_COLL_ATTR_NAME" == "comment") {
            *datasetComments = *datasetComments + 1;
         };
         if (*row."META_COLL_ATTR_NAME" == "to_vault_freeze") {
            *datasetStatus = "frozen";
         };
         if (*row."META_COLL_ATTR_NAME" == "to_vault_lock") {
            *datasetStatus = "locked";
         };
      }

   }
   if (!*isCollection) {
      foreach (*dataObject in *tlObjects) {
         *objects = *objects + 1;
         foreach (*row in SELECT META_DATA_ATTR_NAME, META_DATA_ATTR_VALUE
                       WHERE DATA_NAME = *dataObject) {
            if (*row."META_DATA_ATTR_NAME" == "error") {
               *objectErrors = *objectErrors + 1;
            };
            if (*row."META_DATA_ATTR_NAME" == "warning") {
               *objectWarnings = *objectWarnings + 1;
            };
            if (*objects == 1) {
               # dataset info is duplicated across objects, so count only once
               if (*row."META_DATA_ATTR_NAME" == "dataset_error") {
                  *datasetErrors = *objectErrors + 1;
               };
               if (*row."META_DATA_ATTR_NAME" == "dataset_warning") {
                  *datasetWarnings = *datasetWarnings + 1;
               };
               if (*row."META_DATA_ATTR_NAME" == "comment") {
                  *datasetComments = *datasetComments + 1;
               };
            };
            if (*row."META_DATA_ATTR_NAME" == "to_vault_freeze") {
               *datasetStatus = "frozen";
            };
            if (*row."META_DATA_ATTR_NAME" == "to_vault_lock") {
               *datasetStatus = "locked";
            };
          
         }
      }
   }
      
}



#input null
#output ruleExecOut
