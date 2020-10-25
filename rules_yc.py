import itertools

import genquery

from util import *


def chop_checksum(checksum):
    """Chop iRODS checksum in checksum type and checksum string.

    Checksum format is ({type}:){checksum}, if type is missing then it is "md5".

    :param checksum: iRODS checksum string
    """
    checksum_split = checksum.split(":")

    if len(checksum_split) > 1:
        type = checksum_split[0]
        checksum = checksum_split[1]

    return type, checksum


def intake_generate_dataset_checksums(ctx, dataset_path, checksum_file):
    """"Generate data object with all checksums of a dataset.

    :param dataset_path:  Root collection of dataset to be indexed
    :param checksum_file: Data object to write checksums to
    """
    q_root = genquery.row_iterator("COLL_NAME, DATA_NAME, DATA_CHECKSUM, DATA_SIZE",
                                   "COLL_NAME = '{}'".format(dataset_path),
                                   genquery.AS_LIST, ctx)

    q_sub = genquery.row_iterator("COLL_NAME, DATA_NAME, DATA_CHECKSUM, DATA_SIZE",
                                  "COLL_NAME like '{}/%'".format(dataset_path),
                                  genquery.AS_LIST, ctx)

    # Create checksums file.
    checksums = ""
    for row in itertools.chain(q_root, q_sub):
        type, checksum = chop_checksum(row[2])
        checksums += "{} {} {} {}/{}\n".format(type, checksum, row[3], row[0], row[1])

    # Write checksums file.
    data_object.write(ctx, checksum_file, checksums)
# -*- coding: utf-8 -*-
"""Functions for revision management."""

__copyright__ = 'Copyright (c) 2019-2020, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import os
import time
import irods_types

# from util import *
# from util.query import Query

__all__ = ['api_intake_list_studies',
           'api_intake_list_unrecognized_unscanned_files',
           'api_intake_list_datasets',
           'api_intake_scan_for_datasets',
# ???           'api_intake_get_unrecognized_count',  ???
           'api_intake_lock_dataset',
           'api_intake_unlock_dataset',
           'api_intake_dataset_get_details',
           'api_intake_dataset_add_comment',
           'api_intake_report_vault_dataset_counts_per_study',
           'api_intake_report_vault_aggregated_info',
           'api_intake_report_export_study_data']


@api.make()
def api_intake_list_studies(ctx):
    """
    Get list of all studies current user is involved in
    """
    return 'HALLO'


@api.make()
def api_intake_list_unrecognized_unscanned_files(ctx, coll):
    """
    Get list of all unrecognized or unscanned files for given path

    :param coll: collection to find unrecognized and unscanned files in
    """
    return 'HALLO'


@api.make()
def api_intake_list_datasets(ctx, coll):
    """
    Get list of datasets for given path
    :param coll: collection from which to list all datasets 
    """
    return 'HALLO'


@api.make()
def api_intake_scan_for_datasets(ctx, coll):
    """
    The toplevel of a dataset can be determined by attribute 'dataset_toplevel' and can either be a collection or a data_object
    :param coll: collection to scan for datasets
    """
    return 'HALLO'


# @api.make()
# def api_intake_get_unrecognized_count(ctx, study_id): # ???
#    """
#    Deze vervalt volgens mij
#    """


@api.make()
def api_intake_lock_dataset(ctx, path, dataset_id): 
    """
    Lock a dataset to mark as an indication it can be 'frozen' for it to progress to vault
    Lock = datamanager only
    :param coll: collection for which to lock a specific dataset id
    :param dataset_id: id of the dataset to be locked
    """
    return 'HALLO'


@api.make()
def api_intake_unlock_dataset(ctx, path, dataset_id):
    """
    Unlock a dataset to remove the indication so it can be 'frozen' for it to progress to vault
    Unlock = datamanager only
    :param coll: collection for which to lock a specific dataset id
    :param dataset_id: id of the dataset to be unlocked
    """
    return 'HALLO'


@api.make()
def api_intake_dataset_get_details(ctx, dataset_id):
    """
    Get all details for a dataset (errors/warnings, scanned by who/when, comments, file tree)
    1) Errors/warnings
    2) Comments
    3) Tree view of files within dataset.
    :param dataset_id: id of the dataset to get details for
    """
    return 'HALLO'


@api.make()
def api_intake_dataset_add_comment(ctx, dataset_id, comment):
    """
    Add a comment to the comment section of a dataset 
    :param dataset_id: id of the dataset to add a comment to
    """
    return 'HALLO'


# Reporting / export functions
@api.make()
def  api_intake_report_vault_dataset_counts_per_study(ctx, study_id):
    """
    Get the count of datasets wave/experimenttype
    In the vault a dataset is always located in a folder.
    Therefore, looking at the folders only is enough
    :param study_id: id of the study involved
    """
    return 'HALLO'


@api.make()
def  api_intake_report_vault_aggregated_info(ctx, study_id):
    """
    Collects the following information for Raw, Processed datasets. Including a totalisation of this all
    (Raw/processed is kept in VERSION)

    -Total datasets
    -Total files
    -Total file size
    -File size growth in a month
    -Datasets growth in a month
    -Pseudocodes  (distinct)
    :param study_id: id of the study involved
    """
    return 'HALLO'


@api.make()
def api_intake_report_export_study_data(ctx, study_id):
    """
    Find all datasets in the vault for $studyID.
    Include file count and total file size as well as dataset meta data version, experiment type, pseudocode and wave
    :param study_id: id of the study involved
    """
    return 'HALLO'

# -*- coding: utf-8 -*-
"""Functions for creating API rules.

For example usage, see make().
"""

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import inspect
import traceback
from collections import OrderedDict

import jsonutil
import log
import rule
from config import config
from error import *


class Result(object):
    """API result."""

    def __init__(self, data=None, status='ok', info=None, debug_info=None):
        self.status      = status
        self.status_info = info
        self.data        = data
        self.debug_info  = debug_info

    @staticmethod
    def ok(**xs):
        return Result(**xs)

    def as_dict(self):
        if config.environment == 'development':
            # Emit debug information in dev.
            # This may contain stack traces, exception texts, timing info,
            # etc., which should not be sent to users in production.
            return OrderedDict([('status',      self.status),
                                ('status_info', self.status_info),
                                ('data',        self.data),
                                ('debug_info',  self.debug_info)])
        else:
            return OrderedDict([('status',      self.status),
                                ('status_info', self.status_info),
                                ('data',        self.data)])

    def __bool__(self):
        return self.status == 'ok'
    __nonzero__ = __bool__


class Error(Result, UUError):
    """Error with descriptive (user-readable) message.

    Returned/raised by API functions to produce informative error output.
    """
    def __init__(self, name, info, debug_info=None, data=None):
        self.name = name
        self.info = info
        self.debug_info = debug_info

        Result.__init__(self, data, 'error_' + name, info, debug_info)
        UUError.__init__(self, 'error_' + name)

    def __str__(self):
        return '{}: {}'.format(self.name, self.info)


def _api(f):
    """Turn a Python function into a basic API function.

    By itself, this wrapper is not very useful, as the resulting function is
    not callable by rules. See make() below for a method to turn the
    result into one or two rules, with different calling conventions.

    api() creates a function that takes a JSON string as an argument,
    and translates it to function arguments for `f`. The JSON input is
    automatically validated for required/optional arguments, based on f()'s
    signature.
    Ideally we would also do basic type checking, but this is not possible in Python2.

    f()'s returned value may be of any JSON-encodable type, and will be stored
    in the 'data' field of the returned JSON. If f() returns or raises an
    error, the 'status' and 'status_info' fields are populated (non-null)
    instead.

    In development environments, the result may contain a 'debug_info' property
    with additional information on errors, or timing information.
    """
    # Determine required and optional argument names from the function signature.
    a_pos, a_var, a_kw, a_defaults = inspect.getargspec(f)
    a_pos = a_pos[1:]  # ignore callback/context param.

    required = set(a_pos if a_defaults is None else a_pos[:-len(a_defaults)])
    optional = set([] if a_defaults is None else a_pos[-len(a_defaults):])

    # If the function accepts **kwargs, we do not forbid extra arguments.
    allow_extra = a_kw is not None

    def wrapper(ctx, inp):
        """A function that receives a JSON string and calls a wrapped function with unpacked arguments."""
        # Result shorthands.
        def error_internal(debug_info=None):
            return Error('internal', 'An internal error occurred', debug_info=debug_info)

        def bad_request(debug_info=None):
            return Error('badrequest', 'An internal error occurred', debug_info=debug_info)

        # Validate input string: is it a valid JSON object?
        try:
            data = jsonutil.parse(inp)
            if type(data) is not OrderedDict:
                raise jsonutil.ParseError('Argument is not a JSON object')
        except jsonutil.ParseError as e:
            log._write(ctx, 'Error: API rule <{}> called with invalid JSON argument'
                            .format(f.__name__))
            return bad_request('JSON parse error: {}'.format(e)).as_dict()

        # Check that required arguments are present.
        for param in required:
            if param not in data:
                log._write(ctx, 'Error: API rule <{}> called with missing <{}> argument'
                                .format(f.__name__, param))
                return bad_request('Missing argument: {} (required: [{}]  optional: [{}])'
                                   .format(param, ', '.join(required), ', '.join(optional))).as_dict()

        # Forbid arguments that are not in the function signature.
        if not allow_extra:
            for param in data:
                if param not in required | optional:
                    log._write(ctx, 'Error: API rule <{}> called with unrecognized <{}> argument'
                                    .format(f.__name__, param))
                    return bad_request('Unrecognized argument: {} (required: [{}]  optional: [{}])'
                                       .format(param, ', '.join(required), ', '.join(optional))).as_dict()

        # Try to run the function with the supplied arguments,
        # catching any error it throws.
        try:
            # Time the request.
            import time
            t = time.time()
            result = f(ctx, **data)
            t = time.time() - t

            log._debug(ctx, '%4dms %s' % (int(t * 1000), f.__name__))

            if type(result) is Error:
                raise result  # Allow api.Errors to be either raised or returned.

            elif not isinstance(result, Result):
                # No error / explicit status info implies 'OK' status.
                result = Result(result, debug_info={'time': t})

            return result.as_dict()
        except Error as e:
            # A proper caught error with name and message.
            if e.debug_info is None:
                log._write(ctx, 'Error: API rule <{}> failed with error <{}>'.format(f.__name__, e))
            else:
                log._write(ctx, 'Error: API rule <{}> failed with error <{}> (debug info follows below this line)\n{}'.format(f.__name__, e, e.debug_info))
            return e.as_dict()
        except Exception as e:
            # An uncaught error. Log a trace to aid debugging.
            log._write(ctx, 'Error: API rule <{}> failed with uncaught error (trace follows below this line)\n{}'
                            .format(f.__name__, traceback.format_exc()))
            return error_internal(traceback.format_exc()).as_dict()

    return wrapper


