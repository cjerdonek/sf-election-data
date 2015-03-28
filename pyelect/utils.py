"""Project-wide helper functions."""

import logging
import os

import yaml


_log = logging.getLogger()

FILE_MANUAL = 'manual'
FILE_AUTO_UPDATED = 'auto_updated'
FILE_AUTO_GENERATED = 'auto_generated'

FILE_TYPES = (FILE_MANUAL, FILE_AUTO_UPDATED, FILE_AUTO_GENERATED)

DIR_NAME_OUTPUT = '_build'
DIR_PRE_DATA = 'pre_data'
KEY_META_COMMENTS = 'comments'
KEY_META = '_meta'
KEY_META_COMMENTS = 'comments'
KEY_FILE_TYPE = '_type'
KEY_FILE_TYPE_COMMENT = '_type_comment'

FILE_TYPE_COMMENTS = {
    FILE_AUTO_UPDATED:
        "WARNING: this file is auto-updated. Any YAML comments will be deleted.",
    FILE_AUTO_GENERATED:
        "WARNING: this file is auto-generated. Do not edit this file!",
}


# The idea for this comes from here:
# http://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data
def _yaml_str_representer(dumper, data):
    """A PyYAML representer that uses literal blocks for multi-line strings.

    For example--

      long: |
        This is
        a multi-line
        string.
      short: This is a one-line string.
    """
    style = '|' if '\n' in data else None
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style=style)


yaml.add_representer(str, _yaml_str_representer)


def get_from(dict_, key, message=None):
    try:
        value = dict_[key]
    except:
        raise Exception("error getting key {0!r} from: {1!r} message={2}"
                        .format(key, dict_, message))
    return value


def get_repo_dir():
    repo_dir = os.path.join(os.path.dirname(__file__), os.pardir)
    return os.path.abspath(repo_dir)


def get_pre_data_dir():
    repo_dir = get_repo_dir()
    dir_path = os.path.join(repo_dir, DIR_PRE_DATA)
    return dir_path


def write(path, text):
    _log.info("writing to: {0}".format(path))
    with open(path, mode='w') as f:
        f.write(text)


def read_yaml(path):
    with open(path) as f:
        data = yaml.load(f)
    return data


def read_yaml_rel(rel_path, key=None):
    """Return the data in a YAML file as a Python dict.

    Arguments:
      rel_path: the path to the file relative to the repo root.
      key: optionally, the key-value to return.
    """
    repo_dir = get_repo_dir()
    path = os.path.join(repo_dir, rel_path)
    data = read_yaml(path)
    if key is not None:
        data = data[key]
    return data


def yaml_dump(*args):
    return yaml.dump(*args, default_flow_style=False, allow_unicode=True, default_style=None)


def _write_yaml(data, path, stdout=None):
    if stdout is None:
        stdout = False
    with open(path, "w") as f:
        yaml_dump(data, f)
    if stdout:
        print(yaml_dump(data))


def _get_yaml_meta(data):
    return get_from(data, KEY_META)


def _set_header(data, file_type, comments=None):
    meta = data.setdefault(KEY_META, {})

    if file_type is None:
        # Then we require that the file type already be specified.
        file_type = meta[KEY_FILE_TYPE]
    else:
        meta[KEY_FILE_TYPE] = file_type

    comment = FILE_TYPE_COMMENTS.get(file_type)
    if comment:
        meta[KEY_FILE_TYPE_COMMENT] = comment

    if comments is not None:
        meta[KEY_META_COMMENTS] = comments


def write_yaml_with_header(data, rel_path, file_type=None, comments=None,
                           stdout=None):
    repo_dir = get_repo_dir()
    path = os.path.join(repo_dir, rel_path)
    _set_header(data, file_type=file_type, comments=comments)
    _write_yaml(data, path, stdout=stdout)


def _is_yaml_normalizable(data, path_hint):
    try:
        file_type = _get_yaml_file_type(data)
    except:
        raise Exception("for file: {0}".format(path_hint))
    # Use a white list instead of a black list to be safe.
    return file_type in (FILE_AUTO_UPDATED, FILE_AUTO_GENERATED)


def is_yaml_file_normalizable(path):
    data = read_yaml(path)
    return _is_yaml_normalizable(data, path_hint=path)


# TODO: remove this function.
def _get_yaml_data(dir_path, base_name):
    """Return the data in a YAML file as a pair of dicts.

    Arguments:
      name: base name of the objects file (e.g. "offices" for "offices.yaml").
    """
    file_name = "{0}.yaml".format(base_name)
    path = os.path.join(dir_path, file_name)
    all_yaml = read_yaml(path)
    data = all_yaml[base_name]
    try:
        meta = _get_yaml_meta(all_yaml)
    except KeyError:
        raise Exception("from file at: {0}".format(path))

    return data, meta


def _get_yaml_file_type(data):
    meta = _get_yaml_meta(data)
    file_type = get_from(meta, KEY_FILE_TYPE)
    if file_type not in FILE_TYPES:
        raise Exception('bad file type: {0}'.format(file_type))
    return file_type


def normalize_yaml(path, stdout=None):
    data = read_yaml(path)
    normalizable = _is_yaml_normalizable(data, path_hint=path)
    if not normalizable:
        _log.info("skipping normalization: {0}".format(path))
        return

    write_yaml_with_header(data, path, stdout=stdout)
