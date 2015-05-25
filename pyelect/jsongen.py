
from collections import defaultdict
from copy import deepcopy
import glob
import json
import logging
import os
from pprint import pformat, pprint
import textwrap

import yaml

from pyelect import lang
from pyelect.common import utils
from pyelect.common.utils import (JSON_OUTPUT_PATH, LANG_ENGLISH, easy_format,
                                  append_i18n_suffix, get_required)
from pyelect.common import yamlutil


COURT_OF_APPEALS_ID = 'ca_court_app'

KEY_DISTRICTS = 'districts'
KEY_ID = '_id'
KEY_OFFICES = 'offices'

_LICENSE = ("The database consisting of this file is made available under "
"the Public Domain Dedication and License v1.0 whose full text can be "
"found at: http://www.opendatacommons.org/licenses/pddl/1.0/ .")

_log = logging.getLogger()


def get_json_path():
    repo_dir = utils.get_repo_dir()
    json_path = os.path.join(repo_dir, JSON_OUTPUT_PATH)
    return json_path


def get_yaml_data(base_name):
    """Return the object data from a YAML file."""
    rel_path = utils.get_yaml_objects_path_rel(base_name)
    data = yamlutil.read_yaml_rel(rel_path)
    meta = yamlutil.get_yaml_meta(data)
    objects = utils.get_required(data, base_name)

    return objects, meta


def get_json():
    """Read and return the JSON data."""
    json_path = get_json_path()
    with open(json_path) as f:
        data = json.load(f)

    return data


def get_fields(field_data, node_name):
    type_name = utils.types_name_to_singular(node_name)
    fields = field_data[type_name]

    return fields


def customize_area(json_object, object_data, global_data):
    pass


def customize_body(json_object, object_data, global_data):
    pass


def customize_category(json_object, object_data, global_data):
    pass


def customize_district_type(json_object, object_data, global_data):
    pass


def customize_district(json_object, object_data, global_data):
    type_name, district_type = utils.get_referenced_object(object_data, 'district_type_id', global_data=global_data)

    name_format = get_required(district_type, 'district_name_format')
    name = easy_format(name_format, **object_data)
    json_object['name'] = name

    short_name_format = get_required(district_type, 'district_name_short_format')
    short_name = easy_format(short_name_format, **object_data)
    json_object['name_short'] = short_name


def customize_election_method(json_object, object_data, global_data):
    pass


def customize_language(json_object, object_data, global_data):
    pass


def customize_office(json_object, object_data, global_data):
    """Return the node containing internationalized data."""
    # TODO: review the code below to see if it is necessary.
    info = utils.get_referenced_object(object_data, 'body_id', global_data=global_data)
    if info is not None:
        type_name, body = info
        name = get_required(body, 'member_name')
        json_object['name'] = name


def customize_phrase(json_object, object_data, global_data):
    pass


def make_court_of_appeals_division_numbers():
    return range(1, 6)


def make_court_of_appeals_district_id(division):
    return "{0}_d1_div{1}".format(COURT_OF_APPEALS_ID, division)


def make_court_of_appeals_office_type_id(office_type):
    return "{0}_{1}".format(COURT_OF_APPEALS_ID, office_type)


def make_court_of_appeals_office_id(division, office_type):
    return "{0}_d1_div{1}_{2}".format(COURT_OF_APPEALS_ID, division, office_type)


def make_court_of_appeals_district(division):
    _id = make_court_of_appeals_district_id(division)
    district = {
        KEY_ID: _id,
        'district_type_id': 'ca_court_app_d1',
        'district_code': division,
    }
    return district


def make_court_of_appeals_districts():
    districts = [make_court_of_appeals_district(c) for c in
                 make_court_of_appeals_division_numbers()]
    return districts


def make_court_of_appeals_office(division, office_type, seat_count=None):
    office = {
        KEY_ID: make_court_of_appeals_office_id(division, office_type),
        'office_type_id': make_court_of_appeals_office_type_id(office_type),
    }
    if seat_count is not None:
        office['seat_count'] = seat_count

    return office


def make_court_of_appeals():
    keys = (KEY_DISTRICTS, KEY_OFFICES)
    # TODO: make the following two lines into a helper function.
    data = {k: [] for k in keys}
    districts, offices = [data[k] for k in keys]

    division_numbers = make_court_of_appeals_division_numbers()
    for division in division_numbers:
        office = make_court_of_appeals_office(division, 'pj')
        offices.append(office)
        office = make_court_of_appeals_office(division, 'aj', seat_count=3)
        offices.append(office)

    return offices


def make_json_object(object_data, customize_func, type_name, object_id, object_base,
                     field_data, global_data, mixins):
    json_object = utils.create_object(object_data, type_name=type_name,
                                      object_id=object_id, object_base=object_base,
                                      field_data=field_data, global_data=global_data,
                                      mixins=mixins)
    customize_func(json_object, object_data, global_data=global_data)

    # TODO: review the code below in light of the new way we are treating i18n.
    #
    # Set the non-i18n version of i18n fields to simplify English-only
    # processing of the JSON file.
    fields = field_data[type_name]
    for field_name, field in sorted(fields.items()):  # We sort for reproducibility.
        if not field.get('i18n_okay'):
            continue
        i18n_field_name = append_i18n_suffix(field_name)
        try:
            phrase = json_object[i18n_field_name]
        except KeyError:
            # Then the internationalized field is not present.
            continue
        english = phrase[LANG_ENGLISH]
        json_object[field_name] = english

    utils.check_object(json_object, type_name=type_name, data_type='JSON',
                       field_data=field_data)

    return json_object


def add_json_node(json_data, node_name, field_data, mixins, **kwargs):
    """Add the node with key node_name."""
    _log.info("calculating json node: {0}".format(node_name))
    type_name = utils.types_name_to_singular(node_name)

    objects, meta = get_yaml_data(node_name)
    object_base = meta.get('base', {})
    customize_function_name = "customize_{0}".format(type_name)
    customize_func = globals()[customize_function_name]

    json_node = {}
    # We sort the objects for repeatability when troubleshooting.
    for object_id in sorted(objects.keys()):
        object_data = objects[object_id]
        try:
            json_object = make_json_object(object_data, customize_func, type_name=type_name,
                                           object_id=object_id, object_base=object_base,
                                           field_data=field_data, global_data=json_data,
                                           mixins=mixins)
        except:
            raise Exception("while processing {0!r} object:\n-->{1}"
                            .format(type_name, object_data))
        json_node[object_id] = json_object

    json_data[node_name] = json_node


def load_json_fields():
    data = yamlutil.read_yaml_rel(utils.JSON_FIELDS_PATH)
    fields = get_required(data, 'fields')
    return fields


def make_json_data():
    field_data = load_json_fields()
    mixins, meta = get_yaml_data('mixins')

    node_names = [
        'phrases',
        'areas',
        'categories',
        'district_types',
        'districts',
        'election_methods',
        'languages',
        'bodies',
        'offices',
    ]

    json_data ={}
    for base_name in node_names:
        add_json_node(json_data, base_name, field_data, mixins=mixins)

    json_data['_meta'] = {
        'license': _LICENSE
    }

    return json_data
