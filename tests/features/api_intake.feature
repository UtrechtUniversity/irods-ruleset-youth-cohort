Feature: Intake API

    Scenario: Find all studies a user is involved with
        Given user "<user>" is authenticated
        And the Yoda intake list studies API is queried
        Then the response status code is "200"
        # And ...

        Examples:
            | user        |
            | datamanager |
            | researcher  |

    Scenario: Get list of all unrecognized and unscanned files
        Given user "<user>" is authenticated
        And the Yoda intake list unrecognized unscanned files API is queried with collection "<collection>"
        Then the response status code is "200"
        # And ...

        Examples:
            | user        | collection                      |
            | datamanager | /tempZone/yoda/home/grp-initial |
            | researcher  | /tempZone/yoda/home/grp-initial |

    Scenario: Get list of all datasets
        Given user "<user>" is authenticated
        And the Yoda intake list datasets API is queried with collection "<collection>"
        Then the response status code is "200"
       # And ...

        Examples:
            | user        | collection                      |
            | datamanager | /tempZone/yoda/home/grp-initial |
            | researcher  | /tempZone/yoda/home/grp-initial |

    Scenario: Scan for and recognize datasets in study intake area
        Given user "<user>" is authenticated
        And the Yoda intake scan for datasets API is queried with collection "<collection>"
        Then the response status code is "200"
        # And ...

        Examples:
            | user        | collection                      |
            | datamanager | /tempZone/yoda/home/grp-initial |
            | researcher  | /tempZone/yoda/home/grp-initial |

#    Scenario: Get number of unrecognized (erroneous) files after scan process
#        Given user "<user>" is authenticated
#        And the Yoda intake API is queried for unrecognized files for study "<study>"
#        Then the response status code is "200"
#        # And ...

#        Examples:
#            | user        | study   |
#            | datamanager | initial |
#            | researcher  | initial |

    Scenario: Lock dataset in study intake area
        Given user "<user>" is authenticated
        And dataset exists
        And the Yoda intake lock API is queried with dataset id and collection "<collection>"
        Then the response status code is "200"
        # And ...

        Examples:
            | user        | collection                      |
            | datamanager | /tempZone/yoda/home/grp-initial |
            | researcher  | /tempZone/yoda/home/grp-initial |

    Scenario: Unlock dataset in study intake area
        Given user "<user>" is authenticated
        And dataset exists
        And the Yoda intake unlock API is queried with dataset id and collection "<collection>"
        Then the response status code is "200"
        # And ...

        Examples:
        | user        | collection                      |
        | datamanager | /tempZone/yoda/home/grp-initial |
        | researcher  | /tempZone/yoda/home/grp-initial |

#    Scenario: Get all details for a dataset (errors/warnings, scanned by who/when, comments, file tree)
#        # OPMERKING: dit moeten ws 4 verschillende calls worden
#        Given user "<user>" is authenticated
#        And dataset id is retrieved from dataset list
#        And the Yoda intake API is queried for all dataset details for dataset id
#        Then the response status code is "200"
#        # And ...

#        Examples:
#            | user        | study   |
#            | datamanager | initial |
#            | researcher  | initial |

#    Scenario: Add comment to a perticular dataset
#        Given user "<user>" is authenticated
#        And dataset id is retrieved from dataset list
#        And the Yoda intake API adds comment "<comment>" and dataset id
#        Then the response status code is "200"
#        # And ...

#        Examples:
#            | user        | study   |
#            | datamanager | initial |
#            | researcher  | initial |

    Scenario: Get vault dataset related counts for reporting for a study
        Given user "<user>" is authenticated
        And the Yoda intake report vault dataset counts per study API is queried with study id "<study_id>"
        Then the response status code is "200"
        # And ...

        Examples:
            | user        | study_id   |
            | datamanager | initial    |

    Scenario: Get aggregated vault dataset info for reporting for a study
        Given user "<user>" is authenticated
        And the Yoda intake report vault aggregated info API is queried with study id "<study_id>"
        Then the response status code is "200"
        # And ...

        Examples:
            | user        | study_id |
            | datamanager | initial  |

#    Scenario: Get vault data required for export for a study
#        Given user "<user>" is authenticated
#        And the Yoda intake API is queried for export data study "<study>"
#        Then the response status code is "200"
#        # And ...

#        Examples:
#            | user        | study   |
#            | datamanager | initial |
