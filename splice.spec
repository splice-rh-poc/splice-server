#SELinux
%global selinux_policyver %(%{__sed} -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp || echo 0.0.0)

Name:       splice
Version:    0.51
Release:    1%{?dist}
Summary:    Framework for tracking entitlement consumption

Group:      Development/Languages
License:    GPLv2
URL:        https://github.com/splice/splice-server
# Source0:  https://github.com/splice/splice-server/zipball/master/
Source0: %{name}-%{version}.tar.gz
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch: noarch
BuildRequires:  python2-devel
BuildRequires: python-setuptools
BuildRequires: rpm-python
Requires: mongodb-server
Requires: pymongo
Requires: pymongo-gridfs
Requires: mod_ssl
Requires: mod_wsgi
Requires: rabbitmq-server
Requires: librabbitmq
#
# Below RPMs are newer versions not yet in EPEL or RHEL
# We have the source stored in our git repo under 'deps'
#
Requires: Django >= 1.4.1
Requires: python-django-tastypie >= 0.9.12pre
Requires: python-mongoengine >= 0.6.20
Requires: python-celery >= 3.0
Requires: python-django-celery >= 3.0.9
Requires: m2crypto >= 0.21.1.pulp-7
#
# RPMs from Splice Project
#
Requires: rhic-serve-rcs >= 0.15
#
# Our own selinux RPM
#
Requires: %{name}-selinux = %{version}-%{release}

%description
Framework for metering entitlement consumption

%package        selinux
Summary:        Splice SELinux policy
Group:          Development/Languages
BuildRequires:  rpm-python
BuildRequires:  make
BuildRequires:  checkpolicy
BuildRequires:  selinux-policy-devel
# el6, selinux-policy-doc is the required RPM which will bring below 'policyhelp'
BuildRequires:  /usr/share/selinux/devel/policyhelp
BuildRequires:  hardlink
Requires: selinux-policy >= %{selinux_policyver}
Requires(post): policycoreutils-python 
Requires(post): selinux-policy-targeted
Requires(post): /usr/sbin/semodule, /sbin/fixfiles, /usr/sbin/semanage
Requires(postun): /usr/sbin/semodule

%description  selinux
SELinux policy for Splice

%prep
%setup -q

%build
pushd src
%{__python} setup.py build
popd
# SELinux Configuration
cd selinux
perl -i -pe 'BEGIN { $VER = join ".", grep /^\d+$/, split /\./, "%{version}.%{release}"; } s!0.0.0!$VER!g;' splice-server.te
./build.sh
cd -

%install
rm -rf %{buildroot}
pushd src
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
popd
mkdir -p %{buildroot}/%{_sysconfdir}/httpd/conf.d/
mkdir -p %{buildroot}/%{_sysconfdir}/splice
mkdir -p %{buildroot}/%{_sysconfdir}/pki/%{name}
mkdir -p %{buildroot}/%{_sysconfdir}/rc.d/init.d
mkdir -p %{buildroot}/%{_var}/log/%{name}

# Install WSGI script & httpd conf
cp -R srv %{buildroot}
cp etc/httpd/conf.d/%{name}.conf %{buildroot}/%{_sysconfdir}/httpd/conf.d/
cp -R etc/splice %{buildroot}/%{_sysconfdir}
cp -R etc/rc.d/init.d %{buildroot}/%{_sysconfdir}/rc.d

# Copy Cert Data
cp -R etc/pki/%{name} %{buildroot}/%{_sysconfdir}/pki/

