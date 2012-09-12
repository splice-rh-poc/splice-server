# sitelib for noarch packages, sitearch for others (remove the unneeded one)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}

Name:           python-mongoengine
Version:        0.6.20
Release:        2%{?dist}
Summary:        A Python Document-Object Mapper for working with MongoDB

Group:          Development/Libraries
License:        MIT
URL:            https://github.com/MongoEngine/mongoengine
Source0:        %{name}-%{version}.tar.bz2

BuildRequires:  python-devel
BuildRequires:  python-setuptools

Requires:       mongodb
Requires:       pymongo
Requires:       python-blinker
Requires:       python-imaging


%description
MongoEngine is an ORM-like layer on top of PyMongo.

%prep
%setup -q -n %{name}-%{version}


%build
# Remove CFLAGS=... for noarch packages (unneeded)
CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc docs AUTHORS LICENSE README.rst
# For noarch packages: sitelib
 %{python_sitelib}/*
# For arch-specific packages: sitearch
# %{python_sitearch}/*

%changelog
* Wed Sep 12 2012 John Matthews <jmatthews@redhat.com> 0.6.20-2
- new package built with tito

* Wed Sep 12 2012 John Matthews <jmatthews@redhat.com> 0.6.20-1
- Initial Build, minor tweaks to .spec from mongoengine source
