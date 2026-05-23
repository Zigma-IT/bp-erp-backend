"""
Router helpers for cleaner DRF API root.
"""

from collections import OrderedDict

from rest_framework.routers import DefaultRouter


class ExtendedDefaultRouter(DefaultRouter):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.extra_api_root_dict = OrderedDict()

    def get_api_root_view(self, api_urls=None):

        api_root_dict = OrderedDict()

        for prefix, viewset, basename in self.registry:

            api_root_dict[prefix] = self.routes[0].name.format(
                basename=basename
            )

        api_root_dict.update(self.extra_api_root_dict)

        return self.APIRootView.as_view(
            api_root_dict=api_root_dict
        )