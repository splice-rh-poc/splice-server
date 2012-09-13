%global mod_name blinker

Name:           python-blinker
Version:        1.1
Release:        1%{?dist}
Summary:        Fast, simple object-to-object and broadcast signaling

Group:          Development/Libraries
License:        MIT
URL:            http://discorporate.us/projects/Blinker/
Source0:        http://pypi.python.org/packages/source/b/%{mod_name}/%{mod_name}-%{version}.zip

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-setuptools

%description
Blinker provides a fast dispatching system that allows any number 
of interested parties to subscribe to events, or "signals".

%prep
%setup -q -n %{mod_name}-%{version}


%build
CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

 
%files
%doc docs/ CHANGES LICENSE README PKG-INFO
%{python_sitelib}/*.egg-info
%{python_sitelib}/%{mod_name}

%changelog
* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 1.2-1
- new package built with tito

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Fri Jul 22 2011 Praveen Kumar <kumarpraveen.nitdgp@gmail.com> - 1.1-1
- Initial RPM
