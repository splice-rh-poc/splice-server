%global pkgname django-tastypie
%global docdir %{_docdir}/%{name}-%{version}

Name:		python-sphinxcontrib-httpdomain
Version:	1.1.7
Release:	3%{?dist}
Summary:	Documenting RESTful HTTP APIs with sphinx

Group:		Development/Languages
License:	BSD
URL:		http://packages.python.org/sphinxcontrib-httpdomain/
Source0:	%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:	python2-devel
BuildRequires:  python-setuptools


%description
Documenting RESTful HTTP APIs with sphinx

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
cp -p LICENSE README -t $RPM_BUILD_ROOT%{docdir}


%files
%dir %{python_sitelib}/sphinxcontrib
%{python_sitelib}/sphinxcontrib
%{python_sitelib}/sphinxcontrib_httpdomain*


%files doc
%doc %{docdir}


%changelog
* Thu Oct 25 2012 James Slagle <jslagle@redhat.com> 1.1.7-3
- Packaging Updates (jslagle@redhat.com)

* Thu Oct 25 2012 James Slagle <jslagle@redhat.com> 1.1.7-2
- new package built with tito


