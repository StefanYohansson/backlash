import os
from backlash.utils.wsgi import get_current_url, get_headers, get_environ

has_sdk = True 
try:
    import sentry_sdk
except ImportError:
    has_sdk = False 


class SentryReporter(object):
    def __init__(self, sentry_dsn, **unused):
        if not has_sdk:
            raise SentryNotAvailable('Sentry SDK is not installed, maybe run "pip install sentry_sdk"')

        sentry_traces_sample_rate = os.environ.get('SENTRY_TRACES_SAMPLE_RATE')
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=sentry_traces_sample_rate
        )

    def report(self, traceback):
        environ = traceback.context.get('environ', {})
        data = {
            'sentry.interfaces.Http': {
                'method': environ.get('REQUEST_METHOD'),
                'url': get_current_url(environ, strip_querystring=True),
                'query_string': environ.get('QUERY_STRING'),
                # TODO
                # 'data': environ.get('wsgi.input'),
                'headers': dict(get_headers(environ)),
                'env': dict(get_environ(environ)),
            }
        }

        with sentry_sdk.push_scope() as scope:
            is_backlash_event = getattr(traceback.exc_value, 'backlash_event', False)
            if is_backlash_event:
                # Just a Stack Dump request from backlash
                sentry_sdk.capture_message(traceback.exception, data=data,
                                           stack=traceback.frames)
            else:
                # This is a real crash
                sentry_sdk.capture_exception(traceback.exc_info, data)


class SentryNotAvailable(Exception):
    pass
