from django.db.models import Q
from rest_framework.filters import BaseFilterBackend


class MyDjangoFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        search_param = request.query_params.get('search', None)
        if search_param is not None:
            search_fields = getattr(view, 'search_fields', [])
            if search_fields:
                filter_query = Q()
                for field in search_fields:
                    if search_param.lower() == 'null':
                        filter_query |= Q(**{field: None}) # search for null values
                    elif search_param == '':
                        filter_query |= Q(**{field: None}) # search for null values when presented with a whitespace
                    else:
                        filter_query |= Q(**{field + '__icontains': search_param})
                queryset = queryset.filter(filter_query)
                return queryset
        else:
            return queryset