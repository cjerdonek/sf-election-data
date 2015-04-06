"""Customs custom Django tags.

To define custom tags, Django requires that a module like this exist
in a submodule called "templatetags" of a registered app.

Moreover, the module has to have a "register" attribute of type
django.template.Library().

"""

import logging
from pprint import pprint
import sys

from django import template

from pyelect.html.common import NON_ENGLISH_ORDER
from pyelect.html import pages
from pyelect import lang


_log = logging.getLogger()

register = template.Library()


# This is a decorator to deal with the fact that by default Django silently
# swallows exceptions.
def log_errors(func):
    def wrapper(context, label, object_id, type_name):
        try:
            return func(context, label, object_id, type_name)
        except Exception as err:
            _log.warn("exception: {0}".format(err))
            raise
    return wrapper

def _pprint(text):
    pprint(text, stream=sys.stderr)


def get_page_href(page_base):
    page = pages.get_page_object(page_base)
    href = page.make_href()
    return href


def get_page_title(page_base):
    page = pages.get_page_object(page_base)
    title = page.title
    return title


@register.simple_tag(takes_context=True)
def current_object_count(context):
    current_page_base = context['current_page']
    page_title = get_page_title(current_page_base)
    return page_title


@register.inclusion_tag('tags/page_nav.html', takes_context=True)
def page_nav(context, page_base):
    """A tag to use in site navigation."""
    current_page_base = context['current_page']
    data = {
        'page_href': get_page_href(page_base),
        'page_title': get_page_title(page_base),
        'same_page': page_base == current_page_base
    }

    return data


@register.inclusion_tag('anchor.html')
def anchor(id_):
    return {
        'id': id_
    }


def _header_context(item_data, field_name, item_id):
    name = item_data[field_name]
    i18n_field_name = lang.get_i18n_field_name(field_name)
    translations = item_data.get(i18n_field_name, {})
    non_english = [translations[lang] for lang in NON_ENGLISH_ORDER if lang in translations]
    return {
        'header': name,
        'header_non_english': non_english,
        'header_id': item_id,
    }


@register.inclusion_tag('header_section.html')
def header_section(item_data, field_name, item_id):
    return _header_context(item_data, field_name, item_id)


@register.inclusion_tag('header_item.html')
def header_item(item_data, field_name, item_id):
    return _header_context(item_data, field_name, item_id)


@register.inclusion_tag('tags/cond_include.html')
def cond_include(should_include, template_name, data):
    """A tag to conditionally include a template."""
    return {
        'should_include': should_include,
        'template_name': template_name,
        'data': data,
    }


def _cond_include_context(template_name, header, value):
    return {
        'header': header,
        'should_include': value is not None,
        'template_name': template_name,
        'value': value,
    }


def _cond_include_context_url(label, href, href_text=None):
    if href_text is None:
        href_text = href
    return {
        'header': label,
        'should_include': href is not None,
        'template_name': 'partials/row_url.html',
        'href': href,
        'href_text': href_text,
    }


@register.inclusion_tag('tags/cond_include.html')
def info_row(header, value):
    return _cond_include_context('partials/row_simple.html', header, value)


@register.inclusion_tag('tags/cond_include.html')
def url_row(header, value):
    return _cond_include_context_url(header, value)


# The name argument is necessary because of this issue:
#   https://code.djangoproject.com/ticket/24586
@register.inclusion_tag('tags/cond_include.html', takes_context=True, name='url_row_object')
@log_errors
def url_row_object(context, label, object_id, type_name):
    """
    Arguments:
      type_name: for example, "languages".
    """
    if object_id is not None:
        context = context['_context']
        objects = context[type_name]
        obj = objects[object_id]
        name = obj['name']
        page = pages.get_page_object(type_name)
        href = page.make_href(object_id)
    else:
        href = None

    return _cond_include_context_url(label, href, href_text=name)


@register.inclusion_tag('list_objects.html', takes_context=True)
def list_objects(context, objects, title_attr):
    return {
        '_context': context,
        'current_show_template': context['current_show_template'],
        'objects': objects,
        'title_attr': title_attr
    }
