# \file      job_checksums.r
# \brief     Youth Cohort - generate checksum index of Vault
# \author    Ton Smeele
# \copyright Copyright (c) 2016, Utrecht University. All rights reserved.
# \license   GPLv3, see LICENSE

job_checksums {
  *root = "/nluu1a/home/grp-vault-youth";
# NB: logfile location for test purpose, requires new position upon production!
  *logfile = "/nluu1a/home/julia/checksums.txt";
  uuYcGenerateDatasetsIndex(*root, *logfile, *status);
  writeLine("stdout","return status is *status");
}


input null
output ruleExecOut
