Name:		splice
Version:	0.17
Release:	1%{?dist}
Summary:	Framework for tracking entitlement consumption

Group:		Development/Languages
License:	GPLv2
URL:		https://github.com/splice/splice-server
# Source0:	https://github.com/splice/splice-server/zipball/master/
Source0: %{name}-%{version}.tar.gz
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch: noarch
BuildRequires:	python2-devel
BuildRequires: python-setuptools
BuildRequires: rpm-python
Requires: mongodb-server
Requires: pymongo
Requires: pymongo-gridfs
Requires: mod_ssl
Requires: mod_wsgi
#
# We need a newer django packaged, along with django-tastypie and mongoengin
#Requires:	django > 1.4
#Requires: django-tastypie > 1.0
#Requires: mongoengine > 1.0
Requires: m2crypto >= 0.21.1.pulp-7


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
cp -R etc/splice %{buildroot}/%{_sysconfdir}

# Copy Cert Data
cp -R etc/pki/%{name} %{buildroot}/%{_sysconfdir}/pki/

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
%{_sysconfdir}/pki/%{name}
%dir /srv/%{name}
%dir %{_var}/log/%{name}
/srv/%{name}/webservices.wsgi
%doc

%changelog
* Thu Aug 30 2012 John Matthews <jmatthews@redhat.com> 0.17-1
- Fixed bug in saving system facts from rhsm, mongo didn't like '.' and '$' in
  key values (jmatthews@redhat.com)
- Debugging issue with storing facts (jmatthews@redhat.com)
- Move logic for extracting CN from cert to CertUtils (jmatthews@redhat.com)

* Wed Aug 29 2012 John Matthews <jmatthews@redhat.com> 0.16-1
- Cleaned up raised exceptions so tastypie will return a better response
  reflecting the issue (jmatthews@redhat.com)

* Wed Aug 29 2012 John Matthews <jmatthews@redhat.com> 0.15-1
- Added non-blocking sync of RHIC data, tied this to trigger when we can't find
  a RHIC's uuid, plus added unit tests for rhic_serve_client functionality
  (jmatthews@redhat.com)

* Wed Aug 29 2012 John Matthews <jmatthews@redhat.com> 0.14-1
- Update unit tests for new CA change (jmatthews@redhat.com)

* Wed Aug 29 2012 John Matthews <jmatthews@redhat.com> 0.13-1
- Update Splice testing CA certificate (jmatthews@redhat.com)

* Wed Aug 29 2012 John Matthews <jmatthews@redhat.com> 0.12-1
- Update for rhic_serve change to 'https' (jmatthews@redhat.com)

* Tue Aug 28 2012 John Matthews <jmatthews@redhat.com> 0.11-1
- Fixed how we encoded array query params to candlepin & update unit test with
  expected data (jmatthews@redhat.com)

* Tue Aug 28 2012 John Matthews <jmatthews@redhat.com> 0.10-1
- candlepin client change for productIDs and return the serial number of each
  certificate from json data (jmatthews@redhat.com)
- Implemented ability to call out to rhic_serve and synchronization RHICs, plus
  logic for lookup mapping of RHIC to products (jmatthews@redhat.com)

* Tue Aug 28 2012 John Matthews <jmatthews@redhat.com> 0.9-1
- Update call to candlepin to use rhicUUID param, and remove hard coding of
  RHIC uuid and Product id (jmatthews@redhat.com)

* Tue Aug 28 2012 John Matthews <jmatthews@redhat.com> 0.8-1
- Spec update to allow building tagged version from tito, needed to update
  Source0 (jmatthews@redhat.com)

* Tue Aug 28 2012 John Matthews <jmatthews@redhat.com> 0.7-1
- Cleanup (jmatthews@redhat.com)

* Mon Aug 27 2012 John Matthews <jmatthews@redhat.com> 0.6-1
- Adding requires for patched m2crypto from Pulp (jmatthews@redhat.com)
- Packaging tweaks to get RPM functional (jmatthews@redhat.com)

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

