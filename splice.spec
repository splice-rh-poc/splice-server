Name:		splice-server
Version:	0.1
Release:	1%{?dist}
Summary:	Framework for tracking entitlement consumption

Group:		Development/Languages
License:	GPLv2
URL:		https://github.com/splice/splice-server
Source0:	https://github.com/splice/splice-server/zipball/master
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:	python2-devel
BuildRequires: python-setuptools
BuildRequires: rpm-python
Requires: mongodb-server
Requires: pymongo
Requires: mod_ssl
Requires: mod_wsgi
#
# We need a newer django packaged, along with django-tastypie and mongoengin
#Requires:	django > 1.4
#Requires: django-tastypie > 1.0
#Requires: mongoengine > 1.0
#

%description
Framework for tracking entitlement consumption

%prep
%setup -q

%build
pushd src
%{__python} setup.py build
popd

%install
rm -rf %{buildroot}
pushd src
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
popd
mkdir -p %{buildroot}/%{_sysconfdir}/httpd/conf.d/

# Install WSGI script & httpd conf
cp -R srv %{buildroot}
cp etc/httpd/conf.d/%{name}.conf %{_sysconfdir}/httpd/conf.d/

# Remove egg info
rm -rf %{buildroot}/%{python_sitelib}/*.egg-info

%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%{python_sitelib}/%{name}
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%defattr(-,apache,apache,-)
%dir /srv/%{name}
%dir %{_var}/log/%{name}
/srv/%{name}/webservices.wsgi
%doc

%changelog
* Tue Aug 21 2012 John Matthews <jmatthews@redhat.com> 0.1-1
- initial packaging

