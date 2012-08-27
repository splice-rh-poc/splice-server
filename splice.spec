Name:		splice
Version:	0.5
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
mkdir -p %{buildroot}/%{_sysconfdir}/splice
mkdir -p %{buildroot}/%{_sysconfdir}/pki/%{name}
mkdir -p %{buildroot}/%{_var}/log/%{name}

# Install WSGI script & httpd conf
cp -R srv %{buildroot}
cp etc/httpd/conf.d/%{name}.conf %{buildroot}/%{_sysconfdir}/httpd/conf.d/
cp etc/splice %{buildroot}/%{_sysconfdir}/splice

# Copy Cert Data
cp -R etc/pki/%{name} %{buildroot}/%{_sysconfdir}/pki/%{name}

# Remove egg info
rm -rf %{buildroot}/%{python_sitelib}/*.egg-info

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%{python_sitelib}/%{name}
%config(noreplace) %{_sysconfdir}/splice/server.conf
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%defattr(-,apache,apache,-)
%dir %{_sysconfdir}/pki/%{name}
%dir /srv/%{name}
%dir %{_var}/log/%{name}
/srv/%{name}/webservices.wsgi
%doc

%changelog
* Mon Aug 27 2012 John Matthews <jmatthews@redhat.com> 0.5-1
- RCS is able to grab SSL client cert from request parameters and extract CN,
  also updated to work with latest candlepin API (jmatthews@redhat.com)
- Add ability to validate passed in identity certificate against configured
  root CA (jmatthews@redhat.com)
- Added ability to call out to candlepin to fetch entitlement certs
  (jmatthews@redhat.com)

* Tue Aug 21 2012 John Matthews <jmatthews@redhat.com> 0.4-1
- More spec updates (jmatthews@redhat.com)

* Tue Aug 21 2012 John Matthews <jmatthews@redhat.com> 0.3-1
- new package built with tito

* Tue Aug 21 2012 John Matthews <jmatthews@redhat.com> 0.2-1
- new package built with tito

* Tue Aug 21 2012 John Matthews <jmatthews@redhat.com> 0.1-1
- initial packaging

