__version__ = "0.1"

from inspect import isfunction
from django.views.generic import \
    CreateView, UpdateView, DeleteView, DetailView, ListView
from django.views.generic.edit import ModelFormMixin


def parse_func_dict(selfobj, d):
    """
    Recursively goes through a dict, calling functions that refer to a view's
    self and therefore need to be called from within -- such as getting extra
    kwargs for a form constructor based on request data.
    """
    e = d.copy()
    for i in e.keys():
        if isfunction(e[i]):
            e[i] = e[i](selfobj)
        elif isinstance(d[i], dict):
            e[i] = parse_func_dict(selfobj, e[i])
    return e


def cbv_factory(modelclass, **kwargs):
    """
    For a given model, returns generic class-based ListView, DetailView,
    CreateView, UpdateView, DeleteView.
    """

    _create_class = kwargs.get('create_class', CreateView)
    _update_class = kwargs.get('update_class', UpdateView)
    _delete_class = kwargs.get('delete_class', DeleteView)
    _detail_class = kwargs.get('detail_class', DetailView)
    _list_class = kwargs.get('list_class', ListView)

    _queryset = kwargs.get('queryset', None)
    _form_class = kwargs.get('form_class', None)
    _extra_form_kwargs = kwargs.get('extra_form_kwargs', {})

    _extra_context = kwargs.get('extra_context', {})
    _list_extra_context = kwargs.get('list_extra_context', {})

    _list_template = kwargs.get('list_template', None)
    _form_template = kwargs.get('form_template', None)
    _detail_template = kwargs.get('detail_template', None)
    _delete_template = kwargs.get('delete_template', None)

    class FactoryObjectMixin(object):
        """
        Common properties of all views.
        """
        model = modelclass
        if _queryset:
            queryset = _queryset

        def get_context_data(self, **kwargs):
            d = super(FactoryObjectMixin, self).get_context_data(**kwargs)
            d.update(parse_func_dict(self, _extra_context))
            if issubclass(type(self), ListView):
                d.update(parse_func_dict(self, _list_extra_context))
            return d

    class FactoryFormMixin(ModelFormMixin):
        """
        Common properties of form-based views (Create, Update).
        """
        if _form_template:
            template_name = _form_template
        if _form_class:
            form_class = _form_class

        def get_form_kwargs(self, **kwargs):
            d = super(FactoryFormMixin, self).get_form_kwargs(**kwargs)
            d.update(parse_func_dict(self, _extra_form_kwargs))
            return d

    class Detail(FactoryObjectMixin, _detail_class):
        if _detail_template:
            template_name = _detail_template

    class List(FactoryObjectMixin, _list_class):
        if _list_template:
            template_name = _list_template

    class Create(FactoryFormMixin, FactoryObjectMixin, _create_class):
        pass

    class Update(FactoryFormMixin, FactoryObjectMixin, _update_class):
        pass

    class Delete(FactoryObjectMixin, _delete_class):
        if _delete_template:
            template_name = _delete_template

    return {
        'list': List,
        'detail': Detail,
        'create': Create,
        'update': Update,
        'delete': Delete
    }