def make():
    """Create API functions callable as iRODS rules.

    This translate between a Python calling convention and the iRODS rule
    calling convention.

    An iRODS rule is created that receives a JSON string and prints the
    result of f, JSON-encoded to stdout. If an error occurs, the output JSON
    will contain "error" and "error_message" items.

    Synopsis:

        __all__ = ['api_ping']

        @api.make()
        def api_ping(ctx, foo):
            if foo != 42:
                return api.Error('not_allowed', 'Ping is not allowed')
            log.write(ctx, 'ping received')
            return foo

        # this returns {"status": "ok", "status_info": null, "data": 42}
        # when called as api_ping {"foo": 42}
    """
    def deco(f):
        # The "base" API function, that does handling of arguments and errors.
        base = _api(f)

        # The JSON-in, JSON-out rule.
        return rule.make(inputs=[0], outputs=[],
                         transform=jsonutil.dump, handler=rule.Output.STDOUT)(base)

    return deco
# -*- coding: utf-8 -*-
"""Utility / convenience functions for dealing with AVUs."""

__copyright__ = 'Copyright (c) 2019-2020, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import itertools
from collections import namedtuple

import irods_types

import msi
import pathutil
from query import Query

Avu = namedtuple('Avu', list('avu'))
Avu.attr  = Avu.a
Avu.value = Avu.v
Avu.unit  = Avu.u


def of_coll(ctx, coll):
    """Get (a,v,u) triplets for a given collection."""
    return itertools.imap(lambda x: Avu(*x),
                          Query(ctx, "META_COLL_ATTR_NAME, META_COLL_ATTR_VALUE, META_COLL_ATTR_UNITS",
                                     "COLL_NAME = '{}'".format(coll)))


def of_data(ctx, path):
    """Get (a,v,u) triplets for a given data object."""
    return itertools.imap(lambda x: Avu(*x),
                          Query(ctx, "META_DATA_ATTR_NAME, META_DATA_ATTR_VALUE, META_DATA_ATTR_UNITS",
                                     "COLL_NAME = '{}', DATA_NAME = '{}'".format(*pathutil.chop(path))))


def of_group(ctx, group):
    """Get (a,v,u) triplets for a given group."""
    return itertools.imap(lambda x: Avu(*x),
                          Query(ctx, "META_USER_ATTR_NAME, META_USER_ATTR_VALUE, META_USER_ATTR_UNITS",
                                     "USER_NAME = '{}' AND USER_TYPE = 'rodsgroup'".format(group)))


def set_on_coll(ctx, coll, a, v):
    """Set key/value metadata on a collection."""
    x = msi.string_2_key_val_pair(ctx, '{}={}'.format(a, v), irods_types.BytesBuf())
    msi.set_key_value_pairs_to_obj(ctx, x['arguments'][1], coll, '-C')


def set_on_resource(ctx, resource, a, v):
    """Set key/value metadata on a resource."""
    x = msi.string_2_key_val_pair(ctx, '{}={}'.format(a, v), irods_types.BytesBuf())
    msi.set_key_value_pairs_to_obj(ctx, x['arguments'][1], resource, '-R')


def associate_to_coll(ctx, coll, a, v):
    """Associate key/value metadata on a collection."""
    x = msi.string_2_key_val_pair(ctx, '{}={}'.format(a, v), irods_types.BytesBuf())
    msi.associate_key_value_pairs_to_obj(ctx, x['arguments'][1], coll, '-C')


def associate_to_group(ctx, group, a, v):
    """Associate key/value metadata on a group."""
    x = msi.string_2_key_val_pair(ctx, '{}={}'.format(a, v), irods_types.BytesBuf())
    msi.associate_key_value_pairs_to_obj(ctx, x['arguments'][1], group, '-u')


def associate_to_resource(ctx, resource, a, v):
    """Associate key/value metadata on a group."""
    x = msi.string_2_key_val_pair(ctx, '{}={}'.format(a, v), irods_types.BytesBuf())
    msi.associate_key_value_pairs_to_obj(ctx, x['arguments'][1], resource, '-R')


def rm_from_coll(ctx, coll, a, v):
    """Remove key/value metadata from a collection."""
    x = msi.string_2_key_val_pair(ctx, '{}={}'.format(a, v), irods_types.BytesBuf())
    msi.remove_key_value_pairs_from_obj(ctx, x['arguments'][1], coll, '-C')


def rm_from_data(ctx, coll, a, v):
    """Remove key/value metadata from a data object."""
    x = msi.string_2_key_val_pair(ctx, '{}={}'.format(a, v), irods_types.BytesBuf())
    msi.remove_key_value_pairs_from_obj(ctx, x['arguments'][1], coll, '-d')


def rm_from_group(ctx, group, a, v):
    """Remove key/value metadata from a group."""
    x = msi.string_2_key_val_pair(ctx, '{}={}'.format(a, v), irods_types.BytesBuf())
    msi.remove_key_value_pairs_from_obj(ctx, x['arguments'][1], group, '-u')


def rmw_from_coll(ctx, obj, a, v, u=''):
    """Remove AVU from collection with wildcards."""
    msi.rmw_avu(ctx, '-C', obj, a, v, u)


def rmw_from_data(ctx, obj, a, v, u=''):
    """Remove AVU from data object with wildcards."""
    msi.rmw_avu(ctx, '-d', obj, a, v, u)


def rmw_from_group(ctx, group, a, v, u=''):
    """Remove AVU from group with wildcards."""
    msi.rmw_avu(ctx, '-u', group, a, v, u)
# -*- coding: utf-8 -*-
"""Utility / convenience functions for dealing with collections."""

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import itertools
import sys
if sys.version_info > (2, 7):
    from functools import reduce

import genquery
import irods_types

import msi
from query import Query


def exists(callback, path):
    """Check if a collection with the given path exists."""
    return len(list(genquery.row_iterator(
               "COLL_ID", "COLL_NAME = '{}'".format(path),
               genquery.AS_LIST, callback))) > 0


def owner(callback, path):
    """Find the owner of a collection. Returns (name, zone) or None."""
    owners = list(genquery.row_iterator(
                  "COLL_OWNER_NAME, COLL_OWNER_ZONE",
                  "COLL_NAME = '{}'".format(path),
                  genquery.AS_LIST, callback))
    return tuple(owners[0]) if len(owners) > 0 else None


def empty(callback, path):
    """Check if a collection contains any data objects."""
    return (len(list(genquery.row_iterator(
                     "DATA_ID",
                     "COLL_NAME = '{}'".format(path),
                     genquery.AS_LIST, callback))) == 0
            and len(list(genquery.row_iterator(
                    "DATA_ID",
                    "COLL_NAME like '{}/%'".format(path),
                    genquery.AS_LIST, callback))) == 0)


def size(callback, path):
    """Get a collection's size in bytes."""
    def func(x, row):
        return x + int(row[1])

    return reduce(func,
                  itertools.chain(genquery.row_iterator("DATA_ID, DATA_SIZE",
                                                        "COLL_NAME like '{}'".format(path),
                                                        genquery.AS_LIST, callback),
                                  genquery.row_iterator("DATA_ID, DATA_SIZE",
                                                        "COLL_NAME like '{}/%'".format(path),
                                                        genquery.AS_LIST, callback)), 0)


def data_count(callback, path, recursive=True):
    """Get a collection's data count.

    :param path: A collection path
    :param recursive: Measure subcollections as well
    :return: A number of data objects.
    """
    # Generators can't be fed to len(), so here we are...
    return sum(1 for _ in data_objects(callback, path, recursive=recursive))


def collection_count(callback, path):
    """Get a collection's collection count (the amount of collections within a collection)."""
    return sum(1 for _ in genquery.row_iterator(
               "COLL_ID",
               "COLL_NAME like '{}/%'".format(path),
               genquery.AS_LIST, callback))


def data_objects(callback, path, recursive=False):
    """Get a list of all data objects in a collection.

    Note: the returned value is a generator / lazy list, so that large
          collections can be handled without keeping everything in memory.
          use list(...) on the result to get an actual list if necessary.

    The returned paths are absolute paths (e.g. ['/tempZone/home/x/y.txt']).
    """
    # coll+data name -> path
    def to_absolute(row):
        return '{}/{}'.format(*row)

    q_root = genquery.row_iterator("COLL_NAME, DATA_NAME",
                                   "COLL_NAME = '{}'".format(path),
                                   genquery.AS_LIST, callback)

    if not recursive:
        return itertools.imap(to_absolute, q_root)

    # Recursive? Return a generator combining both queries.
    q_sub = genquery.row_iterator("COLL_NAME, DATA_NAME",
                                  "COLL_NAME like '{}/%'".format(path),
                                  genquery.AS_LIST, callback)

    return itertools.imap(to_absolute, itertools.chain(q_root, q_sub))


def create(ctx, path):
    """Create new collection.

    :param path: Path including new collection

    This may raise a error.UUError if the file does not exist, or when the user
    does not have write permission.
    """
    msi.coll_create(ctx,
                    path,
                    '',
                    irods_types.BytesBuf())


def remove(ctx, path):
    """Delete a collection.

    :param path: Path of collection to be deleted

    This may raise a error.UUError if the file does not exist, or when the user
    does not have write permission.
    """
    msi.rm_coll(ctx,
                path,
                '',
                irods_types.BytesBuf())


def rename(ctx, path_org, path_target):
    """Rename collection from path_org to path_target.

    :param path_org: Collection original path
    :param path_target: Collection new path

    This may raise a error.UUError if the file does not exist, or when the user
    does not have write permission.
    """
    msi.data_obj_rename(ctx,
                        path_org,
                        path_target,
                        '1',
                        irods_types.BytesBuf())


def name_from_id(ctx, coll_id):
    """Get collection name from collection id.

    :param coll_id Collection id
    """
    return Query(ctx, "COLL_NAME", "COLL_ID = '{}'".format(coll_id)).first()
# -*- coding: utf-8 -*-
"""Yoda ruleset configuration."""

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'


# Config class {{{

class Config(object):
    """Stores configuration info, accessible through attributes (config.foo).

    Valid options are determined at __init__ time.
    Setting non-existent options raises an AttributeError.
    Accessing non-existent options raises an AttributeError as well.

    Example:

      config = Config(foo = 'stuff')
      config.foo = 'other stuff'

      x = config.foo
      y = config.bar  # AttributeError
    """

    def __init__(self, **kwargs):
        """kwargs must contain all valid options and their default values."""
        self._items  = kwargs
        self._frozen = False

    def freeze(self):
        """Prevent further config changes via setattr."""
        self._frozen = True

    def __setattr__(self, k, v):
        if k.startswith('_'):
            return super(Config, self).__setattr__(k, v)
        if self._frozen:
            print('Ruleset configuration error: No config changes possible to \'{}\''.format(k))
            return
        if k not in self._items:
            print('Ruleset configuration error: No such config option: \'{}\''.format(k))
            return
        # Set as config option.
        self._items[k] = v

    def __getattr__(self, k):
        if k.startswith('_'):
            return super(Config, self).__getattr__(k)
        try:
            return self._items[k]
        except KeyError as e:
            # py3: should become 'raise ... from e'
            raise AttributeError('Config item <{}> does not exist'.format(k))

    # Never dump config values, they may contain sensitive info.
    def __str__(self):
        return 'Config()'

    def __repr__(self):
        return 'Config()'

    # def __repr__(self):
    #     return 'Config(\n{})'.format(''.join('  {} = {},\n'.format(k,
    #                 ('\n  '.join(repr(v).splitlines()) if isinstance(v, Config) else repr(v)))
    #                     for k, v in self._items.items()))

