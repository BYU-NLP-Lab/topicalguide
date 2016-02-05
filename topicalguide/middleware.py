
import visualize
from topicalguide import settings

class ABTestMiddleware(object):

    def process_request(self, request):

        if not settings.ABTEST and not view == visualize.root.root:
            return None
        print request

        request.extra_attrs = {}
        request.extra_attrs['hi'] = 'there'

        return None
