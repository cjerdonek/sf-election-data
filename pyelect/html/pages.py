"""Supports per-page template context."""

from pprint import pprint


def get_page_name_parts(page_base):
    parts = page_base.split('_')
    return parts


def get_default_page_title(page_base):
    parts = get_page_name_parts(page_base)
    title = " ".join(p.title() for p in parts)
    return title


def get_page_object(page_base):
    parts = get_page_name_parts(page_base)
    prefix = "".join(p.title() for p in parts)
    cls_name = "{0}Page".format(prefix)
    page_class = globals()[cls_name]
    page = page_class(page_base)
    return page


class _Page(object):

    _title = None
    _objects_name = None
    singular = None

    @property
    def objects_name(self):
        return self._objects_name or self.page_base_name

    @property
    def title(self):
        title = self._title
        if title is None:
            title = get_default_page_title(self.objects_name)
        return title

    def __init__(self, page_base):
        self.page_base_name = page_base

    def make_href(self, object_id=None):
        url = "{0}.html".format(self.page_base_name)
        if object_id is not None:
            url += "#{0}".format(object_id)
        return url

    def get_singular(self):
        if self.singular is not None:
            return self.singular
        # Otherwise, remove the final "s".
        return self.objects_name[:-1]

    def get_objects(self, data):
        objects_name = self.objects_name
        objects = data[objects_name]
        return objects

    def get_show_template(self):
        """Return the name of the template that shows one instance."""
        singular = self.get_singular()
        return "show_{0}.html".format(singular)


class AreasPage(_Page):
    pass


class BodiesPage(_Page):
    singular = 'body'
    title = "Bodies"


class DistrictTypesPage(_Page):
    pass


class ElectionMethodsPage(_Page):
    pass


class IndexPage(_Page):
    _objects_name = 'offices'


class LanguagesPage(_Page):
    pass


class PhrasesPage(_Page):
    _title = "Translated Phrases"
