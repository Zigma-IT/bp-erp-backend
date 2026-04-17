"""Router helpers for clearer DRF API roots.

Several apps in `MASTERS` use function-based endpoints for custom datatable
responses. `ExtendedDefaultRouter` lets those named URLs appear in the DRF API
root together with regular viewsets, which makes the module easier to inspect
and hand over to another developer.
"""

from collections import OrderedDict

from rest_framework.routers import DefaultRouter


class ExtendedDefaultRouter(DefaultRouter):
    """Expose additional named URLs alongside registered viewsets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_api_root_dict = OrderedDict()

    def get_api_root_view(self, api_urls=None):
        api_root_dict = OrderedDict()

        # Keep the normal router entries and append manually named function
        # routes so the browsable API root shows the full working surface area.
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = self.routes[0].name.format(basename=basename)

        api_root_dict.update(self.extra_api_root_dict)
        return self.APIRootView.as_view(api_root_dict=api_root_dict)
