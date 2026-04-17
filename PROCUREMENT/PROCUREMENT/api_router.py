"""Router helpers for clearer DRF API roots.

This project mixes router-based viewsets with function-based endpoints.
`ExtendedDefaultRouter` keeps the normal DRF router behavior and also lets
plain named URLs appear in the API root so frontend developers can discover
the important entry points from one place.
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

        # DefaultRouter only knows about registered viewsets. We also include
        # plain Django/DRF paths so the API root becomes a useful index page.
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = self.routes[0].name.format(basename=basename)

        api_root_dict.update(self.extra_api_root_dict)
        return self.APIRootView.as_view(api_root_dict=api_root_dict)
