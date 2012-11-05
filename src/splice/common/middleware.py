# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

# These middleware classes aid development/debugging/testing, they are not needed for production deployments

# StandardExceptionMiddleware
# modified from: http://djangosnippets.org/snippets/638/

# ProfileMiddleware from blogpost below
# http://gun.io/blog/fast-as-fuck-django-part-1-using-a-profiler/
# https://raw.github.com/gist/3649773/72e73609e67f70faaa31c73f25911ba15e384d54/middleware.py
# -------

# Orignal version taken from http://www.djangosnippets.org/snippets/186/
# Original author: udfalkso
# Modified by: Shwagroo Team and Gun.io

import logging
import os
import re
import sys
import hotshot, hotshot.stats
import tempfile
import StringIO

from django import http
from django.conf import settings

_LOG = logging.getLogger(__name__)


import traceback

#http://djangosnippets.org/snippets/1731/
class WsgiLogErrors(object):
    def process_exception(self, request, exception):
        import epdb; epdb.st()  
        tb_text = traceback.format_exc()
        url = request.build_absolute_uri()
        request.META['wsgi.errors'].write(url + '\n' + str(tb_text) + '\n')


# Temporary, from http://code.djangoproject.com/attachment/ticket/6094/6094.2008-02-01.diff
from django.core.urlresolvers import RegexURLResolver
def resolver(request):
    """
    Returns a RegexURLResolver for the request's urlconf.

    If the request does not have a urlconf object, then the default of
    settings.ROOT_URLCONF is used.
    """
    from django.conf import settings
    urlconf = getattr(request, "urlconf", settings.ROOT_URLCONF)
    return RegexURLResolver(r'^/', urlconf)


class StandardExceptionMiddleware(object):
    def process_exception(self, request, exception):
        # Get the exception info now, in case another exception is thrown later.
        if isinstance(exception, http.Http404):
            return self.handle_404(request, exception)
        else:
            return self.handle_500(request, exception)


    def handle_404(self, request, exception):
        if settings.DEBUG:
            from django.views import debug
            return debug.technical_404_response(request, exception)
        else:
            callback, param_dict = resolver(request).resolve404()
            return callback(request, **param_dict)


    def handle_500(self, request, exception):
        exc_info = sys.exc_info()
        if settings.DEBUG:
            self.log_exception(request, exception, exc_info)
            return self.debug_500_response(request, exception, exc_info)
        else:
            self.log_exception(request, exception, exc_info)
            return self.production_500_response(request, exception, exc_info)


    def debug_500_response(self, request, exception, exc_info):
        from django.views import debug
        return debug.technical_500_response(request, *exc_info)


    def production_500_response(self, request, exception, exc_info):
        '''Return an HttpResponse that displays a friendly error message.'''
        callback, param_dict = resolver(request).resolve500()
        return callback(request, **param_dict)


    def log_exception(self, request, exception, exc_info):
        _LOG.exception("Middleware caught exception: ", exception)
        sys.stderr.write("%s\n" % (self._get_traceback(exc_info)))
        sys.stderr.flush()

    def _get_traceback(self, exc_info=None):
        """Helper function to return the traceback as a string"""
        import traceback
        return ''.join(traceback.format_exception(*(exc_info or sys.exc_info())))




words_re = re.compile( r'\s+' )

group_prefix_re = [
    re.compile( "^.*/django/[^/]+" ),
    re.compile( "^(.*)/[^/]+$" ), # extract module path
    re.compile( ".*" ),           # catch strange entries
]

class ProfileMiddleware(object):
    """
    Displays hotshot profiling for any view.
    http://yoursite.com/yourview/?prof

    Add the "prof" key to query string by appending ?prof (or &prof=)
    and you'll see the profiling results in your browser.
    It's set up to only be available in django's debug mode, is available for superuser otherwise,
    but you really shouldn't add this middleware to any production configuration.

    WARNING: It uses hotshot profiler which is not thread safe.
    """
    def process_request(self, request):
        if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
            self.tmpfile = tempfile.mktemp()
            self.prof = hotshot.Profile(self.tmpfile)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def get_group(self, file):
        for g in group_prefix_re:
            name = g.findall( file )
            if name:
                return name[0]

    def get_summary(self, results_dict, sum):
        list = [ (item[1], item[0]) for item in results_dict.items() ]
        list.sort( reverse = True )
        list = list[:40]

        res = "      tottime\n"
        for item in list:
            res += "%4.1f%% %7.3f %s\n" % ( 100*item[0]/sum if sum else 0, item[0], item[1] )

        return res

    def summary_for_files(self, stats_str):
        stats_str = stats_str.split("\n")[5:]

        mystats = {}
        mygroups = {}

        sum = 0

        for s in stats_str:
            fields = words_re.split(s);
            if len(fields) == 7:
                time = float(fields[2])
                sum += time
                file = fields[6].split(":")[0]

                if not file in mystats:
                    mystats[file] = 0
                mystats[file] += time

                group = self.get_group(file)
                if not group in mygroups:
                    mygroups[ group ] = 0
                mygroups[ group ] += time

        return "<pre>" +\
               " ---- By file ----\n\n" + self.get_summary(mystats,sum) + "\n" +\
               " ---- By group ---\n\n" + self.get_summary(mygroups,sum) +\
               "</pre>"

    def process_response(self, request, response):
        if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
            self.prof.close()

            out = StringIO.StringIO()
            old_stdout = sys.stdout
            sys.stdout = out

            stats = hotshot.stats.load(self.tmpfile)
            stats.sort_stats('time', 'calls')
            stats.print_stats()

            sys.stdout = old_stdout
            stats_str = out.getvalue()

            if response and response.content and stats_str:
                response.content = "<pre>" + stats_str + "</pre>"

            response.content = "\n".join(response.content.split("\n")[:40])

            response.content += self.summary_for_files(stats_str)

            os.unlink(self.tmpfile)

        return response
