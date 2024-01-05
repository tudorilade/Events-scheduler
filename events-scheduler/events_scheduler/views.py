from typing import Dict, Any

from django.views.generic import TemplateView

from events_scheduler.limiters import RateLimitedView


class HomePageTemplateView(RateLimitedView, TemplateView):
    """Home page Template View

    TemplateView for displaying the home page.
    """

    def get_context_data(self, **kwargs: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Collects context data for rendering the template.

        Args:
            **kwargs (dict): Keyword arguments to be added to the context.

        Returns:
            context (dict): The context data.
        """
        context: Dict[Any, Any] = super().get_context_data(**kwargs)
        return context
