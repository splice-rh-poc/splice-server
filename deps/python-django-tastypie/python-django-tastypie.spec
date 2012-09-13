%global pkgname django-tastypie
%global docdir %{_docdir}/%{name}-%{version}

Name:           python-django-tastypie
Version:        0.9.12pre
Release:        3%{?dist}
Summary:        A flexible and capable API layer for Django

Group:          Development/Languages
License:        BSD
URL:            http://pypi.python.org/pypi/django-tastypie
Source0:        http://pypi.python.org/packages/source/d/django-tastypie/django-tastypie-%{version}.tar.gz
# to get tests:
# git clone https://github.com/toastdriven/django-tastypie.git && cd django-tastypie
# git checkout v0.9.11
# tar -czf python-django-tastypie-tests.tgz tests/
Source1:        %{name}-tests.tgz


BuildArch:      noarch
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
BuildRequires:  python-mimeparse >= 0.1.3
BuildRequires:  python-dateutil >= 1.5
BuildRequires:  python-dateutil < 2.0
BuildRequires:  Django >= 1.2.0
Requires:       python-mimeparse >= 0.1.3
Requires:       python-dateutil >= 1.5
Requires:       python-dateutil < 2.0
Requires:       Django >= 1.2.0

Provides:       %{pkgname} = %{version}-%{release}
Obsoletes:      %{pkgname} < 0.9.11-3 

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
%setup -q -n %{name}-%{version}
rm -rf *egg-info
tar xzf %{SOURCE1}
sed -i 's|django-admin.py|django-admin|' tests/run_all_tests.sh

%build
%{__python} setup.py build


%install
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{docdir}
cp -pr docs/_build/html $RPM_BUILD_ROOT%{docdir}
cp -p LICENSE README.rst AUTHORS -t $RPM_BUILD_ROOT%{docdir}

%check
# note: the oauth tests will work once the proper module gets into rawhide
# from the authors documentation it is now not very clear if it is
# django-oauth or django-oauth-provider or django-oauth-plus
# anyway, it is not a hard requirement

# Commenting out tests since we don't have this package, 'django-oauth' in el6
#pushd tests
#./run_all_tests.sh
#popd
 
%files
%doc README.rst AUTHORS LICENSE
%dir %{python_sitelib}/tastypie
%{python_sitelib}/django_tastypie*
%{python_sitelib}/tastypie/*

%files doc
%doc %{docdir}


%changelog
* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 0.9.12pre-3
- Spec update for python-django-tastypie (jmatthews@redhat.com)

* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 0.9.12pre-2
- Bump python-django-tastypie to latest version in master, labeling as
  0.9.12pre (jmatthews@redhat.com)

* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 0.9.11-7
- Remove unneeded exclude of .buildinfo for django-tastypie spec
  (jmatthews@redhat.com)

* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 0.9.11-6
- new package built with tito

* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com>
- new package built with tito

* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 0.9.11-5
- Rebuild for el6 and splice project

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
