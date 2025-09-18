import django_filters
from .models import Car


class CarFilter(django_filters.FilterSet):
    # Qiymət filtri
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr='lte')

    # İl filtri
    year_min = django_filters.NumberFilter(field_name="year", lookup_expr='gte')
    year_max = django_filters.NumberFilter(field_name="year", lookup_expr='lte')

    # Kilometr filtri
    mileage_max = django_filters.NumberFilter(field_name="mileage", lookup_expr='lte')
    mileage_min = django_filters.NumberFilter(field_name="mileage", lookup_expr='gte')

    # Sabit seçimlər - case insensitive
    fuel_type = django_filters.CharFilter(lookup_expr='iexact')
    transmission = django_filters.CharFilter(lookup_expr='iexact')
    condition = django_filters.CharFilter(lookup_expr='iexact')

    # Kateqoriya - həm ID, həm ad dəstəyi
    category = django_filters.CharFilter(field_name="category__id", lookup_expr='exact')
    category_name = django_filters.CharFilter(field_name="category__name", lookup_expr='icontains')

    # Rəng filtri
    color = django_filters.CharFilter(lookup_expr='icontains')

    # Mühərrik həcmi
    engine_size = django_filters.NumberFilter()
    engine_size_min = django_filters.NumberFilter(field_name="engine_size", lookup_expr='gte')
    engine_size_max = django_filters.NumberFilter(field_name="engine_size", lookup_expr='lte')

    # Məhsul adı üçün axtarış (ÖNƏMLİ - bu çox istifadə olunur)
    title = django_filters.CharFilter(field_name="title", lookup_expr='icontains')
    search = django_filters.CharFilter(field_name="title", lookup_expr='icontains')

    # Təsvir axtarışı
    description = django_filters.CharFilter(field_name="description", lookup_expr='icontains')

    # Nömrə axtarışı
    number = django_filters.CharFilter(field_name="number", lookup_expr='icontains')

    # Satıcı filtri
    seller = django_filters.CharFilter(field_name="seller__username", lookup_expr='icontains')
    seller_id = django_filters.NumberFilter(field_name="seller__id")

    class Meta:
        model = Car
        fields = [
            'fuel_type', 'transmission', 'condition', 'category',
            'color', 'engine_size', 'is_sold', 'seller'
        ]