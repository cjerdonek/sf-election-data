"""Support for making html."""

from jinja2 import Environment, FileSystemLoader

from pyelect import utils


def make_district(value):
    data = {
        'name': value['district_code']
    }
    return data

def make_districts(data):
    districts = [make_district(v) for v in data['districts']]
    return districts


def make_office(trans, data):
    try:
        name_text_id = data['name_i18n']
    except KeyError:
        # TODO: calculate the name in all cases.
        return None

    words = trans[name_text_id]
    name = words['en']
    translations = [words[lang] for lang in words.keys() if lang != 'en']
    translations = filter(None, translations)
    office = {
        'name': name,
        'translations': translations,
    }
    return office


def make_offices(data):
    trans = data['i18n']
    offices = [make_office(trans, v) for v in data['offices']]
    return offices


def make_template_data(input_data):
    data = {
#        'districts': make_districts(input_data),
        'offices': make_offices(input_data),
    }

    return data


def render_template(template_name, data):
    """Render the sample template as a Unicode string.

    Argument:
      data: a dict of template variables.
    """
    template_dir = utils.get_template_dir()
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    print(data)
    return template.render(data)


def make_html(input_data):
    template_data = make_template_data(input_data)
    html = render_template('sample.html', template_data)
    return html