# }}}


# Default config {{{

# Note: Must name all valid config items.
config = Config(environment=None,
                resource_primary=[],
                resource_replica=None,
                notifications_enabled=False,
                notifications_sender_email=None,
                notifications_sender_name=None,
                notifications_reply_to=None,
                smtp_server=None,
                smtp_username=None,
                smtp_password=None,
                datacite_url=None,
                datacite_username=None,
                datacite_password=None,
                eus_api_fqdn=None,
                eus_api_port=None,
                eus_api_secret=None,
                epic_pid_enabled=False,
                epic_url=None,
                epic_handle_prefix=None,
                epic_key=None,
                epic_certificate=None)

# }}}

# Optionally include a site-local config file to override the above.
# (note: this is done only once per agent)
try:
    import os
    import re
    # Look for a config file in the root dir of this ruleset.
    cfgpath = os.path.dirname(__file__) + '/../rules_uu.cfg'
    with open(cfgpath) as f:
        for i, line in enumerate(f):
            line = line.strip()
            # Skip comments, whitespace lines.
            if line.startswith('#') or len(line) == 0:
                continue
            # Interpret {k = 'v'} and {k =}
            m = re.match(r"""^([\w_]+)\s*=\s*(?:'(.*)')?$""", line)
            if not m:
                raise Exception('Configuration syntax error at {} line {}', cfgpath, i + 1)

            # List-type values are separated by whitespace.
            try:
                typ = type(getattr(config, m.group(1)))
            except AttributeError as e:
                typ = str

            if issubclass(typ, list):
                setattr(config, m.group(1), m.group(2).split())
            elif issubclass(typ, bool):
                setattr(config, m.group(1), {'true': True, 'false': False}[m.group(2)])
            elif issubclass(typ, int):
                setattr(config, m.group(1), int(m.group(2)))
            else:
                setattr(config, *m.groups())

except IOError:
    # Ignore, config file is optional.
    pass

# Try to prevent (accidental) config changes.
config.freeze()
# -*- coding: utf-8 -*-
"""Constants that apply to all Yoda environments."""

__copyright__ = 'Copyright (c) 2016-2020, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

from enum import Enum

# TODO: Naming convention (no capitals, no UU/II prefix)
# TODO: dicts => enum.Enum
# TODO: all attrnames => one enum.Enum

IIGROUPPREFIX = "research-"
IIGRPPREFIX = "grp-"
IIVAULTPREFIX = "vault-"

UUORGMETADATAPREFIX = 'org_'
UUSYSTEMCOLLECTION = '/yoda'

UUREVISIONCOLLECTION = UUSYSTEMCOLLECTION + '/revisions'
"""iRODS path where all revisions will be stored."""

UUDEFAULTRESOURCETIER = 'Standard'
"""Default name for a tier when none defined yet."""

UURESOURCETIERATTRNAME = UUORGMETADATAPREFIX + 'storage_tier'
"""Metadata attribute for storage tier name."""

UUMETADATASTORAGEMONTH = UUORGMETADATAPREFIX + 'storage_data_month'
"""Metadata for calculated storage month."""

UUPROVENANCELOG = UUORGMETADATAPREFIX + 'action_log'
"""Provenance log item."""

IILICENSECOLLECTION = UUSYSTEMCOLLECTION + '/licenses'
"""iRODS path where all licenses will be stored."""

IIPUBLICATIONCOLLECTION = UUSYSTEMCOLLECTION + '/publication'
"""iRODS path where publications will be stored. """

IITERMSCOLLECTION = UUSYSTEMCOLLECTION + "/terms"
"""iRODS path where the publication terms will be stored."""

IIJSONMETADATA = 'yoda-metadata.json'
"""Name of metadata JSON file."""

IIMETADATAXMLNAME = 'yoda-metadata.xml'
"""Name of metadata XML file."""

IIRESEARCHXSDNAME = 'research.xsd'
"""Name of the research XSD."""

IIVAULTXSDNAME = 'vault.xsd'
"""Name of the vault XSD."""

IIDATA_MAX_SLURP_SIZE = 4 * 1024 * 1024  # 4 MiB
"""The maximum file size that can be read into a string in memory, to prevent
   DOSing / out of control memory consumption."""

UUUSERMETADATAPREFIX = 'usr_'
"""Prefix of user metadata (applied via legacy XML metadata file changes)."""

UUUSERMETADATAROOT = 'usr'
"""JSONAVU JSON root / namespace of user metadata (applied via JSON metadata file changes)."""

UUORGMETADATAPREFIX = 'org_'
"""Prefix for organisational metadata."""

IILOCKATTRNAME        = UUORGMETADATAPREFIX + 'lock'
IISTATUSATTRNAME      = UUORGMETADATAPREFIX + 'status'
IIVAULTSTATUSATTRNAME = UUORGMETADATAPREFIX + 'vault_status'
IICOPYPARAMSNAME      = UUORGMETADATAPREFIX + 'copy_to_vault_params'

CRONJOB_STATE = {
    'PENDING':       'CRONJOB_PENDING',
    'PROCESSING':    'CRONJOB_PROCESSING',
    'RETRY':         'CRONJOB_RETRY',
    'UNRECOVERABLE': 'CRONJOB_UNRECOVERABLE',
    'OK':            'CRONJOB_OK',
}
"""Cronjob states."""


class vault_package_state(Enum):
    """Vault package states."""

    # Values are as they appear in AVU values.
    EMPTY                     = ''  # (absence of status attribute)
    INCOMPLETE                = 'INCOMPLETE'
    UNPUBLISHED               = 'UNPUBLISHED'
    SUBMITTED_FOR_PUBLICATION = 'SUBMITTED_FOR_PUBLICATION'
    APPROVED_FOR_PUBLICATION  = 'APPROVED_FOR_PUBLICATION'
    PUBLISHED                 = 'PUBLISHED'
    PENDING_DEPUBLICATION     = 'PENDING_DEPUBLICATION'
    DEPUBLISHED               = 'DEPUBLISHED'
    PENDING_REPUBLICATION     = 'PENDING_REPUBLICATION'

    def __str__(self):
        return self.name


# List of valid datapackage transitions (src, dst).
datapackage_transitions = [(vault_package_state(x),
                            vault_package_state(y))
                           for x, y in [('',                          'INCOMPLETE'),
                                        ('',                          'UNPUBLISHED'),
                                        ('INCOMPLETE',                'UNPUBLISHED'),
                                        ('UNPUBLISHED',               'SUBMITTED_FOR_PUBLICATION'),
                                        ('SUBMITTED_FOR_PUBLICATION', 'APPROVED_FOR_PUBLICATION'),
                                        ('SUBMITTED_FOR_PUBLICATION', 'UNPUBLISHED'),
                                        ('APPROVED_FOR_PUBLICATION',  'PUBLISHED'),
                                        ('PUBLISHED',                 'PENDING_DEPUBLICATION'),
                                        ('PENDING_DEPUBLICATION',     'DEPUBLISHED'),
                                        ('DEPUBLISHED',               'PENDING_REPUBLICATION'),
                                        ('PENDING_REPUBLICATION',     'PUBLISHED')]]


class research_package_state(Enum):
    """Research folder states."""

    # Values are as they appear in AVU values.
    FOLDER    = ''  # (absence of status attribute)
    LOCKED    = 'LOCKED'
    SUBMITTED = 'SUBMITTED'
    ACCEPTED  = 'ACCEPTED'
    REJECTED  = 'REJECTED'
    SECURED   = 'SECURED'

    def __str__(self):
        return self.name


# List of valid folder transitions (src, dst).
folder_transitions = [(research_package_state(x),
                       research_package_state(y))
                      for x, y in [('',          'LOCKED'),
                                   ('',          'SUBMITTED'),
                                   ('LOCKED',    ''),
                                   ('LOCKED',    'SUBMITTED'),
                                   ('SUBMITTED', ''),
                                   ('SUBMITTED', 'ACCEPTED'),
                                   ('SUBMITTED', 'REJECTED'),
                                   ('REJECTED',  'LOCKED'),
                                   ('REJECTED',  ''),
                                   ('REJECTED',  'SUBMITTED'),
                                   ('ACCEPTED',  'SECURED'),
                                   ('SECURED',   'LOCKED'),
                                   ('SECURED',   ''),
                                   ('SECURED',   'SUBMITTED')]]
# -*- coding: utf-8 -*-
"""Utility / convenience functions for data object IO."""

__copyright__ = 'Copyright (c) 2019-2020, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import genquery
import irods_types

import constants
import error
import msi
import pathutil
from query import Query


def exists(callback, path):
    """Check if a data object with the given path exists."""
    return len(list(genquery.row_iterator(
               "DATA_ID",
               "COLL_NAME = '%s' AND DATA_NAME = '%s'" % pathutil.chop(path),
               genquery.AS_LIST, callback))) > 0


def owner(callback, path):
    """Find the owner of a data object. Returns (name, zone) or None."""
    owners = list(genquery.row_iterator(
                  "DATA_OWNER_NAME, DATA_OWNER_ZONE",
                  "COLL_NAME = '%s' AND DATA_NAME = '%s'" % pathutil.chop(path),
                  genquery.AS_LIST, callback))
    return tuple(owners[0]) if len(owners) > 0 else None


def size(callback, path):
    """Get a data object's size in bytes."""
    iter = genquery.row_iterator(
        "DATA_SIZE, order_desc(DATA_MODIFY_TIME)",
        "COLL_NAME = '%s' AND DATA_NAME = '%s'" % pathutil.chop(path),
        genquery.AS_LIST, callback
    )

    for row in iter:
        return int(row[0])


def write(callback, path, data):
    """
    Write a string to an iRODS data object.

    This will overwrite the data object if it exists.
    """
    ret = msi.data_obj_create(callback, path, 'forceFlag=', 0)
    handle = ret['arguments'][2]

    msi.data_obj_write(callback, handle, data, 0)
    msi.data_obj_close(callback, handle, 0)


def read(callback, path, max_size=constants.IIDATA_MAX_SLURP_SIZE):
    """Read an entire iRODS data object into a string."""
    sz = size(callback, path)
    if sz is None:
        raise error.UUFileNotExistError('data_object.read: object does not exist ({})'
                                        .format(path))

    if sz > max_size:
        raise error.UUFileSizeError('data_object.read: file size limit exceeded ({} > {})'
                                    .format(sz, max_size))

    if sz == 0:
        # Don't bother reading an empty file.
        return ''

    ret = msi.data_obj_open(callback, 'objPath=' + path, 0)
    handle = ret['arguments'][1]

    ret = msi.data_obj_read(callback,
                            handle,
                            sz,
                            irods_types.BytesBuf())

    buf = ret['arguments'][2]

    msi.data_obj_close(callback, handle, 0)

    return ''.join(buf.buf[:buf.len])


