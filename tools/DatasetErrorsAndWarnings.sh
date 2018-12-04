#!/bin/sh
irule -F /etc/irods/irods-ruleset-youth-cohort/tools/ExportDatasetErrorsAndWarnings.r "*studyParam='$1'" > DatasetErrorsAndWarnings.csv
