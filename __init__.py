from inspect import isfunction
from django.views.generic import View, CreateView, UpdateView, DeleteView, DetailView
from django.views.generic.edit import ModelFormMixin
from django.views.generic.detail import SingleObjectMixin
from crunchy_lists.views import CrunchyListView
from crunchy_lists.fields import Field, Choice, Link

def parse_func_dict(selfobj, d):
	"""
	Recursively goes through a dict, calling functions that refer to a view's
	self and therefore need to be called from within -- such as getting extra
	kwargs for a form constructor based on request data.
	"""
	for i in d.keys():
		if isfunction(d[i]):
			d[i] = d[i](selfobj)
		elif isinstance(d[i],dict):
			d[i] = parse_func_dict(selfobj,d[i])
	return d

def cbv_factory(modelclass, **kwargs):
	"""
	For a given model, returns generic class-based CrunchyListView, DetailView,
	CreateView, UpdateView, DeleteView.
	"""
	_queryset = kwargs.get('queryset',None)
	_field_list = kwargs.get('field_list',None)
	_form_class = kwargs.get('form_class',None)
	_extra_context = kwargs.get('extra_context',{})
	_extra_form_kwargs = kwargs.get('extra_form_kwargs',{})

	class FactoryObjectMixin(SingleObjectMixin):
		"""
		Common properties of all views.
		"""
		model = modelclass
		if _queryset:
			queryset = _queryset
		def get_context_data(self, **kwargs):
			d = super(FactoryObjectMixin, self).get_context_data(**kwargs)
			d.update(parse_func_dict(self, _extra_context))
			return d

	class FactoryFormMixin(ModelFormMixin):
		"""
		Common properties of form-based views (Create, Update).
		"""
		template_name = 'form.html'
		if _form_class:
			form_class = _form_class
		def get_form_kwargs(self, **kwargs):
			d = super(FactoryFormMixin,self).get_form_kwargs(**kwargs)
			d.update(parse_func_dict(self, _extra_form_kwargs))
			return d

	class Detail(FactoryObjectMixin, DetailView):
		template_name = 'detail.html'

	class List(CrunchyListView):
		model = modelclass
		if _field_list:
			field_list = _field_list
		if _queryset:
			queryset = _queryset

	class Create(FactoryFormMixin, FactoryObjectMixin, CreateView):
		pass

	class Update(FactoryFormMixin, FactoryObjectMixin, UpdateView):
		pass

	class Delete(FactoryObjectMixin, DeleteView):
		pass

	return {
		'list':List,
		'detail':Detail,
		'create':Create,
		'update':Update,
		'delete':Delete
	}