def copy(ctx, path_org, path_copy, force=True):
    """Copy a data object.

    :param path_org: Data object original path
    :param path_copy: Data object copy path
    :param force: applies "forceFlag"

    This may raise a error.UUError if the file does not exist, or when the user
    does not have write permission.
    """
    msi.data_obj_copy(ctx,
                      path_org,
                      path_copy,
                      'verifyChksum={}'.format('++++forceFlag=' if force else ''),
                      irods_types.BytesBuf())


def remove(ctx, path, force=True):
    """Delete a data object.

    :param path: data object path
    :param force: applies "forceFlag"

    This may raise a error.UUError if the file does not exist, or when the user
    does not have write permission.
    """
    msi.data_obj_unlink(ctx,
                        'objPath={}{}'.format(path, '++++forceFlag=' if force else ''),
                        irods_types.BytesBuf())


def rename(ctx, path_org, path_target):
    """Rename data object from path_org to path_target.

    :param path_org: Data object original path
    :param path_target: Data object new path

    This may raise a error.UUError if the file does not exist, or when the user
    does not have write permission.
    """
    msi.data_obj_rename(ctx,
                        path_org,
                        path_target,
                        '0',
                        irods_types.BytesBuf())


def name_from_id(ctx, data_id):
    """Get data object name from data object id.

    :param data_id Data object id
    """
    x = Query(ctx, "COLL_NAME, DATA_NAME", "DATA_ID = '{}'".format(data_id)).first()
    if x is not None:
        return '/'.join(x)
# -*- coding: utf-8 -*-
"""Common UU Error/Exception types."""

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'


class UUError(Exception):
    """Generic Python rule error."""


class UUFileSizeError(UUError):
    """File size limit exceeded."""


class UUFileNotExistError(UUError):
    """File does not exist."""
# -*- coding: utf-8 -*-
"""Temporary genquery compatibility module.

https://github.com/irods/irods_rule_engine_plugin_python/pull/34
https://github.com/irods/irods_rule_engine_plugin_python/issues/35

Improves performance for queries using the row_iterator interface.
"""
import query

AS_LIST = query.AS_LIST
AS_DICT = query.AS_DICT


def row_iterator(columns,
                 conditions,
                 row_return,
                 callback):
    return query.Query(callback, columns, conditions, output=row_return)
# -*- coding: utf-8 -*-
"""Utility / convenience functions for querying user info."""

__copyright__ = 'Copyright (c) 2019-2020, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import user
from query import Query


def exists(ctx, grp):
    """
    Check if a group with the given name exists.

    :param grp: Group name
    """
    return Query(ctx, "USER_GROUP_NAME", "USER_GROUP_NAME = '{}' AND USER_TYPE = 'rodsgroup'"
                      .format(grp)).first() is not None


def members(ctx, grp):
    """
    Get members of a given group.

    :param grp: Group name
    """
    return Query(ctx, "USER_NAME, USER_ZONE",
                 "USER_GROUP_NAME = '{}' AND USER_TYPE != 'rodsgroup'"
                 .format(grp))


def is_member(ctx, grp, usr=None):
    """
    Check if a group has a certain member.

    :param grp: Group name
    """
    return user.is_member_of(ctx, grp, usr)


def get_category(ctx, grp):
    """
    Get the category of a group.

    :param grp: Group name
    """
    ret = ctx.uuGroupGetCategory(grp, '', '')
    x = ret['arguments'][1]
    return None if x == '' else x
# -*- coding: utf-8 -*-
"""Generic UU ruleset utility functions and types.

This subpackage does not export any callable rules by itself.
Rather, it provides utility Python functions to other rules.
"""

__copyright__ = 'Copyright (c) 2019-2020, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

# Make sure that importing * from this package gives (qualified) access to all
# contained modules.
# i.e. importing code can use these modules like: collection.exists(callback, 'bla')

import log
import error
import jsonutil
import rule
import api
import msi
import policy
import pathutil
import constants
import collection
import data_object
import user
import group
import avu
import misc
import query
import genquery  # temporary
import config

# Config items can be accessed directly as 'config.foo' by any module
# that imports * from util.
from config import config

if config.environment == 'development':
    import irods_type_info
    ping = api_ping = api.make()(lambda ctx, x=42: x)
# -*- coding: utf-8 -*-
"""Allows converting certain irods types to string representation for debugging purposes.

Importing this module (anywhere) adds stringifyability to some frequently-used
irods_types types.
"""

import irods_types


def pyify(x):
    """Turn irods type into equivalent python type, if possible."""
    return x._pyify() if '_pyify' in dir(x) else str(x)


irods_types.c_string._pyify   = lambda self: str(self)
irods_types.c_string.__repr__ = lambda self: repr(pyify(self))

irods_types.char_array._pyify   = lambda self: str(self)
irods_types.char_array.__repr__ = lambda self: repr(pyify(self))

irods_types.int_array._pyify   = lambda self: list(self)
irods_types.int_array.__repr__ = lambda self: repr(pyify(self))

irods_types.c_string_array._pyify   = lambda self: map(pyify, list(self))
irods_types.c_string_array.__repr__ = lambda self: repr(pyify(self))

irods_types.InxIvalPair._pyify   = lambda self: dict(zip(pyify(self.inx), pyify(self.value)))
irods_types.InxIvalPair.__repr__ = lambda self: repr(pyify(self))

irods_types.KeyValPair._pyify   = lambda self: (pyify(self.key), pyify(self.value))
irods_types.KeyValPair.__repr__ = lambda self: repr(pyify(self))

irods_types.InxValPair._pyify   = lambda self: zip(pyify(self.inx), pyify(self.value))
irods_types.InxValPair.__repr__ = lambda self: repr(pyify(self))

irods_types.GenQueryInp.__repr__ = \
    lambda self: 'GenQuery(select {} where {})'.format(
        ', '.join(map(col_name, pyify(self.selectInp))),
        ' and '.join(map(lambda kv: '{} {}'.format(col_name(kv[0]), kv[1]),
                     pyify(self.sqlCondInp))))

# (add more as needed)


def col_name(i):
    return filter(lambda kv: kv[1] == i, cols)[0][0]


