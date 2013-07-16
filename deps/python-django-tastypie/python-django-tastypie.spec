%global pypi_name django-tastypie
Name:           python-%{pypi_name}
Version:        0.9.14
Release:        2%{?dist}
Summary:        A flexible and capable API layer for Django

Group:          Development/Languages
License:        BSD
URL:            https://github.com/toastdriven/django-tastypie/

# Release version doesn't include tests
Source0:        http://pypi.python.org/packages/source/d/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
# To get version with tests (last commit in tag v0.9.14):
%global commit 19218ef73dee4d85b6ec87bf0d2b6293da79758e
%global shortcommit %(c=%{commit}; echo ${c:0:7})
Source1:        https://github.com/toastdriven/%{pypi_name}/archive/%{commit}/%{pypi_name}-%{version}-github.tar.gz

# Patch so this works with Django 1.5
Patch0:         %{name}-django-1.5.patch

%global docdir %{_docdir}/%{name}-%{version}

BuildArch:      noarch
# Let's keep Requires and BuildRequires sorted alphabetically
BuildRequires:  python2-devel
%if 0%{?rhel}
BuildRequires:  python-dateutil
%else
BuildRequires:  python-dateutil >= 1.5
BuildRequires:  python-dateutil < 2.0
%endif
%if 0%{?fedora} >= 18
BuildRequires:  python-django >= 1.2.0
%else
BuildRequires:  Django >= 1.2.0
%endif
BuildRequires:  python-defusedxml
BuildRequires:  python-lxml
BuildRequires:  python-mimeparse >= 0.1.3
BuildRequires:  python-mock
BuildRequires:  python-setuptools
BuildRequires:  python-sphinx
BuildRequires:  PyYAML

%if 0%{?rhel}
Requires:       python-dateutil15
# also require setuptools to be able to use 'require' function from pkg_resources module
Requires:       python-setuptools
%else
Requires:       python-dateutil >= 1.5
Requires:       python-dateutil < 2.0
%endif
%if 0%{?fedora} >= 18
Requires:       python-django >= 1.2.0
%else
Requires:       Django >= 1.2.0
%endif
Requires:       python-mimeparse >= 0.1.3

Provides:       %{pypi_name} = %{version}-%{release}
Obsoletes:      %{pypi_name} < 0.9.11-3 

%description
Tastypie is an webservice API framework for Django. It provides a convenient, 
yet powerful and highly customizable, abstraction for creating REST-style 
interfaces.

%package doc
Summary: Documentation for %{name}
Group: Documentation

Requires: %{name} = %{version}-%{release}

%description doc
This package contains documentation for %{name}.


%prep 
%setup -qb1 -n %{pypi_name}-%{commit}
%setup -q -n %{pypi_name}-%{version}
%patch0 -p1
cp -r ../%{pypi_name}-%{commit}/tests .
# (re)generate the documentation
sphinx-build docs docs/_build/html

# if on RHEL, using dateutils15, we need to alter __init__.py to load them properly
%if 0%{?rhel}
cat << 'EOF' >> tastypie/__init__.py
from pkg_resources import require
require('python-dateutil')
EOF
%endif

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{docdir}
cp -p LICENSE README.rst AUTHORS -t $RPM_BUILD_ROOT%{docdir}
cp -pr docs/_build/html -t $RPM_BUILD_ROOT%{docdir}

%check
# note: the oauth tests will work once the proper module gets into rawhide
# from the authors documentation it is now not very clear if it is
# django-oauth or django-oauth-provider or django-oauth-plus
# anyway, it is not a hard requirement
# also, the gis tests need a running postgresql server, so they are skipped
# run_all_tests.sh is no longer used, following commands are copied from tox.ini
pushd tests
# handle building on hosts with bad DNS
find -type f -name '*.py' -print | xargs sed -i 's|localhost|127.0.0.1|'
PYTHONPATH=$PWD:$PWD/..${PYTHONPATH:+:$PYTHONPATH}
export PYTHONPATH
#django-admin test core --settings=settings_core
django-admin test basic --settings=settings_basic
django-admin test complex --settings=settings_complex
django-admin test alphanumeric --settings=settings_alphanumeric
django-admin test slashless --settings=settings_slashless
django-admin test namespaced --settings=settings_namespaced
django-admin test related_resource --settings=settings_related
django-admin test validation --settings=settings_validation
django-admin test content_gfk --settings=settings_content_gfk
popd
 
%files
%doc README.rst AUTHORS LICENSE
%dir %{python_sitelib}/tastypie
%{python_sitelib}/django_tastypie*
%{python_sitelib}/tastypie/*

%files doc
%doc %{docdir}
# %%exclude %{docdir}/html/.*

%changelog
* Wed Jun 05 2013 John Matthews <jwmatthews@gmail.com> 0.9.14-2
- Removed older files from python-django-tastypie 0.9.12 (jwmatthews@gmail.com)
- Upgrade python-django-tastypie to 0.9.14 (jwmatthews@gmail.com)

* Tue Mar 26 2013 Miro Hrončok <mhroncok@redhat.com> - 0.9.14-1
- New version
- Using new GitHub rule to get archive with tests
- Run tests manually
- Added BR python-defusedxml
- Dropped dance around release and development versioning
- Added patch for Django 1.5

* Mon Mar 25 2013 Cédric OLIVIER <cedric.olivier@free.fr> 0.9.12-1
- Updated to upstream 0.9.12

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.9.12-0.2.alpha
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Aug 14 2012 Bohuslav Kabrda <bkabrda@redhat.com> - 0.9.12-0.1.alpha
- Updated to upstream version 0.9.12-alpha.
- Adapted the specfile to prerelease versioning.
- Add some BuildRequires, so that more tests are run (these
are soft requirements, so they aren't in Requires)
- Fixed URL to point to upstream, not PyPI.
- Made the spec compatible with EPEL6.

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.9.11-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sun Mar 18 2012 Cédric OLIVIER <cedric.olivier@free.fr> 0.9.11-4
- Bugfix in obsoletes

* Sun Mar 18 2012 Cédric OLIVIER <cedric.olivier@free.fr> 0.9.11-3
- Removing bundled .egg-info during prep

* Sat Mar 17 2012 Cédric OLIVIER <cedric.olivier@free.fr> 0.9.11-2
- Adding missing buildrequires
- Adding info about renaming django-tastypie
- Adding check section
- Adding documentation subpackage

* Wed Mar 02 2012 Cédric OLIVIER <cedric.olivier@free.fr> 0.9.11-1
- Initial version of the package