# Remove egg info
rm -rf %{buildroot}/%{python_sitelib}/*.egg-info

# Install SELinux policy modules
cd selinux
./install.sh %{buildroot}%{_datadir}
mkdir -p %{buildroot}%{_datadir}/%{name}/selinux
cp enable.sh %{buildroot}%{_datadir}/%{name}/selinux
cp uninstall.sh %{buildroot}%{_datadir}/%{name}/selinux
cp relabel.sh %{buildroot}%{_datadir}/%{name}/selinux
cd -

%clean
rm -rf %{buildroot}

%post selinux
# Enable SELinux policy modules
if /usr/sbin/selinuxenabled ; then
 %{_datadir}/%{name}/selinux/enable.sh %{_datadir}
fi

# Continuing with using posttrans, as we did this for Pulp and it worked for us.
# restorcecon wasn't reading new file contexts we added when running under 'post' so moved to 'posttrans'
# Spacewalk saw same issue and filed BZ here: https://bugzilla.redhat.com/show_bug.cgi?id=505066
%posttrans selinux
if /usr/sbin/selinuxenabled ; then
 %{_datadir}/%{name}/selinux/relabel.sh %{_datadir}
fi

%preun selinux
# Clean up after package removal
if [ $1 -eq 0 ]; then
  %{_datadir}/%{name}/selinux/uninstall.sh
  %{_datadir}/%{name}/selinux/relabel.sh
fi
exit 0


%files
%defattr(-,root,root,-)
%{python_sitelib}/%{name}
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%config(noreplace) %{_sysconfdir}/splice/server.conf
%config(noreplace) %{_sysconfdir}/splice/celery/celerybeat
%config(noreplace) %{_sysconfdir}/splice/celery/celeryd
%config(noreplace) %{_sysconfdir}/rc.d/init.d/splice_celerybeat
%config(noreplace) %{_sysconfdir}/rc.d/init.d/splice_celeryd
%config(noreplace) %{_sysconfdir}/rc.d/init.d/splice_all


%defattr(-,apache,apache,-)
%dir %{_sysconfdir}/pki/%{name}
%{_sysconfdir}/pki/%{name}
%dir /srv/%{name}
%dir %{_var}/log/%{name}
/srv/%{name}/webservices.wsgi
%doc


%files selinux
%defattr(-,root,root,-)
%doc selinux/%{name}-server.fc selinux/%{name}-server.if selinux/%{name}-server.te
%{_datadir}/%{name}/selinux/*
%{_datadir}/selinux/*/%{name}-server.pp
%{_datadir}/selinux/devel/include/apps/%{name}-server.if

%changelog
* Fri Oct 12 2012 John Matthews <jmatthews@redhat.com> 0.51-1
- Fixes for selinux policy (jmatthews@redhat.com)
- Remove steps of disabling selinux (jmatthews@redhat.com)
- Update to reflect new build instance (jmatthews@redhat.com)

* Fri Oct 12 2012 John Matthews <jmatthews@redhat.com> 0.50-1
- SELinux policy (jmatthews@redhat.com)
- Added dep for django-picklefield for django-celery (jmatthews@redhat.com)

* Fri Oct 05 2012 John Matthews <jmatthews@redhat.com> 0.49-1
- Bumping number of RHICs to fetch on each pagination call
  (jmatthews@redhat.com)
- Touch up test script so we can vary gzip/limit and other params
  (jmatthews@redhat.com)
- Configuring splice server to use mod_defalte to gzip data,  updating rhic
  serve client to handle gzip response  adding test script to isolate behavior
  (jmatthews@redhat.com)
- Update speed of test script so it's quicker to load test rhics for syncing
  (jmatthews@redhat.com)

* Thu Oct 04 2012 John Matthews <jmatthews@redhat.com> 0.48-1
- Performance improvement for syncing RHICs, new UUIDs are broken out and a
  bulk insert is done, updates proceed sequentially as before, speed up seen
  about 20X improvement. (jmatthews@redhat.com)

* Tue Oct 02 2012 John Matthews <jmatthews@redhat.com> 0.47-1
- Removed the 'removal' logic that was deleting a RHIC if it wasn't on rhic-
  serve  - If rhic-serve deletes a rhic it will keep the RHIC in the DB and
  mark it as 'deleted=True' (jmatthews@redhat.com)

* Tue Oct 02 2012 John Matthews <jmatthews@redhat.com> 0.46-1
- Added pagination support for syncing all rhics (jmatthews@redhat.com)