cols =\
    [('ZONE_ID', 101),
     ('ZONE_NAME', 102),
     ('ZONE_TYPE', 103),
     ('ZONE_CONNECTION', 104),
     ('ZONE_COMMENT', 105),
     ('ZONE_CREATE_TIME', 106),
     ('ZONE_MODIFY_TIME', 107),
     ('USER_ID', 201),
     ('USER_NAME', 202),
     ('USER_TYPE', 203),
     ('USER_ZONE', 204),
     ('USER_INFO', 206),
     ('USER_COMMENT', 207),
     ('USER_CREATE_TIME', 208),
     ('USER_MODIFY_TIME', 209),
     ('USER_DN_INVALID', 205),
     ('R_RESC_ID', 301),
     ('R_RESC_NAME', 302),
     ('R_ZONE_NAME', 303),
     ('R_TYPE_NAME', 304),
     ('R_CLASS_NAME', 305),
     ('R_LOC', 306),
     ('R_VAULT_PATH', 307),
     ('R_FREE_SPACE', 308),
     ('R_RESC_INFO', 309),
     ('R_RESC_COMMENT', 310),
     ('R_CREATE_TIME', 311),
     ('R_MODIFY_TIME', 312),
     ('R_RESC_STATUS', 313),
     ('R_FREE_SPACE_TIME', 314),
     ('R_RESC_CHILDREN', 315),
     ('R_RESC_CONTEXT', 316),
     ('R_RESC_PARENT', 317),
     ('R_RESC_PARENT_CONTEXT', 318),
     ('D_DATA_ID', 401),
     ('D_COLL_ID', 402),
     ('DATA_NAME', 403),
     ('DATA_REPL_NUM', 404),
     ('DATA_VERSION', 405),
     ('DATA_TYPE_NAME', 406),
     ('DATA_SIZE', 407),
     ('D_RESC_NAME', 409),
     ('D_DATA_PATH', 410),
     ('D_OWNER_NAME', 411),
     ('D_OWNER_ZONE', 412),
     ('D_REPL_STATUS', 413),
     ('D_DATA_STATUS', 414),
     ('D_DATA_CHECKSUM', 415),
     ('D_EXPIRY', 416),
     ('D_MAP_ID', 417),
     ('D_COMMENTS', 418),
     ('D_CREATE_TIME', 419),
     ('D_MODIFY_TIME', 420),
     ('DATA_MODE', 421),
     ('D_RESC_HIER', 422),
     ('D_RESC_ID', 423),
     ('COLL_ID', 500),
     ('COLL_NAME', 501),
     ('COLL_PARENT_NAME', 502),
     ('COLL_OWNER_NAME', 503),
     ('COLL_OWNER_ZONE', 504),
     ('COLL_MAP_ID', 505),
     ('COLL_INHERITANCE', 506),
     ('COLL_COMMENTS', 507),
     ('COLL_CREATE_TIME', 508),
     ('COLL_MODIFY_TIME', 509),
     ('COLL_TYPE', 510),
     ('COLL_INFO1', 511),
     ('COLL_INFO2', 512),
     ('META_DATA_ATTR_NAME', 600),
     ('META_DATA_ATTR_VALUE', 601),
     ('META_DATA_ATTR_UNITS', 602),
     ('META_DATA_ATTR_ID', 603),
     ('META_DATA_CREATE_TIME', 604),
     ('META_DATA_MODIFY_TIME', 605),
     ('META_COLL_ATTR_NAME', 610),
     ('META_COLL_ATTR_VALUE', 611),
     ('META_COLL_ATTR_UNITS', 612),
     ('META_COLL_ATTR_ID', 613),
     ('META_COLL_CREATE_TIME', 614),
     ('META_COLL_MODIFY_TIME', 615),
     ('META_NAMESPACE_COLL', 620),
     ('META_NAMESPACE_DATA', 621),
     ('META_NAMESPACE_RESC', 622),
     ('META_NAMESPACE_USER', 623),
     ('META_NAMESPACE_RESC_GROUP', 624),
     ('META_NAMESPACE_RULE', 625),
     ('META_NAMESPACE_MSRVC', 626),
     ('META_NAMESPACE_MET2', 627),
     ('META_RESC_ATTR_NAME', 630),
     ('META_RESC_ATTR_VALUE', 631),
     ('META_RESC_ATTR_UNITS', 632),
     ('META_RESC_ATTR_ID', 633),
     ('META_RESC_CREATE_TIME', 634),
     ('META_RESC_MODIFY_TIME', 635),
     ('META_USER_ATTR_NAME', 640),
     ('META_USER_ATTR_VALUE', 641),
     ('META_USER_ATTR_UNITS', 642),
     ('META_USER_ATTR_ID', 643),
     ('META_USER_CREATE_TIME', 644),
     ('META_USER_MODIFY_TIME', 645),
     ('META_RESC_GROUP_ATTR_NAME', 650),
     ('META_RESC_GROUP_ATTR_VALUE', 651),
     ('META_RESC_GROUP_ATTR_UNITS', 652),
     ('META_RESC_GROUP_ATTR_ID', 653),
     ('META_RESC_GROUP_CREATE_TIME', 654),
     ('META_RESC_GROUP_MODIFY_TIME', 655),
     ('META_RULE_ATTR_NAME', 660),
     ('META_RULE_ATTR_VALUE', 661),
     ('META_RULE_ATTR_UNITS', 662),
     ('META_RULE_ATTR_ID', 663),
     ('META_RULE_CREATE_TIME', 664),
     ('META_RULE_MODIFY_TIME', 665),
     ('META_MSRVC_ATTR_NAME', 670),
     ('META_MSRVC_ATTR_VALUE', 671),
     ('META_MSRVC_ATTR_UNITS', 672),
     ('META_MSRVC_ATTR_ID', 673),
     ('META_MSRVC_CREATE_TIME', 674),
     ('META_MSRVC_MODIFY_TIME', 675),
     ('META_MET2_ATTR_NAME', 680),
     ('META_MET2_ATTR_VALUE', 681),
     ('META_MET2_ATTR_UNITS', 682),
     ('META_MET2_ATTR_ID', 683),
     ('META_MET2_CREATE_TIME', 684),
     ('META_MET2_MODIFY_TIME', 685),
     ('DATA_ACCESS_TYPE', 700),
     ('DATA_ACCESS_NAME', 701),
     ('DATA_TOKEN_NAMESPACE', 702),
     ('DATA_ACCESS_USER_ID', 703),
     ('DATA_ACCESS_DATA_ID', 704),
     ('COLL_ACCESS_TYPE', 710),
     ('COLL_ACCESS_NAME', 711),
     ('COLL_TOKEN_NAMESPACE', 712),
     ('COLL_ACCESS_USER_ID', 713),
     ('COLL_ACCESS_COLL_ID', 714),
     ('RESC_ACCESS_TYPE', 720),
     ('RESC_ACCESS_NAME', 721),
     ('RESC_TOKEN_NAMESPACE', 722),
     ('RESC_ACCESS_USER_ID', 723),
     ('RESC_ACCESS_RESC_ID', 724),
     ('META_ACCESS_TYPE', 730),
     ('META_ACCESS_NAME', 731),
     ('META_TOKEN_NAMESPACE', 732),
     ('META_ACCESS_USER_ID', 733),
     ('META_ACCESS_META_ID', 734),
     ('RULE_ACCESS_TYPE', 740),
     ('RULE_ACCESS_NAME', 741),
     ('RULE_TOKEN_NAMESPACE', 742),
     ('RULE_ACCESS_USER_ID', 743),
     ('RULE_ACCESS_RULE_ID', 744),
     ('MSRVC_ACCESS_TYPE', 750),
     ('MSRVC_ACCESS_NAME', 751),
     ('MSRVC_TOKEN_NAMESPACE', 752),
     ('MSRVC_ACCESS_USER_ID', 753),
     ('MSRVC_ACCESS_MSRVC_ID', 754),
     ('USER_GROUP_ID', 900),
     ('USER_GROUP_NAME', 901),
     ('RULE_EXEC_ID', 1000),
     ('RULE_EXEC_NAME', 1001),
     ('RULE_EXEC_REI_FILE_PATH', 1002),
     ('RULE_EXEC_USER_NAME', 1003),
     ('RULE_EXEC_ADDRESS', 1004),
     ('RULE_EXEC_TIME', 1005),
     ('RULE_EXEC_FREQUENCY', 1006),
     ('RULE_EXEC_PRIORITY', 1007),
     ('RULE_EXEC_ESTIMATED_EXE_TIME', 1008),
     ('RULE_EXEC_NOTIFICATION_ADDR', 1009),
     ('RULE_EXEC_LAST_EXE_TIME', 1010),
     ('RULE_EXEC_STATUS', 1011),
     ('TOKEN_NAMESPACE', 1100),
     ('TOKEN_ID', 1101),
     ('TOKEN_NAME', 1102),
     ('TOKEN_VALUE', 1103),
     ('TOKEN_VALUE2', 1104),
     ('TOKEN_VALUE3', 1105),
     ('TOKEN_COMMENT', 1106),
     ('AUDIT_OBJ_ID', 1200),
     ('AUDIT_USER_ID', 1201),
     ('AUDIT_ACTION_ID', 1202),
     ('AUDIT_COMMENT', 1203),
     ('AUDIT_CREATE_TIME', 1204),
     ('AUDIT_MODIFY_TIME', 1205),
     ('AUDIT_RANGE_START', 1200),
     ('AUDIT_RANGE_END', 1299),
     ('COLL_USER_NAME', 1300),
     ('COLL_USER_ZONE', 1301),
     ('DATA_USER_NAME', 1310),
     ('DATA_USER_ZONE', 1311),
     ('RESC_USER_NAME', 1320),
     ('RESC_USER_ZONE', 1321),
     ('SL_HOST_NAME', 1400),
     ('SL_RESC_NAME', 1401),
     ('SL_CPU_USED', 1402),
     ('SL_MEM_USED', 1403),
     ('SL_SWAP_USED', 1404),
     ('SL_RUNQ_LOAD', 1405),
     ('SL_DISK_SPACE', 1406),
     ('SL_NET_INPUT', 1407),
     ('SL_NET_OUTPUT', 1408),
     ('SL_NET_OUTPUT', 1408),
     ('SL_CREATE_TIME', 1409),
     ('SLD_RESC_NAME', 1500),
     ('SLD_LOAD_FACTOR', 1501),
     ('SLD_CREATE_TIME', 1502),
     ('USER_AUTH_ID', 1600),
     ('USER_DN', 1601),
     ('RULE_ID', 1700),
     ('RULE_VERSION', 1701),
     ('RULE_BASE_NAME', 1702),
     ('RULE_NAME', 1703),
     ('RULE_EVENT', 1704),
     ('RULE_CONDITION', 1705),
     ('RULE_BODY', 1706),
     ('RULE_RECOVERY', 1707),
     ('RULE_STATUS', 1708),
     ('RULE_OWNER_NAME', 1709),
     ('RULE_OWNER_ZONE', 1710),
     ('RULE_DESCR_1', 1711),
     ('RULE_DESCR_2', 1712),
     ('RULE_INPUT_PARAMS', 1713),
     ('RULE_OUTPUT_PARAMS', 1714),
     ('RULE_DOLLAR_VARS', 1715),
     ('RULE_ICAT_ELEMENTS', 1716),
     ('RULE_SIDEEFFECTS', 1717),
     ('RULE_COMMENT', 1718),
     ('RULE_CREATE_TIME', 1719),
     ('RULE_MODIFY_TIME', 1720),
     ('RULE_BASE_MAP_VERSION', 1721),
     ('RULE_BASE_MAP_BASE_NAME', 1722),
     ('RULE_BASE_MAP_OWNER_NAME', 1723),
     ('RULE_BASE_MAP_OWNER_ZONE', 1724),
     ('RULE_BASE_MAP_COMMENT', 1725),
     ('RULE_BASE_MAP_CREATE_TIME', 1726),
     ('RULE_BASE_MAP_MODIFY_TIME', 1727),
     ('RULE_BASE_MAP_PRIORITY', 1728),
     ('DVM_ID', 1800),
     ('DVM_VERSION', 1801),
     ('DVM_BASE_NAME', 1802),
     ('DVM_EXT_VAR_NAME', 1803),
     ('DVM_CONDITION', 1804),
     ('DVM_INT_MAP_PATH', 1805),
     ('DVM_STATUS', 1806),
     ('DVM_OWNER_NAME', 1807),
     ('DVM_OWNER_ZONE', 1808),
     ('DVM_COMMENT', 1809),
     ('DVM_CREATE_TIME', 1810),
     ('DVM_MODIFY_TIME', 1811),
     ('DVM_BASE_MAP_VERSION', 1812),
     ('DVM_BASE_MAP_BASE_NAME', 1813),
     ('DVM_BASE_MAP_OWNER_NAME', 1814),
     ('DVM_BASE_MAP_OWNER_ZONE', 1815),
     ('DVM_BASE_MAP_COMMENT', 1816),
     ('DVM_BASE_MAP_CREATE_TIME', 1817),
     ('DVM_BASE_MAP_MODIFY_TIME', 1818),
     ('FNM_ID', 1900),
     ('FNM_VERSION', 1901),
     ('FNM_BASE_NAME', 1902),
     ('FNM_EXT_FUNC_NAME', 1903),
     ('FNM_INT_FUNC_NAME', 1904),
     ('FNM_STATUS', 1905),
     ('FNM_OWNER_NAME', 1906),
     ('FNM_OWNER_ZONE', 1907),
     ('FNM_COMMENT', 1908),
     ('FNM_CREATE_TIME', 1909),
     ('FNM_MODIFY_TIME', 1910),
     ('FNM_BASE_MAP_VERSION', 1911),
     ('FNM_BASE_MAP_BASE_NAME', 1912),
     ('FNM_BASE_MAP_OWNER_NAME', 1913),
     ('FNM_BASE_MAP_OWNER_ZONE', 1914),
     ('FNM_BASE_MAP_COMMENT', 1915),
     ('FNM_BASE_MAP_CREATE_TIME', 1916),
     ('FNM_BASE_MAP_MODIFY_TIME', 1917),
     ('QUOTA_USER_ID', 2000),
     ('QUOTA_RESC_ID', 2001),
     ('QUOTA_LIMIT', 2002),
     ('QUOTA_OVER', 2003),
     ('QUOTA_MODIFY_TIME', 2004),
     ('QUOTA_USAGE_USER_ID', 2010),
     ('QUOTA_USAGE_RESC_ID', 2011),
     ('QUOTA_USAGE', 2012),
     ('QUOTA_USAGE_MODIFY_TIME', 2013),
     ('QUOTA_RESC_NAME', 2020),
     ('QUOTA_USER_NAME', 2021),
     ('QUOTA_USER_ZONE', 2022),
     ('QUOTA_USER_TYPE', 2023),
     ('MSRVC_ID', 2100),
     ('MSRVC_NAME', 2101),
     ('MSRVC_SIGNATURE', 2102),
     ('MSRVC_DOXYGEN', 2103),
     ('MSRVC_VARIATIONS', 2104),
     ('MSRVC_STATUS', 2105),
     ('MSRVC_OWNER_NAME', 2106),
     ('MSRVC_OWNER_ZONE', 2107),
     ('MSRVC_COMMENT', 2108),
     ('MSRVC_CREATE_TIME', 2109),
     ('MSRVC_MODIFY_TIME', 2110),
     ('MSRVC_VERSION', 2111),
     ('MSRVC_HOST', 2112),
     ('MSRVC_LOCATION', 2113),
     ('MSRVC_LANGUAGE', 2114),
     ('MSRVC_TYPE_NAME', 2115),
     ('MSRVC_MODULE_NAME', 2116),
     ('MSRVC_VER_OWNER_NAME', 2150),
     ('MSRVC_VER_OWNER_ZONE', 2151),
     ('MSRVC_VER_COMMENT', 2152),
     ('MSRVC_VER_CREATE_TIME', 2153),
     ('MSRVC_VER_MODIFY_TIME', 2154),
     ('TICKET_ID', 2200),
     ('TICKET_STRING', 2201),
     ('TICKET_TYPE', 2202),
     ('TICKET_USER_ID', 2203),
     ('TICKET_OBJECT_ID', 2204),
     ('TICKET_OBJECT_TYPE', 2205),
     ('TICKET_USES_LIMIT', 2206),
     ('TICKET_USES_COUNT', 2207),
     ('TICKET_EXPIRY_TS', 2208),
     ('TICKET_CREATE_TIME', 2209),
     ('TICKET_MODIFY_TIME', 2210),
     ('TICKET_WRITE_FILE_COUNT', 2211),
     ('TICKET_WRITE_FILE_LIMIT', 2212),
     ('TICKET_WRITE_BYTE_COUNT', 2213),
     ('TICKET_WRITE_BYTE_LIMIT', 2214),
     ('TICKET_ALLOWED_HOST_TICKET_ID', 2220),
     ('TICKET_ALLOWED_HOST', 2221),
     ('TICKET_ALLOWED_USER_TICKET_ID', 2222),
     ('TICKET_ALLOWED_USER_NAME', 2223),
     ('TICKET_ALLOWED_GROUP_TICKET_ID', 2224),
     ('TICKET_ALLOWED_GROUP_NAME', 2225),
     ('TICKET_DATA_NAME', 2226),
     ('TICKET_DATA_COLL_NAME', 2227),
     ('TICKET_COLL_NAME', 2228),
     ('TICKET_OWNER_NAME', 2229),
     ('TICKET_OWNER_ZONE', 2230)]
