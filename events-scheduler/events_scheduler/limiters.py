from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
from django_ratelimit.decorators import ratelimit


@method_decorator(ratelimit(key='ip', rate=settings.REQUEST_RATE, block=True), name='dispatch')
class RateLimitedView(View):
    """
    A Django view that applies rate limiting to all incoming requests.

    This view applies a ratelimit of REQUEST_RATE per IP on dispatch method. If the REQUEST_RATE is overreached,
    the ip will be blocked and wait until next hour starts.

    If you inherit another generic view which inherits View class, place RateLimitedView as the first class to inherit.
    Example:
    ```
    class SomeOtherView(RateLimitedView, OtherInheritedView):
        # your code here
    ```
    """
    pass