* Tue Oct 02 2012 John Matthews <jmatthews@redhat.com> 0.45-1
- Updated to return '404' during checkin when a RHIC is confirmed NOT FOUND
  from parent chain, added test scripts to create a RHIC to throw a 404 with
  curl scripts (jmatthews@redhat.com)

* Tue Oct 02 2012 John Matthews <jmatthews@redhat.com> 0.44-1
- Bumpd requires on rhic-serve (jmatthews@redhat.com)

* Tue Oct 02 2012 John Matthews <jmatthews@redhat.com> 0.43-1
- Convenience method to drop the database (jmatthews@redhat.com)
- Added config option to enable/disable the task for syncing all RHICs
  (jmatthews@redhat.com)
- Automatic commit of package [python-mongoengine] minor release [0.7.5-3].
  (jslagle@redhat.com)
- Bump mongoengine to 0.7.5 (jslagle@redhat.com)
- Cleanup configuration options for rhic lookup tasks (jmatthews@redhat.com)

* Mon Oct 01 2012 John Matthews <jmatthews@redhat.com> 0.42-1
- Added logic to return a '410' when we know a RHIC has been deleted from rhic-
  serve (jmatthews@redhat.com)

* Sun Sep 30 2012 John Matthews <jmatthews@redhat.com> 0.41-1
- Fix processing existing rhic lookup tasks, logic for determining if a celery
  task was pending was incorrect. (jmatthews@redhat.com)
- Fix for data["objects"] when testing rhic_service_client.py by itself
  (jmatthews@redhat.com)
- Fix for getting 'state' of celery task (jmatthews@redhat.com)

* Fri Sep 28 2012 John Matthews <jmatthews@redhat.com> 0.40-1
- Fix broken tasks for single rhic lookup (jmatthews@redhat.com)

* Fri Sep 28 2012 John Matthews <jmatthews@redhat.com> 0.39-1
- Disabling full RHIC sync temporarily as we test single rhic lookup tasks
  (jmatthews@redhat.com)

* Fri Sep 28 2012 John Matthews <jmatthews@redhat.com> 0.38-1
- Update for rhic_serve changes placing rhic data in ["objects"]
  (jmatthews@redhat.com)
- Don't import Django 'settings.py' explicitly, use 'from django.conf import
  settings', this broke mongoengine and using an alias, resulting in a some
  documents using the 'production' database and others using the 'unittest'
  database. (jmatthews@redhat.com)
- Update rhic since after rhic_serve was wiped (jmatthews@redhat.com)
- Update settings.py to correct wrong celery task name for
  'process_running_rhic_lookup_tasks' (jmatthews@redhat.com)

* Thu Sep 27 2012 John Matthews <jmatthews@redhat.com> 0.37-1
- Update for new shared CA from rhic-serve (jmatthews@redhat.com)

* Thu Sep 27 2012 John Matthews <jmatthews@redhat.com> 0.36-1
- Add an init.d script to control the deps RCS has, httpd, splice_celeryd &
  splice_celerybeat (jmatthews@redhat.com)
- Added logic for initiating a single RHIC lookup and managing the lookup task
  until we receive a definitive '200' or '404' from an upstream parent.
  (jmatthews@redhat.com)
- Modify RHICRcsResource to return a '202' opposed to a '404' when a RHIC isn't
  known. Future change will return '404' after a lookup through RCS chain.
  (jmatthews@redhat.com)

* Mon Sep 24 2012 John Matthews <jmatthews@redhat.com> 0.35-1
- Added config option: 'task_schedule_minutes' under 'rhic_serve' controls how
  often sync task runs (jmatthews@redhat.com)

* Mon Sep 24 2012 John Matthews <jmatthews@redhat.com> 0.34-1
- Update for last_sync functionality when syncing RHICs against rhic_server or
  another RCS (jmatthews@redhat.com)