# -*- coding: utf-8 -*-
"""Utility / convenience functions for dealing with JSON."""

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import json
from collections import OrderedDict

import data_object
import error


class ParseError(error.UUError):
    """
    Exception for unparsable JSON text.

    Python2's JSON lib raises ValueError on bad parses, which is ambiguous.
    Use this exception (together with the functions below) instead.
    (this can also ease transitions to python3, since python3's json already
    uses a different, unambiguous exception type: json.JSONDecodeError)
    """


def _fold(x, **alg):
    """
    Fold over a JSON structure.

    Calls functions from 'alg', indexed by the type of value, to transform values recursively.
    """
    f = alg.get(type(x).__name__, lambda y: y)
    if type(x) in [dict, OrderedDict]:
        return f(OrderedDict([(k, _fold(v, **alg)) for k, v in x.items()]))
    elif type(x) is list:
        return f([_fold(v, **alg) for v in x])
    else:
        return f(x)


def _demote_strings(json_data):
    """
    Transform unicode -> UTF-8 encoded strings recursively, for a given JSON structure.

    Needed for handling unicode in JSON as long as we are still using Python2.
    Both JSON string values and JSON object (dict) keys are transformed.
    """
    return _fold(json_data,
                 unicode=lambda x: x.encode('utf-8'),
                 OrderedDict=lambda x: OrderedDict([(k.encode('utf-8'), v) for k, v in x.items()]))


def _promote_strings(json_data):
    """
    Transform UTF-8 encoded strings -> unicode recursively, for a given JSON structure.

    Needed for handling unicode in JSON as long as we are still using Python2.
    Both JSON string values and JSON object (dict) keys are transformed.

    May raise UnicodeDecodeError if strings are not proper UTF-8.
    """
    return _fold(json_data,
                 str=lambda x: x.decode('utf-8'),
                 OrderedDict=lambda x: OrderedDict([(k.decode('utf-8'), v) for k, v in x.items()]),
                 dict=lambda x: OrderedDict([(k.decode('utf-8'), v) for k, v in x.items()]))


def parse(text, want_bytes=True):
    """
    Parse JSON into an OrderedDict.

    All strings are UTF-8 encoded with Python2 in mind.
    This behavior is disabled if want_bytes is False.
    """
    try:
        x = json.loads(text, object_pairs_hook=OrderedDict)
        return _demote_strings(x) if want_bytes else x
    except ValueError:
        raise ParseError('JSON file format error')


def dump(data, **options):
    """Dump an object to a JSON string."""
    # json.dumps seems to not like mixed str/unicode input, so make sure
    # everything is of the same type first.
    data = _promote_strings(data)
    return json.dumps(data,
                      ensure_ascii=False,  # Don't unnecessarily use \u0000 escapes.
                      encoding='utf-8',
                      **({'indent': 4} if options == {} else options)) \
               .encode('utf-8')  # turn unicode json string back into an encoded str


def read(callback, path, **options):
    """Read an iRODS data object and parse it as JSON."""
    return parse(data_object.read(callback, path), **options)


def write(callback, path, data, **options):
    """Write a JSON object to an iRODS data object."""
    return data_object.write(callback, path, dump(data, **options))
# -*- coding: utf-8 -*-
"""Logging facilities."""

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import inspect

import rule
import user
from config import config


def write(ctx, text):
    """Write a message to the log, including client name and originating rule/API name."""
    caller = inspect.stack()[1][3]
    _write(ctx, '{}: {}'.format(caller, text))


def _write(ctx, text):
    """Write a message to the log, including the client name (intended for internal use)."""
    if type(ctx) is rule.Context:
        ctx.writeLine('serverLog', '{{{}#{}}} {}'.format(*list(user.user_and_zone(ctx)) + [text]))
    else:
        ctx.writeLine('serverLog', text)


def debug(ctx, text):
    """Write a log message if in a development environment."""
    if config.environment == 'development':
        write(ctx, 'DEBUG: {}'.format(text))


def _debug(ctx, text):
    """Write a log message if in a development environment."""
    if config.environment == 'development':
        _write(ctx, 'DEBUG: {}'.format(text))
# -*- coding: utf-8 -*-
"""Miscellaneous functions for interacting with iRODS."""

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import irods_types

import msi


def kvpair(ctx, k, v):
    """Create a keyvalpair object, needed by certain msis."""
    return msi.string_2_key_val_pair(ctx, '{}={}'.format(k, v), irods_types.BytesBuf())['arguments'][1]
# -*- coding: utf-8 -*-
"""iRODS microservice wrappers that provide primitive error handling.

Microservices may fail and indicate failure in a number of different ways.
With this module, we aim to unify microservice error handling by converting
all errors to unambiguous Python exceptions.
"""

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import error


class Error(error.UUError):
    """Error for microservice failure."""

    def __init__(self, message, msi_status, msi_code, msi_args, src_exception):
        super(Error, self).__init__(message)
        # Store msi result, if any.
        # These may be None when an msi aborts in an abnormal way.
        self.msi_status = msi_status
        self.msi_code = msi_code
        self.msi_args = msi_args
        self.src_exception = src_exception

    def __str__(self):
        if self.msi_status is not None:
            return '{}: error code {}'.format(self.message, self.msi_code)
        elif self.src_exception is not None:
            return '{}: iRODS error <{}>'.format(self.message, self.src_exception)
        else:
            return self.message


# Machinery for wrapping microservices and creating microservice-specific exceptions. {{{

def make(name, error_text):
    """Create msi wrapper function and exception type as a tuple (see functions below)."""
    e = _make_exception(name, error_text)
    return (_wrap('msi' + name, e), e)


def _run(msi, exception, *args):
    """Run an MSI such that it throws an MSI-specific exception on failure."""
    try:
        ret = msi(*args)
    except RuntimeError as e:
        # msi failures may be raised as non-specific RuntimeErrors.
        # There is no result to save, but we can still convert this to a
        # msi-specific exception.
        raise exception(None, None, None, e)

    if not ret['status']:
        # False status indicates error.
        raise exception(ret['status'],
                        ret['code'],
                        ret['arguments'])
    return ret


def _wrap(msi, exception):
    """Wrap an MSI such that it throws an MSI-specific exception on failure.

    The arguments to the wrapper are the same as that of the msi, only with
    a callback in front.

    e.g.:    callback.msiDataObjCreate(x, y, z)
    becomes: data_obj_create(callback, x, y, z)
    """
    return lambda callback, *args: _run(getattr(callback, msi), exception, *args)


def _make_exception(name, message):
    """Create a msi Error subtype for a specific microservice."""
    t = type('{}Error'.format(name), (Error,), {})
    t.__init__ = lambda self, status, code, args, e = None: \
        super(t, self).__init__(message, status, code, args, e)
    return t


# }}}
# Microservice wrappers {{{

# This naming scheme follows the original msi name, changed to snake_case.
# Note: there is no 'msi_' prefix:
# When imported without '*', these msis are callable as msi.coll_create(), etc.

data_obj_create, DataObjCreateError = make('DataObjCreate', 'Could not create data object')
data_obj_open,   DataObjOpenError   = make('DataObjOpen',   'Could not open data object')
data_obj_read,   DataObjReadError   = make('DataObjRead',   'Could not read data object')
data_obj_write,  DataObjWriteError  = make('DataObjWrite',  'Could not write data object')
data_obj_close,  DataObjCloseError  = make('DataObjClose',  'Could not close data object')
data_obj_copy,   DataObjCopyError   = make('DataObjCopy',   'Could not copy data object')
data_obj_unlink, DataObjUnlinkError = make('DataObjUnlink', 'Could not remove data object')
data_obj_rename, DataObjRenameError = make('DataObjRename', 'Could not rename data object')
coll_create,     CollCreateError    = make('CollCreate',    'Could not create collection')
rm_coll,         RmCollError        = make('RmColl',        'Could not remove collection')
check_access,    CheckAccessError   = make('CheckAccess',   'Could not check access')
set_acl,         SetACLError        = make('SetACL',        'Could not set ACL')
get_icat_time,   GetIcatTimeError   = make('GetIcatTime',   'Could not get Icat time')
get_obj_type,    GetObjTypeError    = make('GetObjType',    'Could not get object type')

register_epic_pid, RegisterEpicPIDError = make('RegisterEpicPID', 'Could not register EpicPID')

string_2_key_val_pair, String2KeyValPairError = \
    make('String2KeyValPair', 'Could not create keyval pair')

set_key_value_pairs_to_obj, SetKeyValuePairsToObjError = \
    make('SetKeyValuePairsToObj', 'Could not set metadata on object')

associate_key_value_pairs_to_obj, AssociateKeyValuePairsToObjError = \
    make('AssociateKeyValuePairsToObj', 'Could not associate metadata to object')

# :s/[A-Z]/_\L\0/g

remove_key_value_pairs_from_obj, RemoveKeyValuePairsFromObjError = \
    make('RemoveKeyValuePairsFromObj', 'Could not remove metadata from object')

add_avu, AddAvuError = make('_add_avu', 'Could not add metadata to object')
rmw_avu, RmwAvuError = make('_rmw_avu', 'Could not remove metadata to object')

sudo_obj_acl_set, SudoObjAclSetError = make('SudoObjAclSet', 'Could not set ACLs as admin')

# Add new msis here as needed.

