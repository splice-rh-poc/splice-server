%if 0%{?fedora} > 12 || 0%{?rhel} > 6
%global with_python3 1
%else
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print (get_python_lib())")}
%endif


%global pypi_name nose-cover3

Name:           python-%{pypi_name}
Version:        0.1.0
Release:        4%{?dist}
Summary:        Coverage 3.x support for Nose

License:        LGPLv2+
URL:            http://pypi.python.org/pypi/nose-cover3/0.1.0
Source0:        http://pypi.python.org/packages/source/n/nose-cover3/nose-cover3-0.1.0.tar.gz
BuildArch:      noarch
Requires:       python-nose 
BuildRequires:  python2-devel
BuildRequires:  python-setuptools

%if 0%{?with_python3}
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
%endif # if with_python3


%description
Coverage 3.x support for Nose.

%if 0%{?with_python3}
%package -n python3-nose-cover3
Summary:        Coverage 3.x support for Nose
Requires:  python3-nose

%description -n python3-nose-cover3
Coverage 3.x support for Nose.
%endif # with_python3

%prep
%setup -q -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info
%if 0%{?with_python3}
cp -a . %{py3dir}
%endif



%build
%{__python} setup.py build
%if 0%{?with_python3}
pushd %{py3dir}
%{__python3} setup.py build
popd
%endif # with_python3



%install
%{__python} setup.py install --skip-build --root %{buildroot}
%if 0%{?with_python3}
pushd %{py3dir}
%{__python3} setup.py install --skip-build --root %{buildroot}
popd
%endif # with_python3


%files
%doc README.rst LICENSE
%{python_sitelib}/nosecover3
%{python_sitelib}/nose_cover3-%{version}-py?.?.egg-info

%if 0%{?with_python3}
%files -n python3-nose-cover3
%doc README.rst LICENSE
%{python3_sitelib}/*
%endif # with_python3


%changelog
* Sat Aug 04 2012 David Malcolm <dmalcolm@redhat.com> - 0.1.0-4
- rebuild for https://fedoraproject.org/wiki/Features/Python_3.3

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.1.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sun Jul 08 2012 Matthias Runge <mrunge@matthias-runge.de> - 0.1.0-2
- add python3 support

* Tue Jun 05 2012 Matthias Runge <mrunge@matthias-runge.de> - 0.1.0-1
- Initial package.
