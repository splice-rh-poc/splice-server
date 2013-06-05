%global pkgname django-tastypie
%global docdir %{_docdir}/%{name}-%{version}

Name:		python-django-tastypie-mongoengine
Version:	0.2.3
Release:	4%{?dist}
Summary:	MongoEngine support for django-tastypie.

Group:		Development/Languages
License:	GPLv3+
URL:		https://github.com/mitar/django-tastypie-mongoengine
Source0:	%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:	python2-devel
BuildRequires:  python-setuptools
Requires:	    python-django-tastypie
Requires:       Django
Requires:       python-mongoengine

%description
MongoEngine support for django-tastypie.


%package doc
Summary: Documentation for %{name}
Group: Documentation

Requires: %{name} = %{version}-%{release}

%description doc
This package contains documentation for %{name}.


%prep
%setup -q -n %{name}-%{version}
rm -rf *egg-info
tar xzf %{SOURCE0}


%build
%{__python} setup.py build


%install
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{docdir}
cp -p LICENSE README.rst -t $RPM_BUILD_ROOT%{docdir}


%files
%dir %{python_sitelib}/tastypie_mongoengine
%{python_sitelib}/django_tastypie_mongoengine*
%{python_sitelib}/tastypie_mongoengine/*


%files doc
%doc %{docdir}


%changelog
* Mon Sep 17 2012 James Slagle <slagle@redhat.com> 0.2.3-4
- Add missing Requires (slagle@redhat.com)

* Mon Sep 17 2012 James Slagle <slagle@redhat.com> 0.2.3-3
- Add docs (slagle@redhat.com)
- package build fixes (slagle@redhat.com)

* Mon Sep 17 2012 James Slagle <slagle@redhat.com> 0.2.3-2
- new package built with tito

