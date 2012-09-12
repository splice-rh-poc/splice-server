%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?pyver: %define pyver %(%{__python} -c "import sys ; print sys.version[:5]")}

# Tests requiring Internet connections are disabled by default
# pass --with internet to run them (e.g. when doing a local rebuild
# for sanity checks before committing)
%bcond_with internet

Name:           Django
Version:        1.4.1
Release:        5%{?dist}.splice
Summary:        A high-level Python Web framework

Group:          Development/Languages
License:        BSD
URL:            http://www.djangoproject.com/
Source0:        http://pypi.python.org/packages/source/D/Django/Django-%{version}.tar.gz
Source1:        simplejson-init.py
# patch tests to skip tests requiring internet connection
Patch0:         Django-1.4-no-internet-connection-tests.patch
# patch tests to relax performance scalability requirements
Patch1:         Django-1.4-relax-scalability-req.patch
# patch uses python-sphinx10 pkg, opposed to sphinx 0.6 which is default on rhel
Patch2:         Django-1.4-sphinx10.patch


%if 0%{?rhel} <= 5
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
%endif

BuildArch:      noarch
# Note: No longer required in development version > 0.95
# BuildRequires:  python-setuptools
BuildRequires:  python-devel
%if 0%{?rhel} > 4 || 0%{?fedora} > 12
BuildRequires:  python-sphinx10
%endif
# for testing
BuildRequires:  python-simplejson

Requires:       python-simplejson


