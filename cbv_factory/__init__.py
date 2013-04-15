__version__ = "0.1"

import warnings
from inspect import isfunction

from django.conf.urls import patterns, url
from django.views.generic import \
    CreateView, UpdateView, DeleteView, DetailView, ListView
from django.views.generic.edit import ModelFormMixin


def parse_func_dict(selfobj, d):
    """ Recursively goes through a dict, calling functions that refer
        to a view's self and therefore need to be called from within --
        such as getting extra kwargs for a form constructor based on
        request data. """
    e = d.copy()
    for i in e.keys():
        if isfunction(e[i]):
            e[i] = e[i](selfobj)
        elif isinstance(d[i], dict):
            e[i] = parse_func_dict(selfobj, e[i])
    return e


def cbv_factory(modelclass, **kwargs):
    """ For a given model, returns generic class-based ListView,
        DetailView, CreateView, UpdateView, DeleteView. """

    _queryset = kwargs.get('queryset', None)
    _form_class = kwargs.get('form_class', None)
    _extra_form_kwargs = kwargs.get('extra_form_kwargs', {})
    _extra_context = kwargs.get('extra_context', {})
    _form_template = kwargs.get('form_template', {})

    class FactoryObjectMixin(object):
        """ Common properties of all views.  """
        model = modelclass

        def get_context_data(self, **kwargs):
            d = super(FactoryObjectMixin, self).get_context_data(**kwargs)
            d.update(parse_func_dict(self, _extra_context))
            return d

    class FactoryFormMixin(ModelFormMixin):
        """ Common properties of form-based views (Create, Update). """
        if _form_class:
            form_class = _form_class
        if _form_template:
            template_name = _form_template

        def get_form_kwargs(self, **kwargs):
            d = super(FactoryFormMixin, self).get_form_kwargs(**kwargs)
            d.update(parse_func_dict(self, _extra_form_kwargs))
            return d

    class Detail(FactoryObjectMixin, DetailView): pass

    class List(FactoryObjectMixin, ListView):
        if _queryset:
            queryset = _queryset

    class Create(FactoryFormMixin, FactoryObjectMixin, CreateView): pass

    class Update(FactoryFormMixin, FactoryObjectMixin, UpdateView): pass

    class Delete(FactoryObjectMixin, DeleteView): pass

    return {
        'list': List,
        'detail': Detail,
        'create': Create,
        'update': Update,
        'delete': Delete
    }


def generate_urls(views, view_patterns):
    """ Generates URL patterns for the manufactured views. """
    url_patterns = []

    for modelname, modelviews in views.items():
        for viewname, pattern in view_patterns.items():
            try:
                view = modelviews[viewname]
            except KeyError:
                warnings.warn('No %s view for %s.' % (viewname, modelname))
                continue
            url_patterns += patterns(
                '',
                url(pattern % modelname.lower(),
                    view.as_view() if hasattr(view, 'as_view') else view,
                    name=('%s_%s') % (modelname.lower(), viewname.lower())))

    return url_patterns
