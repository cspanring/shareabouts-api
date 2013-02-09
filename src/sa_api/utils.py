import time
from djangorestframework import status


def isiterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return True


def to_wkt(orig):
    """
    Given a dict, convert 'lat' and 'lng' keys to a WKT POINT.
    Given a string, return it.
    """
    if isinstance(orig, basestring):
        # assume it's already WKT
        return orig
    if isiterable(orig) and 'lat' in orig and 'lng' in orig:
        # Raises TypeError if orig isn't a mapping
        return 'POINT ({lng} {lat})'.format(**orig)
    else:
        raise TypeError("to_wkt should take a mapping or string, not %s"
                        % type(orig))


def unpack_data_blob(data):
    """
    Input is a mapping.  Find a key named 'data', decode it as a JSON
    blob, and merge the result into the mapping (in place; returns
    None).
    """
    import ujson as json
    from djangorestframework.response import ErrorResponse

    # Don't let the CSRF middleware token muck up our data.
    if 'csrfmiddlewaretoken' in data:
        del data['csrfmiddlewaretoken']

    # Handle the JSON data blob submitted through a form.
    if 'data' in data:
        try:
            data_blob = json.loads(data['data'])
        except ValueError:
            raise ErrorResponse(
                status.HTTP_400_BAD_REQUEST,
                {'detail': 'data blob must be a valid JSON object string'})

        if not isinstance(data_blob, dict):
            raise ErrorResponse(
                status.HTTP_400_BAD_REQUEST,
                {'detail': 'data blob must be a valid JSON object string'})

        del data['data']
        data.update(data_blob)


def cached_method(f):
    @wraps(f)
    def get(self, *args, **kwargs):
        key = (f, args, tuple(kwargs.items()))
        try:
            return self._method_cache[key]
        except AttributeError:
            self._method_cache = {}
            x = self._method_cache[key] = f(self, *args, **kwargs)
            return x
        except KeyError:
            x = self._method_cache[key] = f(self, *args, **kwargs)
            return x

    return get


def cached_property(f):
    """
    Returns a cached property that is calculated by function f.  Lifted from
    http://code.activestate.com/recipes/576563-cached-property/

    f cannot take arguments except 'self' (the object on which to
    store the cache, permanently).
    """
    def get(self):
        try:
            return self._property_cache[f]
        except AttributeError:
            self._property_cache = {}
            x = self._property_cache[f] = f(self)
            return x
        except KeyError:
            x = self._property_cache[f] = f(self)
            return x

    return property(get)


def base62_time():
    """
    Convert the current epoch time in milliseconds to a base-64 encoded string.
    """
    ms = int(time.time() * 1000)
    return to_base(ms, 62)


def to_base(num, base):
    """
    Convert an integer to a string in the given base, up to 62.
    """
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    digits = []
    while num > 0:
        num, remainder = divmod(num, base)
        digits.insert(0, alphabet[remainder])

    return ''.join(digits)