%description
Django is a high-level Python Web framework that encourages rapid
development and a clean, pragmatic design. It focuses on automating as
much as possible and adhering to the DRY (Don't Repeat Yourself)
principle.

%if 0%{?rhel} > 4 || 0%{?fedora} >= 12
%package doc
Summary:        Documentation for Django
Group:          Documentation
Requires:       %{name} = %{version}-%{release}
Provides:       %{name}-docs = %{version}-%{release}
Obsoletes:      %{name}-docs < %{version}-%{release}

%description doc
This package contains the documentation for the Django high-level
Python Web framework.
%endif

%prep
%setup -q 
%if ! %{with internet}
# patch tests to skip tests requiring internet connection
%patch0 -p1 -b .no-internet-connection-tests
%endif
# patch tests to relax performance scalability requirements
%patch1 -p1 -b .relax-scalability-req
%patch2 -p1 -b .sphinx10-usage

# empty files
for f in \
    django/contrib/humanize/models.py \
    django/contrib/markup/models.py \
    django/contrib/staticfiles/models.py \
    django/contrib/webdesign/models.py \
; do
  echo "# just a comment" > $f
done
echo "<!-- nothing -->" > django/contrib/flatpages/tests/templates/registration/login.html

# remove bundled simplejson (for tests)
cd django/utils/simplejson
rm -rf *
# and put the replacement stub in place
cp -p %{SOURCE1} __init__.py


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT

%if 0%{?rhel} > 6 || 0%{?fedora} >= 16
%find_lang django
%find_lang djangojs
# append djangojs.lang to django.lang
cat djangojs.lang >> django.lang

%else

# Handling locale files
# This is adapted from the %%find_lang macro, which cannot be directly
# used since Django locale files are not located in %%{_datadir}
#
# The rest of the packaging guideline still apply -- do not list
# locale files by hand!
(cd $RPM_BUILD_ROOT && find . -name 'django*.mo') | %{__sed} -e 's|^.||' |
%{__sed} -e \
   's:\(.*/locale/\)\([^/_]\+\)\(.*\.mo$\):%lang(\2) \1\2\3:' \
      >> django.lang
%endif

# If it's rhel5+ or any Fedora over 12 build docs
%if 0%{?rhel} > 4 || 0%{?fedora} >= 12
    # build documentation
    (cd docs && mkdir djangohtml && mkdir -p _build/{doctrees,html} && make html)
%endif


# install man pages
mkdir -p $RPM_BUILD_ROOT%{_mandir}/man1/
cp -p docs/man/* $RPM_BUILD_ROOT%{_mandir}/man1/

# install bash completion script
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/bash_completion.d/
install -m 0644 -p extras/django_bash_completion \
   $RPM_BUILD_ROOT%{_sysconfdir}/bash_completion.d/

# Fix items in %%{_bindir}
mv $RPM_BUILD_ROOT%{_bindir}/django-admin.py $RPM_BUILD_ROOT%{_bindir}/django-admin

# remove .po files
find $RPM_BUILD_ROOT -name "*.po" | xargs rm -f

# Fix permissions
chmod +x \
  $RPM_BUILD_ROOT%{python_sitelib}/django/contrib/admin/static/admin/js/compress.py \
  $RPM_BUILD_ROOT%{python_sitelib}/django/bin/profiling/gather_profile_stats.py

# test section
%check
export PYTHONPATH=$(pwd)
export LANG=en_US.utf8
#cd tests
#./runtests.py --settings=test_sqlite

%clean
rm -rf $RPM_BUILD_ROOT


%files -f django.lang
%defattr(-,root,root,-)
%doc AUTHORS LICENSE README
%{_bindir}/django-admin
%{_mandir}/man1/*
%attr(0755,root,root) %{python_sitelib}/django/bin/*-messages.py*
%attr(0755,root,root) %{python_sitelib}/django/bin/daily_cleanup.py*
%attr(0755,root,root) %{python_sitelib}/django/bin/django-admin.py*
%dir %{_sysconfdir}/bash_completion.d/
%config(noreplace) %{_sysconfdir}/bash_completion.d/django_bash_completion
%{python_sitelib}/django/bin/profiling/
%{python_sitelib}/django/bin/__init__.py*
# Include everything but the locale data ...
%dir %{python_sitelib}/django/
%{python_sitelib}/django/db/
%{python_sitelib}/django/*.py*
%{python_sitelib}/django/shortcuts/
%{python_sitelib}/django/utils/
%{python_sitelib}/django/dispatch/
%{python_sitelib}/django/template/
%{python_sitelib}/django/views/
%dir %{python_sitelib}/django/contrib/
%{python_sitelib}/django/contrib/*.py*
%dir %{python_sitelib}/django/contrib/admin/
%{python_sitelib}/django/contrib/admin/static/
%dir %{python_sitelib}/django/contrib/admindocs/
%dir %{python_sitelib}/django/contrib/auth/
%dir %{python_sitelib}/django/contrib/comments/
%dir %{python_sitelib}/django/contrib/contenttypes/
%dir %{python_sitelib}/django/contrib/databrowse/
%dir %{python_sitelib}/django/contrib/flatpages/
%dir %{python_sitelib}/django/contrib/formtools/
%{python_sitelib}/django/contrib/formtools/wizard/
%dir %{python_sitelib}/django/contrib/gis/
%{python_sitelib}/django/contrib/gis/geoip/
%dir %{python_sitelib}/django/contrib/humanize/
%dir %{python_sitelib}/django/contrib/localflavor/
%dir %{python_sitelib}/django/contrib/markup/
%dir %{python_sitelib}/django/contrib/messages/
%dir %{python_sitelib}/django/contrib/redirects
%dir %{python_sitelib}/django/contrib/sessions/
%dir %{python_sitelib}/django/contrib/sitemaps/
%dir %{python_sitelib}/django/contrib/sites/
%dir %{python_sitelib}/django/contrib/staticfiles/
%dir %{python_sitelib}/django/contrib/syndication/
%dir %{python_sitelib}/django/contrib/webdesign/
%{python_sitelib}/django/contrib/*/*.py*
%{python_sitelib}/django/contrib/*/fixtures/
%{python_sitelib}/django/contrib/*/handlers/
%{python_sitelib}/django/contrib/*/management/
%{python_sitelib}/django/contrib/*/plugins/
%{python_sitelib}/django/contrib/*/templates/
%{python_sitelib}/django/contrib/*/templatetags/
%{python_sitelib}/django/contrib/*/tests/
%{python_sitelib}/django/contrib/*/views/
%{python_sitelib}/django/contrib/gis/admin/
%{python_sitelib}/django/contrib/gis/db/
%{python_sitelib}/django/contrib/gis/forms/
%{python_sitelib}/django/contrib/gis/gdal/
%{python_sitelib}/django/contrib/gis/geometry/
%{python_sitelib}/django/contrib/gis/geos/
%{python_sitelib}/django/contrib/gis/maps/
%{python_sitelib}/django/contrib/gis/sitemaps/
%{python_sitelib}/django/contrib/gis/utils/
%{python_sitelib}/django/contrib/localflavor/??/
%{python_sitelib}/django/contrib/localflavor/??_??/
%{python_sitelib}/django/contrib/localflavor/generic/
%{python_sitelib}/django/contrib/localflavor/in_/
%{python_sitelib}/django/contrib/localflavor/is_/
%{python_sitelib}/django/contrib/messages/storage/
%{python_sitelib}/django/contrib/sessions/backends/
%{python_sitelib}/django/forms/
%{python_sitelib}/django/templatetags/ 
%{python_sitelib}/django/core/
%{python_sitelib}/django/http/
%{python_sitelib}/django/middleware/
%{python_sitelib}/django/test/
%{python_sitelib}/django/conf/*.py*
%{python_sitelib}/django/conf/project_template/
%{python_sitelib}/django/conf/app_template/
%{python_sitelib}/django/conf/urls/
%{python_sitelib}/django/conf/locale/*/*.py*
%{python_sitelib}/django/conf/locale/*.py*

# Leaving these since people may want to rebuild on lower dists
%if 0%{?fedora} >= 9 || 0%{?rhel} >= 6
%{python_sitelib}/*.egg-info
%endif

%if 0%{?fedora} > 0 && 0%{?fedora} <= 9
%ghost %{_bindir}/django-admin.pyc
%ghost %{_bindir}/django-admin.pyo
%endif
# -----------------
 

%if 0%{?rhel} > 4 || 0%{?fedora} >= 12
%files doc
%defattr(-,root,root,-)
%doc docs/_build/html/*
%endif


%changelog
* Wed Sep 12 2012 John Matthews <jmatthews@redhat.com> 1.4.1-5.splice
- Problem with running unit tests from this RPM build, commenting out for now
  (jmatthews@redhat.com)

* Wed Sep 12 2012 John Matthews <jmatthews@redhat.com> 1.4.1-4.splice
- Update Django-1.4.1.tar.gz to match django's git branch for 1.4.1
  (jmatthews@redhat.com)

* Wed Sep 12 2012 John Matthews <jmatthews@redhat.com> 1.4.1-3.splice
- new package built with tito

* Wed Sep 12 2012 John Matthews <jmatthews@redhat.com> 1.4.1-2
- update for rhel6, build requires python-sphinx10

* Wed Aug 01 2012 Alan Pevec <apevec@redhat.com> 1.4.1-1
- security release
  https://www.djangoproject.com/weblog/2012/jul/30/security-releases-issued/
  fixes CVE-2012-3442 CVE-2012-3443 CVE-2012-3444

* Wed May 30 2012 Matthias Runge <mrunge@matthias-runge.de> - 1.4-3
- fix for FTBFS using python 2.7.3 (thanks to  M.Cepl)

* Sun Apr 01 2012 Matthias Runge <mrunge@matthias-runge.de> - 1.4-2
- include forgotten %%bcond_with internet
- fix language handling for el6

* Wed Mar 27 2012 Matthias Runge <mrunge@matthias-runge.de> - 1.4-1
- Update to 1.4
- backport simplejson-import from python-django package

* Mon Mar 19 2012 Matthias Runge <mrunge@matthias-runge.de> - 1.3.1-9
- spec cleanup

* Sat Mar 17 2012 Matthias Runge <mrunge@matthias-runge.de> - 1.3.1-8
- patch tests to work on koji (no internet connection)

* Sat Mar 10 2012 Michel Salim <salimma@fedoraproject.org> - 1.3.1-7
- Enable tests
- Now obsoletes (last Django release+1)
- Mark Bash completion script as a configuration file

* Fri Mar 09 2012 Matthias Runge <mrunge@matthias-runge.de> - 1.3.1-6
- add additional provides django = %%{version}-%%{release}

* Wed Mar 07 2012 Matthias Runge <mrunge@matthias-runge.de> - 1.3.1-5
- rename package to python-django

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Oct 12 2011 Michel Salim <salimma@fedoraproject.org> - 1.3.1-3
- Package bash completion script

* Sat Sep 10 2011 Michel Salim <salimma@fedoraproject.org> - 1.3.1-2
- Switch to the 'html' doc builder, for easier navigation without a web server

* Sat Sep 10 2011 Michel Salim <salimma@fedoraproject.org> - 1.3.1-1
- Update to 1.3.1
- Remove workaround for non-functional -doc generation
- Deduplicate file listing

* Wed Mar 30 2011 Steve Milner <me@stevemilner.org> - 1.3-2
- Fix for BZ#693865

* Wed Mar 30 2011 Steve Milner <me@stevemilner.org> - 1.3-1
- Fix for es_MX upstream bug
- Update for upstream release

* Wed Feb  9 2011 Steve Milner <me@stevemilner.org> - 1.2.5-1
- Fix for CVE-2011-0697

* Mon Feb 07 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Jan  3 2011 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.2.4-1
- Update for multiple security issues (see http://www.djangoproject.com/weblog/2010/dec/22/security/)

* Sat Oct  9 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.2.3-3
- Now build docs for F12+
- Added Django-remove-djangodocs-ext.patch

* Sat Oct  9 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.2.3-2
- Moved to dirhtml for documentation generation

* Mon Sep 13 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.2.3-1
- Update for http://www.djangoproject.com/weblog/2010/sep/10/123/

* Thu Sep  9 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.2.2-1
- Update for CVE-2010-3082 (see http://www.djangoproject.com/weblog/2010/sep/08/security-release/)
- Removed Django-hash-compat-13310.patch as it is already included in this release

* Wed Jul 21 2010 David Malcolm <dmalcolm@redhat.com> - 1.2.1-6
- Rebuilt for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Tue Jun  8 2010 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.2.1-5
- Added http://code.djangoproject.com/changeset/13310?format=diff&new=13310 per BZ#601212

* Thu Jun  3 2010 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.2.1-4
- Include egg in >= rhel6

* Thu Jun  3 2010 Michel Salim <salimma@fedoraproject.org> - 1.2.1-3
- Use generated %%{name}.lang instead of including each locale file by hand
- Temporarily make main package provide -doc on Rawhide, to fix upgrade path
  until upstream documentation builds with Sphinx 1.0

* Thu May 27 2010 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.2.1-2
- Allow for building docs in F13 as it's only F14 freaking out

* Tue May 25 2010 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.2.1-1
- Update for new release.
- Added lang files per BZ#584866.
- Changed perms on %%{python_sitelib}/django/contrib/admin/media/js/compress.py
- Lots of explicit files listed in %%files in order to reduce duplicate file listings
- Docs are not built on F-13 for now

* Wed Oct 21 2009 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.1.1-2
- Removed po files per BZ#529188.

* Fri Oct  9 2009 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.1.1-1
- Update to fix http://www.djangoproject.com/weblog/2009/oct/09/security/
- Django-ignore-pyo-bz-495046.patch no longer needed.

* Wed Aug 26 2009 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.1-4
- EL-4 shouldn't get the sphinx docs.

* Wed Aug 26 2009 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.1-3
- ghosting admin py* is now FC9 and under.

* Thu Aug  6 2009 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.1-2
- Applied Daniel Mach's patch from bz#516016.

* Sat Aug  1 2009 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.1-1
- Update for Django 1.1 release.
- Moved /usr/bin/django-admin.py to /usr/bin/django-admin
- sed macro is now being used
- Patch for bz#495046 applied.

* Wed Jul 29 2009 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.0.3-6
- Attempted combined spec for F12/11/10 and EL5

* Wed Jul 29 2009 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.0.3-4
- Older builds must ghost django-admin.py[c,o]

* Wed Jul 29 2009 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.0.3-3
- Bump for tag issue.

* Wed Jul 29 2009 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.0.3-2
- Fix changelog.

* Wed Jul 29 2009 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.0.3-1
- Upgrade for http://www.djangoproject.com/weblog/2009/jul/28/security/

* Thu Mar 12 2009 Michel Salim <salimma@fedoraproject.org> - 1.0.2-3
- Build HTML documentation (bug #484070)
- No longer excluding *.py? in bindir, F11's Python does not optimizes these

* Mon Feb 23 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Sun Dec 14 2008 Michel Salim <salimma@fedoraproject.org> - 1.0.2-1
- Update to 1.0.2

* Sat Nov  1 2008 Steve 'Ashcrow' Milner <stevem@gnulinux.net> - 1.0.1-0.1.beta1
- Update to 1.0.1_beta_1

* Sat Sep  6 2008 Michel Salim <salimma@fedoraproject.org> - 1.0-1
- Update to final 1.0 release

* Tue Sep  2 2008 Michel Salim <salimma@fedoraproject.org> - 1.0-0.1.rc1%{?dist}
- CSRF security update: bz#460966

* Wed Aug 27 2008 Michel Salim <salimma@fedoraproject.org> - 1.0-0.1.beta2
- Update to 1.0 beta2

* Sat Aug 23 2008 Michel Salim <salimma@fedoraproject.org> - 1.0-0.1.beta1
- Update to 1.0 beta1

* Mon May 19 2008 Michel Salim <salimma@fedoraproject.org> - 0.96.2-1
- XSS security update: CVE-2008-2302 (bz# 442757-60)

* Sat Apr  5 2008 Michel Salim <salimma@fedoraproject.org> - 0.96.1-2
- Package .egg-info file on Fedora >= 9

* Thu Nov  1 2007 Michel Salim <michel.sylvan@gmail.com> 0.96.1-1
- i18n security update: CVE-2007-5712, bz#357051

* Sat Mar 24 2007 Michel Salim <michel.salim@gmail.com> - 0.96-1
- New upstream version

* Sun Jan 21 2007 Michel Salim <michel.salim@gmail.com> - 0.95.1-1
- Upstream security updates:
  http://www.djangoproject.com/weblog/2007/jan/21/0951/

* Sun Nov 12 2006 Michel Salim <michel.salim@gmail.com> - 0.95-1
- Initial package
