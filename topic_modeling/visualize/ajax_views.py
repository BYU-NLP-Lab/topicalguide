
import functools
from 

class Router:
    def __init__(self, prefix):
        self.prefix = prefix
        self.urls = []

    def reg(self, url, ajax=True, replace=True):
        def wrap(fn):
            if ajax:
                @functools.wraps(fn)
                def meta(request, *args, **kwds):
                    try:
                        res = fn(request, *args, **kwds)
                    except Exception as e:
                        res = {'error': str(e)}
                    if isinstance(res, (dict, list, tuple, int)):
                        res = json.dumps(res)
                        return HttpResponse(res, mimetype='text/javascript')
                    else:
                        return res
                self.urls.append(url(self.prefix + url, meta))
                if replace:
                    return meta
                return fn
            else:
                self.urls.append(url(self.prefix + url, fn))
                return fn
        return wrap

router = Router('^ajax/')