- Add a new header to record time in seconds of last call to entitlement
  service  example: X-Entitlement-Time-Seconds: 1.39451313019
  (jmatthews@redhat.com)

* Fri Sep 21 2012 John Matthews <jmatthews@redhat.com> 0.33-1
- Update mongo database alias for 'rhic_serve' (jmatthews@redhat.com)
- Update logic for sync of RHIC data to update creation/modification/deletion
  dates (jmatthews@redhat.com)

* Thu Sep 20 2012 John Matthews <jmatthews@redhat.com> 0.32-1
- Update to request entitlement certificate for all products associated to
  RHIC, also if a checkin is requested for some products not allowed by the
  RHIC we will allow the products associated to succeed and be entitled, while
  logging those unentitled. (jmatthews@redhat.com)

* Wed Sep 19 2012 John Matthews <jmatthews@redhat.com> 0.31-1
- Update settings.py for rhic_serve.rhic-rcs, also remove setting 'meta' on
  models.ConsumerIdentity (jmatthews@redhat.com)

* Wed Sep 19 2012 John Matthews <jmatthews@redhat.com> 0.30-1
- Added rhic-serve-rcs API, updated ConsumerIdentity to inherit from RHIC,
  added config attributes for SpliceServer to config file
  (jmatthews@redhat.com)

* Tue Sep 18 2012 John Matthews <jmatthews@redhat.com> 0.29-1
- Making tasks.sync_rhics() periodic, will run every hour
  (jmatthews@redhat.com)

* Tue Sep 18 2012 John Matthews <jmatthews@redhat.com> 0.28-1
- Remove celeryconfig from /etc/splice/celery (jmatthews@redhat.com)

* Tue Sep 18 2012 John Matthews <jmatthews@redhat.com> 0.27-1
- Add requires for python-django-celery (jmatthews@redhat.com)
- Added test periodic tasks to see how celery tasks behave from RPM

* Fri Sep 14 2012 John Matthews <jmatthews@redhat.com> 0.26-1
- Return '200' instead of '202' for a valid checkin with data
  (jmatthews@redhat.com)

* Fri Sep 14 2012 John Matthews <jmatthews@redhat.com> 0.25-1
- Return a '202' if we don't know about a RHIC (jmatthews@redhat.com)

* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 0.24-1
- Update splice.spec for celery daemon and config files (jmatthews@redhat.com)

* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 0.23-1
- Added a test task into splice that works with our celery daemon script
  (jmatthews@redhat.com)
- First pass at daemon scripts for celery & celerybeat (jmatthews@redhat.com)
- Update playpen celery test files with explicit name of tasks
  (jmatthews@redhat.com)

* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 0.22-1
- Fix requires for python-mongoengine (jmatthews@redhat.com)

* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 0.21-1
- Update spec to account newly built RPMs for Django, tastypie, mongoengine,
  celery (jmatthews@redhat.com)
* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 0.20-1
- Update spec to account newly built RPMs for Django, tastypie, mongoengine,
  celery (jmatthews@redhat.com)

* Wed Sep 12 2012 John Matthews <jmatthews@redhat.com> 0.19-1
- Update for timezones when request explict start/end expiration dates from
  candlepin (jmatthews@redhat.com)
- Moving celery playpen scripts to diff dir so we can experiment with rabbitmq
  (jmatthews@redhat.com)

* Wed Sep 12 2012 John Matthews <jmatthews@redhat.com> 0.18-1
- Added 'minutes' to checkin request, this is converted to start/end dates for
  certificate request when talking to candlepin (jmatthews@redhat.com)
- Update checkin entitlement call to accept a 'POST' or a 'PUT', recommended
  approach will be 'POST', updated test scripts to reflect this
  (jmatthews@redhat.com)
- Fixed an exception being formed incorrectly (jmatthews@redhat.com)
- Added a profiler middleware based on blogpost: http://gun.io/blog/fast-as-
  fuck-django-part-1-using-a-profiler/ (jmatthews@redhat.com)

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

