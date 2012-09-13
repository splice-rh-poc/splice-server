%global srcname billiard

Name:           python-%{srcname}
Version:        2.7.3.13
Release:        1%{?dist}
Summary:        Multiprocessing Pool Extensions

Group:          Development/Languages
License:        BSD
URL:            http://pypi.python.org/pypi/billiard
Source0:        http://pypi.python.org/packages/source/b/%{srcname}/%{srcname}-%{version}.tar.gz

BuildRequires:  python2-devel
BuildRequires:  python-setuptools

%description
This package contains extensions to the multiprocessing Pool.

%prep
%setup -q -n %{srcname}-%{version}

%build
%{__python} setup.py build

%install
rm -rf %{buildroot}
%{__python} setup.py install --skip-build --root %{buildroot}

%files
%doc CHANGES.txt LICENSE.txt README.rst
%{python_sitearch}/_billiard*
%{python_sitearch}/%{srcname}/
%{python_sitearch}/%{srcname}*.egg-info

%changelog
* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 2.7.3.13-1
- new package built with tito

* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 2.7.3.12-1
- update to new upstream version 2.7.3.12

* Fri Aug 03 2012 Matthias Runge <mrunge@matthias-runge.de> 2.7.3.11-1
- update to new upstream version 2.7.3.11

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.7.3.9-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Jun 19 2012 Fabian Affolter <mail@fabian-affolter.ch> - 2.7.3.9-1
- Updated to new upstream version 2.7.3.9

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.3.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.3.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sat Aug 14 2010 Fabian Affolter <mail@fabian-affolter.ch> - 0.3.1-2
- TODO removed

* Sat Jul 03 2010 Fabian Affolter <mail@fabian-affolter.ch> - 0.3.1-1
- Initial package