# }}}
# -*- coding: utf-8 -*-
"""Utility / convenience functions for dealing with paths."""

# (ideally this module would be named 'path', but name conflicts cause too much pain)

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import re
from enum import Enum

import msi
import query
from query import Query


class Space(Enum):
    """Differentiates Yoda path types between research and vault spaces."""

    OTHER       = 0
    RESEARCH    = 1
    VAULT       = 2
    DATAMANAGER = 3

    def __repr__(self):
        return 'Space.' + self.name


class ObjectType(Enum):
    COLL = 0
    DATA = 1

    def __repr__(self):
        return 'ObjectType.' + self.name

    def __str__(self):
        return '-d' if self is ObjectType.DATA else '-C'


def chop(path):
    """Split off the rightmost path component of a path.

    /a/b/c -> (/a/b, c)
    """
    # In practice, this is the same as os.path.split on POSIX systems,
    # but it's better to not rely on OS-defined path syntax for iRODS paths.
    if path == '/' or len(path) == 0:
        return '/', ''
    else:
        x = path.split('/')
        return '/'.join(x[:-1]), x[-1]


def dirname(path):
    """Return the dirname of a path."""
    return chop(path)[0]  # chops last component off


def basename(path):
    """Return basename of a path."""
    return chop(path)[1]  # chops everything *but* the last component


def chopext(path):
    """Return the extension of a path."""
    return path.rsplit('.', 1)


def info(path):
    """
    Parse a path into a (Space, zone, group, subpath) tuple.

    Synopsis: space, zone, group, subpath = pathutil.info(path)

    This can be used to discern research and vault paths, and provides
    group name and subpath information.

    Examples:

    /                              => Space.OTHER,       '',         '',              ''
    /tempZone                      => Space.OTHER,       'tempZone', '',              ''
    /tempZone/yoda/x               => Space.OTHER,       'tempZone', '',              'yoda/x'
    /tempZone/home                 => Space.OTHER,       'tempZone', '',              'home'
    /tempZone/home/rods            => Space.OTHER,       'tempZone', 'rods',          ''
    /tempZone/home/vault-x         => Space.VAULT,       'tempZone', 'vault-x',       ''
    /tempZone/home/vault-x/y       => Space.VAULT,       'tempZone', 'vault-x',       'y'
    /tempZone/home/datamanager-x/y => Space.DATAMANAGER, 'tempZone', 'datamanager-x', 'y'
    /tempZone/home/research-x/y/z  => Space.RESEARCH,    'tempZone', 'research-x',    'y/z'
    etc.
    """
    # Turn empty match groups into empty strings.
    def f(x):
        return '' if x is None else x

    def g(m, i):
        return '' if i > len(m.groups()) else f(m.group(i))

    def result(s, m):
        return (s, g(m, 1), g(m, 2), g(m, 3))

    # Try a pattern and report success if it matches.
    def test(r, space):
        m = re.match(r, path)
        return m and result(space, m)

    from collections import namedtuple

    return (namedtuple('PathInfo', 'space zone group subpath'.split())
            (*test('^/([^/]+)/home/(vault-[^/]+)(?:/(.+))?$',        Space.VAULT)
            or test('^/([^/]+)/home/(research-[^/]+)(?:/(.+))?$',    Space.RESEARCH)
            or test('^/([^/]+)/home/(datamanager-[^/]+)(?:/(.+))?$', Space.DATAMANAGER)
            or test('^/([^/]+)/home/([^/]+)(?:/(.+))?$',             Space.OTHER)
            or test('^/([^/]+)()(?:/(.+))?$',                        Space.OTHER)
            or (Space.OTHER, '', '', '')))  # (matches '/' and empty paths)


def object_type(ctx, path):
    try:
        t = msi.get_obj_type(ctx, path, '')['arguments'][1]
    except Exception as e:
        return
    if t == '-d':
        return ObjectType.DATA
    if t == '-c':
        return ObjectType.COLL


def fs_object_from_id(ctx, obj_id):
    """Return (path, ObjectType) for the given object id, or (None, None) if the ID does not exist."""
    x = Query(ctx, 'COLL_NAME, DATA_NAME', "DATA_ID = '{}'".format(obj_id), query.AS_DICT).first() \
        or Query(ctx, 'COLL_NAME',            "COLL_ID = '{}'".format(obj_id), query.AS_DICT).first()

    if x is None:  # obj does not exist.
        return None, None
    elif 'DATA_NAME' in x:
        return '{}/{}'.format(*x.values()), ObjectType.DATA
    else:
        return x['COLL_NAME'], ObjectType.COLL
# -*- coding: utf-8 -*-
"""Utilities for creating PEP rules."""

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import api
import log
import rule


class Succeed(object):
    """Policy function result, indicates success.

    Evaluates to True in boolean context.
    """

    def __str__(self):
        return 'Action permitted'

    def __bool__(self):
        return True
    __nonzero__ = __bool__


class Fail(object):
    """Policy function result, indicates failure.

    As a result, the PEP-instrumented operation will be aborted, and
    pep_x_except will fire.

    Evaluates to False in boolean context.
    """

    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return 'Action not permitted: ' + self.reason

    def __bool__(self):
        return False
    __nonzero__ = __bool__


# Functions to be used to instantiate the above result types.
fail    = Fail
succeed = Succeed


def all(*x):
    for i in x:
        if not i:
            return i
    return succeed()


def require():
    """Turn a function into a PEP rule that fails unless policy.succeed() is returned.

    The function must explicitly return policy.succeed() or .fail('reason') as a result.
    Any other return type will result in the PEP failing (blocks associated action).
    """
    def deco(f):
        @rule.make(outputs=[])
        def r(ctx, *args):
            try:
                result = f(ctx, *args)
            except api.Error as e:
                log._write(ctx, '{} failed due to unhandled API error: {}'.format(f.__name__, str(e)))
                raise
            except Exception as e:
                log._write(ctx, '{} failed due to unhandled internal error: {}'.format(f.__name__, str(e)))
                raise

            if isinstance(result, Succeed):
                return  # succeed the rule (msi "succeed" has no effect here)
            elif isinstance(result, Fail):
                log._write(ctx, '{} denied: {}'.format(f.__name__, str(result)))
                ctx.msiOprDisallowed()
                raise AssertionError()  # Just in case.

            # Require an unambiguous YES from the policy function.
            # Default to fail.
            log._write(ctx, '{} denied: ambiguous policy result (internal error): {}'
                            .format(f.__name__, str(result)))
            ctx.msiOprDisallowed()
            raise AssertionError()
        return r
    return deco
# -*- coding: utf-8 -*-
"""Utilities for performing iRODS genqueries."""

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

from collections import OrderedDict
from enum import Enum

import irods_types

MAX_SQL_ROWS = 256


class Option(object):
    """iRODS QueryInp option flags - used internally.

    AUTO_CLOSE, RETURN_TOTAL_ROW_COUNT, and UPPER_CASE_WHERE should not be set
    by calling code, as Query already provides convenient functionality for this.

    See irods: lib/core/include/rodsGenQuery.h
    """
    RETURN_TOTAL_ROW_COUNT = 0x020
    NO_DISTINCT            = 0x040
    QUOTA_QUERY            = 0x080
    AUTO_CLOSE             = 0x100
    UPPER_CASE_WHERE       = 0x200


class OutputType(Enum):
    """
    Represents query output type.

    AS_DICT:  result rows are dicts of (column_name => value)
    AS_LIST:  result rows are lists of cells (ordered by input column list)
    AS_TUPLE: result rows are tuples of cells, or a single string if only one column is selected

    Note that when using AS_DICT, operations on columns (MAX, COUNT, ORDER, etc.)
    become part of the column name in the result.
    """

    AS_DICT  = 0
    AS_LIST  = 1
    AS_TUPLE = 2


AS_DICT  = OutputType.AS_DICT
AS_LIST  = OutputType.AS_LIST
AS_TUPLE = OutputType.AS_TUPLE


