#!/bin/sh
irule -F ExportDatasetErrorsAndWarnings.r "*studyParam='$1'" > DatasetErrorsAndWarnings.csv