class Query(object):
    """Generator-style genquery iterator.

    :param callback:       iRODS callback
    :param columns:        a list of SELECT column names, or columns as a comma-separated string.
    :param condition:      (optional) where clause, as a string
    :param output:         (optional) [default=AS_TUPLE] either AS_DICT/AS_LIST/AS_TUPLE
    :param offset:         (optional) starting row (0-based), can be used for pagination
    :param limit:          (optional) maximum amount of results, can be used for pagination
    :param case_sensitive: (optional) set this to False to make the entire where-clause case insensitive
    :param options:        (optional) other OR-ed options to pass to the query (see the Option type above)

    Getting the total row count:

      Use q.total_rows() to get the total number of results matching the query
      (without taking offset/limit into account).

    Output types:

      AS_LIST and AS_DICT behave the same as in row_iterator.
      AS_TUPLE produces a tuple, similar to AS_LIST, with the exception that
      for queries on single columns, each result is returned as a string
      instead of a 1-element tuple.

    Examples:

        # Print all collections.
        for x in Query(callback, 'COLL_NAME'):
            print('name: ' + x)

        # The same, but more verbose:
        for x in Query(callback, 'COLL_NAME', output=AS_DICT):
            print('name: {}'.format(x['COLL_NAME']))

        # ... or make it into a list
        colls = list(Query(callback, 'COLL_NAME'))

        # ... or get data object paths
        datas = ['{}/{}'.format(x, y) for x, y in Query(callback, 'COLL_NAME, DATA_NAME')]

        # Print the first 200-299 of data objects ordered descending by data
        # name, owned by a username containing 'r' or 'R', in a collection
        # under (case-insensitive) '/tempzone/'.
        for x in Query(callback, 'COLL_NAME, ORDER_DESC(DATA_NAME), DATA_OWNER_NAME',
                       "DATA_OWNER_NAME like '%r%' and COLL_NAME like '/tempzone/%'",
                       case_sensitive=False,
                       offset=200, limit=100):
            print('name: {}/{} - owned by {}'.format(*x))
    """

    def __init__(self,
                 callback,
                 columns,
                 conditions='',
                 output=AS_TUPLE,
                 offset=0,
                 limit=None,
                 case_sensitive=True,
                 options=0):

        self.callback = callback

        if type(columns) is str:
            # Convert to list for caller convenience.
            columns = [x.strip() for x in columns.split(',')]

        assert type(columns) is list

        # Boilerplate.
        self.columns    = columns
        self.conditions = conditions
        self.output     = output
        self.offset     = offset
        self.limit      = limit
        self.options    = options

        assert self.output in (AS_TUPLE, AS_LIST, AS_DICT)

        if not case_sensitive:
            # Uppercase the entire condition string. Should cause no problems,
            # since query keywords are case insensitive as well.
            self.options   |= Option.UPPER_CASE_WHERE
            self.conditions = self.conditions.upper()

        self.gqi = None  # genquery inp
        self.gqo = None  # genquery out
        self.cti = None  # continue index

        # Filled when calling total_rows() on the Query.
        self._total = None

    def exec_if_not_yet_execed(self):
        """Query execution is delayed until the first result or total row count is requested."""
        if self.gqi is not None:
            return

        self.gqi = self.callback.msiMakeGenQuery(', '.join(self.columns),
                                                 self.conditions,
                                                 irods_types.GenQueryInp())['arguments'][2]
        if self.offset > 0:
            self.gqi.rowOffset = self.offset
        else:
            # If offset is 0, we can (relatively) cheaply let iRODS count rows.
            # - with non-zero offset, the query must be executed twice if the
            #   row count is needed (see total_rows()).
            self.options |= Option.RETURN_TOTAL_ROW_COUNT

        if self.limit is not None and self.limit < MAX_SQL_ROWS - 1:
            # We try to limit the amount of rows we pull in, however in order
            # to close the query, 256 more rows will (if available) be fetched
            # regardless.
            self.gqi.maxRows = self.limit

        self.gqi.options |= self.options

        import log
        log._debug(self.callback, self)

        self.gqo    = self.callback.msiExecGenQuery(self.gqi, irods_types.GenQueryOut())['arguments'][1]
        self.cti    = self.gqo.continueInx
        self._total = None

    def total_rows(self):
        """Return the total amount of rows matching the query.

        This includes rows that are omitted from the result due to limit/offset parameters.
        """
        if self._total is None:
            if self.offset == 0 and self.options & Option.RETURN_TOTAL_ROW_COUNT:
                # Easy mode: Extract row count from gqo.
                self.exec_if_not_yet_execed()
                self._total = self.gqo.totalRowCount
            else:
                # Hard mode: for some reason, using PostgreSQL, you cannot get
                # the total row count when an offset is supplied.
                # When RETURN_TOTAL_ROW_COUNT is set in combination with a
                # non-zero offset, iRODS solves this by executing the query
                # twice[1], one time with no offset to get the row count.
                # Apparently this does not work (we get the correct row count, but no rows).
                # So instead, we run the query twice manually. This should
                # perform only slightly worse.
                # [1]: https://github.com/irods/irods/blob/4.2.6/plugins/database/src/general_query.cpp#L2393
                self._total = Query(self.callback, self.columns, self.conditions, limit=0,
                                    options=self.options | Option.RETURN_TOTAL_ROW_COUNT).total_rows()

        return self._total

    def __iter__(self):
        self.exec_if_not_yet_execed()

        row_i = 0

        # Iterate until all rows are fetched / the query is aborted.
        while True:
            try:
                # Iterate over a set of rows.
                for r in range(self.gqo.rowCnt):
                    if self.limit is not None and row_i >= self.limit:
                        self._close()
                        return

                    row = [self.gqo.sqlResult[c].row(r) for c in range(len(self.columns))]
                    row_i += 1

                    if self.output == AS_TUPLE:
                        yield row[0] if len(self.columns) == 1 else tuple(row)
                    elif self.output == AS_LIST:
                        yield row
                    else:
                        yield OrderedDict(zip(self.columns, row))

            except GeneratorExit:
                self._close()
                return

            if self.cti <= 0 or self.limit is not None and row_i >= self.limit:
                self._close()
                return

            self._fetch()

    def _fetch(self):
        """Fetch the next batch of results."""
        ret      = self.callback.msiGetMoreRows(self.gqi, self.gqo, 0)
        self.gqo = ret['arguments'][1]
        self.cti = ret['arguments'][2]

    def _close(self):
        """Close the query (prevents filling the statement table)."""
        if not self.cti:
            return

        # msiCloseGenQuery fails with internal errors.
        # Close the query using msiGetMoreRows instead.
        # This is less than ideal, because it may fetch 256 more rows
        # (gqi.maxRows is overwritten) resulting in unnecessary processing
        # work. However there appears to be no other way to close the query.

        while self.cti > 0:
            # Close query immediately after getting the next batch.
            # This avoids having to soak up all remaining results.
            self.gqi.options |= Option.AUTO_CLOSE
            self._fetch()

        # Mark self as closed.
        self.gqi = None
        self.gqo = None
        self.cti = None

    def first(self):
        """Get exactly one result (or None if no results are available)."""
        for x in self:
            self._close()
            return x

    def __str__(self):
        return 'Query(select {}{}{}{})'.format(', '.join(self.columns),
                                               ' where ' + self.conditions if self.conditions else '',
                                               ' limit ' + str(self.limit) if self.limit is not None else '',
                                               ' offset ' + str(self.offset) if self.offset else '')

    def __del__(self):
        """Auto-close query on when Query goes out of scope."""
        self._close()
# -*- coding: utf-8 -*-
"""Experimental Python/Rule interface code."""

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import json
from enum import Enum


class Context(object):
    """Combined type of a callback and rei struct.

    `Context` can be treated as a rule engine callback for all intents and purposes.
    However @rule and @api functions that need access to the rei, can do so through this object.
    """
    def __init__(self, callback, rei):
        self.callback = callback
        self.rei      = rei

    def __getattr__(self, name):
        """Allow accessing the callback directly."""
        return getattr(self.callback, name)


class Output(Enum):
    """Specifies rule output handlers."""
    STORE      = 0  # store in output parameters
    STDOUT     = 1  # write to stdout
    STDOUT_BIN = 2  # write to stdout, without a trailing newline


def make(inputs=None, outputs=None, transform=lambda x: x, handler=Output.STORE):
    """Create a rule (with iRODS calling conventions) from a Python function.

    :param inputs:    Optional list of rule_args indices to influence how parameters are passed to the function.
    :param outputs:   Optional list of rule_args indices to influence how return values are processed.
    :param transform: Optional function that will be called to transform each output value.
    :param handler:   Specifies how return values are handled.

    inputs and outputs can optionally be specified as lists of indices to
    influence how parameters are passed to this function, and how the return
    value is processed. By default, 'inputs' and 'outputs' both span all rule arguments.

    transform can be used to apply a transformation to the returned value(s),
    e.g. by encoding them as JSON.

    handler specifies what to do with the (transformed) return value(s):
    - Output.STORE:      stores return value(s) in output parameter(s) (this is the default)
    - Output.STDOUT:     prints return value(s) to stdout
    - Output.STDOUT_BIN: prints return value(s) to stdout, without a trailing newline

    Examples:

        @rule.make(inputs=[0,1], outputs=[2])
        def foo(ctx, x, y):
            return int(x) + int(y)

    is equivalent to:

        def foo(rule_args, callback, rei):
            x, y = rule_args[0:2]
            rule_args[2] = int(x) + int(y)

    and...

        @rule.make(transform=json.dumps, handler=Output.STDOUT)
        def foo(ctx, x, y):
            return {'result': int(x) + int(y)}

    is equivalent to:

        def foo(rule_args, callback, rei):
            x, y = rule_args[0:2]
            callback.writeString('stdout', json.dumps(int(x) + int(y)))
    """
    def encode_val(v):
        """Encode a value such that it can be safely transported in rule_args, as output."""
        if type(v) is str:
            return v
        else:
            # Encode numbers, bools, lists and dictionaries as JSON strings.
            # note: the result of encoding e.g. int(5) should be equal to str(int(5)).
            return json.dumps(v)

    def deco(f):
        def r(rule_args, callback, rei):
            a = rule_args if inputs is None else [rule_args[i] for i in inputs]
            result = f(Context(callback, rei), *a)

            if result is None:
                return

            result = map(transform, list(result) if type(result) is tuple else [result])

            if handler is Output.STORE:
                if outputs is None:
                    # outputs not specified? overwrite all arguments.
                    rule_args[:] = map(encode_val, result)
                else:
                    # set specific output arguments.
                    for i, x in zip(outputs, result):
                        rule_args[i] = encode_val(x)
            elif handler is Output.STDOUT:
                for x in result:
                    callback.writeString('stdout', encode_val(x) + '\n')
                    # For debugging:
                    # log.write(callback, 'rule output (DEBUG): ' + encode_val(x))
            elif handler is Output.STDOUT_BIN:
                for x in result:
                    callback.writeString('stdout', encode_val(x))
        return r
    return deco
# -*- coding: utf-8 -*-
"""Utility / convenience functions for querying user info."""

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

from collections import namedtuple

import genquery
import session_vars

from query import Query

# User is a tuple consisting of a name and a zone, which stringifies into 'user#zone'.
User = namedtuple('User', ['name', 'zone'])
User.__str__ = lambda self: '{}#{}'.format(*self)


def user_and_zone(ctx):
    """Obtain client name and zone."""
    client = session_vars.get_map(ctx.rei)['client_user']
    return User(client['user_name'], client['irods_zone'])


def full_name(ctx):
    """Obtain client name and zone, formatted as a 'x#y' string."""
    return str(user_and_zone(ctx))


def name(ctx):
    """Get the name of the client user."""
    return session_vars.get_map(ctx.rei)['client_user']['user_name']


def zone(ctx):
    """Get the zone of the client user."""
    return session_vars.get_map(ctx.rei)['client_user']['irods_zone']


def from_str(ctx, s):
    """Return a (user,zone) tuple from a user[#zone] string.

    If no zone is present in the string, the client's zone is used.
    """
    parts = s.split('#')
    if len(parts) < 2 or len(parts[1]) == 0:
        # Take zone from client zone when not present.
        return User(parts[0], zone(ctx))
    else:
        return User(*parts)


def exists(ctx, user):
    """Check if a user exists."""
    if type(user) is str:
        user = from_str(ctx, user)

    return Query(ctx, "USER_TYPE", "USER_NAME = '{}' AND USER_ZONE = '{}'".format(*user)).first() is not None


def user_type(ctx, user=None):
    """Return the user type ('rodsuser' or 'rodsadmin') for the given user, or the client user if no user is given.

    If the user does not exist, None is returned.
    """
    if user is None:
        user = user_and_zone(ctx)
    elif type(user) is str:
        user = from_str(ctx, user)

    return Query(ctx, "USER_TYPE",
                      "USER_NAME = '{}' AND USER_ZONE = '{}'".format(*user)).first()


def is_admin(ctx, user=None):
    """Check if user is an admin."""
    return user_type(ctx, user) == 'rodsadmin'


def is_member_of(ctx, group, user=None):
    """Check if user is member of given group."""
    if user is None:
        user = user_and_zone(ctx)
    elif type(user) is str:
        user = from_str(ctx, user)

    return Query(ctx, 'USER_GROUP_NAME',
                      "USER_NAME = '{}' AND USER_ZONE = '{}' AND USER_GROUP_NAME = '{}'"
                      .format(*list(user) + [group])).first() is not None


# TODO: Remove. {{{
def get_client_name_zone(rei):
    """Obtain client name and zone, as a tuple."""
    client = session_vars.get_map(rei)['client_user']
    return client['user_name'], client['irods_zone']


# TODO: Replace calls (meta.py) with full_name.
def get_client_full_name(rei):
    """Obtain client name and zone, formatted as a 'x#y' string."""
    return '{}#{}'.format(*get_client_name_zone(rei))
# }}}


def name_from_id(callback, user_id):
    """Retrieve username from user ID."""
    for row in genquery.row_iterator("USER_NAME",
                                     "USER_ID = '{}'".format(user_id),
                                     genquery.AS_LIST, callback):
        return row[0]
    return ''
