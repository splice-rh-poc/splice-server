#SELinux
%global selinux_policyver %(%{__sed} -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp || echo 0.0.0)

Name:       splice
Version:    0.117
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
BuildRequires: python-sphinx
BuildRequires: python-sphinxcontrib-httpdomain
Requires: mongodb-server
Requires: mod_ssl
Requires: mod_wsgi
Requires: rabbitmq-server
Requires: librabbitmq
Requires: python-oauth2
Requires: python-httplib2
#
# Below RPMs are newer versions not yet in EPEL or RHEL
# We have the source stored in our git repo under 'deps'
#
Requires: Django >= 1.4.1
Requires: python-django-tastypie >= 0.9.14
Requires: python-celery >= 3.0
Requires: django-celery >= 3.0.9
Requires: m2crypto >= 0.21.1.pulp-7
#
# RPMs from Splice Project
#
Requires: report-server-import >= 0.53
Requires: rhic-serve-rcs >= 0.15
#
# Our own sub RPMs
#
Requires: %{name}-selinux = %{version}-%{release}
Requires: %{name}-common = %{version}-%{release}
#
# rhic-serve's mod_wsgi configuration will cause Splice to be unusable
#
Conflicts: rhic-serve
#
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

%package        common
Summary:        Splice common components
Group:          Development/Languages
Requires:       %{name}-common-config = %{version}-%{release}
Requires:       python-certutils >= 0.15
Requires:       python-mongoengine >= 0.7.5
Requires:       pymongo
#Requires:       pymongo-gridfs

%description    common
Splice common components

%package        common-config
Summary:        Splice common config components
Group:          Development/Languages
Requires:       python-isodate

%description    common-config
Splice common config components

%package doc
Summary:    Splice documentation
Group:      Development/Languages

BuildRequires:  python-sphinx
BuildRequires:  python-sphinxcontrib-httpdomain

%description doc
Splice documentation


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

# Sphinx documentation
pushd doc
make html
popd

%install
rm -rf %{buildroot}
pushd src
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
popd
mkdir -p %{buildroot}/%{_sysconfdir}/httpd/conf.d/
mkdir -p %{buildroot}/%{_sysconfdir}/splice
mkdir -p %{buildroot}/%{_sysconfdir}/pki/%{name}
mkdir -p %{buildroot}/%{_sysconfdir}/rc.d/init.d
mkdir -p %{buildroot}/%{_var}/lib/%{name}
mkdir -p %{buildroot}/%{_var}/log/%{name}
mkdir -p %{buildroot}/%{_var}/log/%{name}/celery


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

# Documentation
mkdir -p %{buildroot}/%{_docdir}/%{name}
cp LICENSE %{buildroot}/%{_docdir}/%{name}
cp -R doc/_build/html %{buildroot}/%{_docdir}/%{name}

%clean
rm -rf %{buildroot}

%post
#
# If https certs haven't been generated, generate them and update https config file
# 
if [ ! -f /etc/pki/splice/generated/Splice_HTTPS_server.cert ]
then
    splice_cert_gen_setup.py /etc/httpd/conf.d/splice.conf
fi

%pre common
getent group splice >/dev/null || groupadd -r splice
getent passwd splice >/dev/null || \
    useradd -r -g splice -G apache -d %{_var}/lib/%{name} -s /sbin/nologin \
    -c "splice user" splice
exit 0

%post common
chown -R apache:splice %{_var}/log/%{name}
chown -R splice:splice %{_var}/log/%{name}/celery
chmod -R g+rwX %{_var}/log/%{name}
#
# If there is no Splice Server identity certificate, generate a new one for testing
# This step will be removed during production, the splice server cert must come from
# access.redhat.com eventually
#
if [ ! -f /etc/pki/consumer/Splice_identity.cert ]
then
    if [ ! -d /etc/pki/consumer ]
    then
        mkdir /etc/pki/consumer
    fi
    splice_cert_gen_identity.py --cacert /etc/pki/splice/Splice_testing_root_CA.crt --cakey /etc/pki/splice/Splice_testing_root_CA.key --outcert /etc/pki/consumer/Splice_identity.cert --outkey /etc/pki/consumer/Splice_identity.key
fi


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
    # TODO:
    # **Remove for Production**:  This is only to aid test/development
    semanage fcontext -a -t splice_cert_t "/etc/pki/consumer/Splice(.*)?"
    restorecon /etc/pki/consumer/Splice*
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
%config(noreplace) %{_sysconfdir}/splice/celery/celerybeat
%config(noreplace) %{_sysconfdir}/splice/celery/celeryd
%config(noreplace) %{_sysconfdir}/rc.d/init.d/splice_celerybeat
%config(noreplace) %{_sysconfdir}/rc.d/init.d/splice_celeryd
%config(noreplace) %{_sysconfdir}/rc.d/init.d/splice_all
%defattr(-,apache,apache,-)
%dir /srv/%{name}
/srv/%{name}/webservices.wsgi
%doc

%files common
%defattr(-,root,root,-)
%{python_sitelib}/%{name}/common
%exclude %{python_sitelib}/%{name}/common/__init__.py*
%exclude %{python_sitelib}/%{name}/common/config.py*
%{python_sitelib}/%{name}/__init__.py*
%config(noreplace) %{_sysconfdir}/%{name}
%exclude %{_sysconfdir}/%{name}/splice.conf
%exclude %{_sysconfdir}/%{name}/logging/basic.cfg
%defattr(-,apache,splice,-)
%dir %{_sysconfdir}/pki/%{name}
%{_sysconfdir}/pki/%{name}
%dir %{_var}/lib/%{name}
%dir %{_var}/log/%{name}
%dir %{_var}/log/%{name}/celery

%files common-config
%defattr(-,root,root,-)
%dir %{python_sitelib}/%{name}/common
%{python_sitelib}/%{name}/common/__init__.py*
%{python_sitelib}/%{name}/common/config.py*
%config(noreplace) %{_sysconfdir}/%{name}
%exclude %{_sysconfdir}/%{name}/conf.d


%files selinux
%defattr(-,root,root,-)
%doc selinux/%{name}-server.fc selinux/%{name}-server.if selinux/%{name}-server.te
%{_datadir}/%{name}/selinux/*
%{_datadir}/selinux/*/%{name}-server.pp
%{_datadir}/selinux/devel/include/apps/%{name}-server.if

%files doc
%doc %{_docdir}/%{name}


%changelog
* Wed May 22 2013 John Matthews <jwmatthews@gmail.com> 0.117-1
- Removing pymongo-gridfs dep (jwmatthews@gmail.com)

* Fri May 17 2013 John Matthews <jwmatthews@gmail.com> 0.116-1
- Fix for newer version of tastypie which no longer passes in 'request' to
  obj_update (jwmatthews@gmail.com)

* Fri May 17 2013 John Matthews <jwmatthews@gmail.com> 0.115-1
- Handle if 'updated' or 'created' are passed into JSON with "" values
  (jwmatthews@gmail.com)

* Fri May 17 2013 John Matthews <jwmatthews@gmail.com> 0.114-1
- Fix for newer version of tastypie so we don't delete the collection on upload
  (jwmatthews@gmail.com)
- Updated marketing product usage JSON example (jwmatthews@gmail.com)

* Mon May 13 2013 John Matthews <jwmatthews@gmail.com> 0.113-1
- Update to work with python-django-tastypie-0.9.14, also add requires for
  python-oauth2 and python-httplib2 (jwmatthews@gmail.com)

* Wed May 08 2013 John Matthews <jwmatthews@gmail.com> 0.112-1
- Changing 'entitlement_status' to a Dictionary (jwmatthews@gmail.com)
- Fix error: TypeError: option values must be strings (jwmatthews@gmail.com)
- Fix deps on splice-common (jslagle@redhat.com)

* Thu Apr 25 2013 James Slagle <jslagle@redhat.com> 0.111-1
- Add missing import (jslagle@redhat.com)

* Thu Apr 25 2013 James Slagle <jslagle@redhat.com> 0.110-1
- Update test for different dep (jslagle@redhat.com)

* Thu Apr 25 2013 James Slagle <jslagle@redhat.com> 0.109-1
- Remove dependencies on rhic-serve. (jslagle@redhat.com)

* Wed Apr 24 2013 John Matthews <jwmatthews@gmail.com> 0.108-1
- Added OAuth Authentication and a 'ping' API to test SpliceAuth which contains
  both OAuth and X509 as Authentication methods (jwmatthews@gmail.com)

* Tue Apr 16 2013 John Matthews <jwmatthews@gmail.com> 0.107-1
- Fix for splice.common.api 'complete_hook', reset 'self.all_objects' on each
  request (jwmatthews@gmail.com)

* Fri Apr 12 2013 John Matthews <jwmatthews@gmail.com> 0.106-1
- Small cleanup (jwmatthews@gmail.com)
- Update for spliceserver API (jwmatthews@gmail.com)
- Removing sphix generated _build from git (jwmatthews@gmail.com)
- Updated shinx docs for splice.common.apis (jwmatthews@gmail.com)
- Sample curl script and json to exercise splice.common.apis
  (jwmatthews@gmail.com)
- use server name instead of server hostname (cduryee@redhat.com)

* Mon Apr 08 2013 John Matthews <jwmatthews@gmail.com> 0.105-1
- Add allow inheritance to splice.common.models (jwmatthews@gmail.com)
- use candlepin from upstream (cduryee@redhat.com)
- Updated BaseResource based on integration work getting
  MarkertingProductUsageResouce to work with Report Server  - added the
  'complete_hook' to be called after all objects have been serialized from REST
  request  - move some base classes from unit tests to splice.common so we can
  reuse functionality in ReportServer  - Moved ProductUsageResource into
  splice.common.api, more updates may be desired so inherits from BaseResource
  (jwmatthews@gmail.com)
- add additional fields per wes (cduryee@redhat.com)
- add spacewalk-reports rpm (cduryee@redhat.com)
- Changed sample data and removed comment (jwmatthews@gmail.com)
- add unit tests for deserializer (cduryee@redhat.com)
- Add new deserializer to handle zipped json data (cduryee@redhat.com)
- add entitlement status field to MPU (cduryee@redhat.com)
- Updates to Pool/Product/Rules API, curl scripts to upload real data from
  Candlepin to Splice APIs - from_test_json.py  will talk to candlepin and form
  sample .json data - then upload*.sh scripts under playpen will send the
  sample .json to splice APIs (jwmatthews@gmail.com)
- unit tests for MarketingProductUsage (cduryee@redhat.com)
- marketing product tracking support (cduryee@redhat.com)
- Added support for decoding base64 rules from Candlepin as well as
  splice.common API to accept Rules being uploaded to us (jwmatthews@gmail.com)
- Updates and unit tests for Pool & Product API (jwmatthews@gmail.com)
- Fixes problem when passed in manifest is called manifest.zip
  (jwmatthews@gmail.com)
- Require a --host to be specified (jwmatthews@gmail.com)
- Introduced a BaseResource to handle most of the update logic we want for our
  APIs Reworked SpliceServerResource to use BaseResource Added Product & Pool
  API, unit tests lacking, will be in commit later today (jwmatthews@gmail.com)
- Changing SpliceServer models attribute of "modified" to "updated"
  (jwmatthews@gmail.com)
- add spacewalk-splice-tool (cduryee@redhat.com)
- forgot a file (cduryee@redhat.com)
- use master instead of buildtest branch for spacewalk (cduryee@redhat.com)
- rebuild candlepin from source, and install newer candlepin.
  (cduryee@redhat.com)
- Added ability to fetch Pool & Product data from Candlepin and save to mongo
  (jwmatthews@gmail.com)
- Fetch/Parse Pool & Product data from Candlepin (jwmatthews@gmail.com)
- First steps for getting subscription manifest data from Candlepin
  (jwmatthews@gmail.com)
- Open 8443 for Candlepin in iptables (jwmatthews@gmail.com)
- Fixed issue with using pub sshkey instead of priv for ssh, added more print
  statements (jwmatthews@gmail.com)
- Tweaks to fix provisioning a Spacewalk+Candlepin (jwmatthews@gmail.com)
- Provisioning script to lauch a modified Spacewalk with Candlepin
  (jwmatthews@gmail.com)
- EC2 provisioning script to install Spacewalk & Candlepin together on same
  instance (jwmatthews@gmail.com)
- EC2 provisioning script to install Spacewalk & Candlepin together on same
  instance (jwmatthews@gmail.com)
- EC2 provisioning scripts to launch a Spacewalk instance
  (jwmatthews@gmail.com)
- Touchups to launch Report Server and fix to source functions.sh for launch
  RCS (jwmatthews@gmail.com)
- Added a provisioning script for ReportServer, fixed EBS volume to be set to
  delete on termination (jwmatthews@gmail.com)
- Minor cleanup of Log statements no longer needed (jwmatthews@gmail.com)
- Moved launch EC2 scripts to python-boto (jwmatthews@gmail.com)

* Thu Jan 31 2013 John Matthews <jwmatthews@gmail.com> 0.104-1
- Adding debug info to track down issue with SpliceServer upload in
  ReportServer (jwmatthews@gmail.com)

* Thu Jan 31 2013 John Matthews <jwmatthews@gmail.com> 0.103-1
- Adding debug info for splice.common.api SpliceServer (jwmatthews@gmail.com)

* Thu Jan 31 2013 John Matthews <jwmatthews@gmail.com> 0.102-1
- Adding requires of "python-isodate" to splice-common (jwmatthews@gmail.com)

* Thu Jan 31 2013 John Matthews <jwmatthews@gmail.com> 0.101-1
- Removing requirement of django.http being available to use
  splice.common.exceptions (needed by spacewalk-splice-tool)
  (jwmatthews@gmail.com)
- Fix unit test to allow mocked method to accept "gzip" arg
  (jwmatthews@gmail.com)
- Adding "spacewalk-splice-tool" and "splice-socketreport" to list of packages
  to build (jwmatthews@gmail.com)
- Update ec2 instance tag to reflect the rpm version of the RCS which was setup
  (jmatthews@redhat.com)
- Small logging update (jmatthews@redhat.com)
- Prefix ec2 instance of launched RCS with whoami (jmatthews@redhat.com)

* Wed Jan 23 2013 John Matthews <jmatthews@redhat.com> 0.100-1
- Bump requires on report server to version with gzip support
  (jmatthews@redhat.com)

* Wed Jan 23 2013 John Matthews <jmatthews@redhat.com> 0.99-1
- Adding gzip to request for upload of ProductUsage data, seeing improvements
  from 10k entries of 35MB compressed to 240k (jmatthews@redhat.com)
- Unit tests for uploading an empty body on ProductUsage, requires update from
  ReportServer API (jmatthews@redhat.com)
- Update comments in SingleTaskInfo (jmatthews@redhat.com)
- Fix exception with get_all_rhics() when body is empty (jmatthews@redhat.com)
- Debug scripts to help isolate celerybeat issues during daemon mode
  (jmatthews@redhat.com)
- Added ability to create test data from any start date (jmatthews@redhat.com)
- Test script to help test timing for fetch/update of the tracker entry in a
  ProductUsage document (jmatthews@redhat.com)

* Thu Jan 17 2013 John Matthews <jmatthews@redhat.com> 0.98-1
- Added @single_task_instance to product usage task (jmatthews@redhat.com)
- Added @single_instance_task decorator to restrict celery tasks spawned by
  different processes to a global single task running at a time
  (jmatthews@redhat.com)
- Add mongo port to config file (jmatthews@redhat.com)
- Removing manage.py's usage of "dev.settings" (jmatthews@redhat.com)

* Tue Jan 15 2013 John Matthews <jmatthews@redhat.com> 0.97-1
- Removed traces of older usage of "since" with product usage upload
  (jmatthews@redhat.com)
- Update exception middleware to return a plain text exception traceback that
  is easier to read for REST API calls opposed to HTML text
  (jmatthews@redhat.com)
- Update path for splice identity cert (jmatthews@redhat.com)
- Don't log large message bodies (jmatthews@redhat.com)
- Added index for ProductUsage to fix: database error: too much data for sort()
  with no index. (jmatthews@redhat.com)

* Mon Jan 14 2013 John Matthews <jmatthews@redhat.com> 0.96-1
- Increasing verbosity for celerybeat launcher (jmatthews@redhat.com)
- Fix how /var/run/ was being owned by 'splice' because of celeryd/celerybeat
  chown of the basedir containing their pid lock files (jmatthews@redhat.com)
- First steps on change to upload ProductUsage based on which endpoint it's
  been sent to, opposed to a last processed timestamp (jmatthews@redhat.com)
- Update to use tee for builder output (jmatthews@redhat.com)
- Run 'restorecon' so apache is able to serve content with SELinux enabled
  (jmatthews@redhat.com)
- Script to build all splice subprojects and form a yum repo
  (jmatthews@redhat.com)

* Mon Jan 07 2013 John Matthews <jmatthews@redhat.com> 0.95-1
- Adding a logging perm workaround to /etc/init.d/splice_all
  (jmatthews@redhat.com)

* Mon Jan 07 2013 John Matthews <jmatthews@redhat.com> 0.94-1
- Update for perms on /var/log/splice, celery files will be in own subdir
  (jmatthews@redhat.com)

* Mon Jan 07 2013 John Matthews <jmatthews@redhat.com> 0.93-1
- Cleanup RHIC sync task (jmatthews@redhat.com)
- Fix for dev_setup.py with creating 'splice' user (jmatthews@redhat.com)

* Thu Jan 03 2013 John Matthews <jmatthews@redhat.com> 0.92-1
- Clean up of launch RCS scripts (jmatthews@redhat.com)
- Update splice.spec to change home dir of 'splice' user to '/var/lib/splice'
  (jmatthews@redhat.com)
- Update dev_setup.py to create 'splice' user (jmatthews@redhat.com)

* Thu Jan 03 2013 John Matthews <jmatthews@redhat.com> 0.91-1
- Update group perms for /var/log/splice (jmatthews@redhat.com)

* Thu Jan 03 2013 John Matthews <jmatthews@redhat.com> 0.90-1
- Adding 'waitfor' function to install script for RCS (jmatthews@redhat.com)
- Celery tasks now execute as 'splice' user (jmatthews@redhat.com)
- Continuing to debug intermittent issues with RCS ec2 scripts
  (jmatthews@redhat.com)

* Wed Jan 02 2013 John Matthews <jmatthews@redhat.com> 0.89-1
- Fix intermittent timing error with launch of new RCS & mark EBS volume as
  delete on termination true (jmatthews@redhat.com)
- Fix for upload tasks of Splice Server metadata and ProductUsage to append "/"
  to end of URL (jmatthews@redhat.com)
- Updates for latest build of splice-certmaker (jmatthews@redhat.com)

* Tue Dec 11 2012 John Matthews <jmatthews@redhat.com> 0.88-1
- Moved SpliceServerResource from report server codebase to here
  (jmatthews@redhat.com)
- Modified upload task to include uploading Splice Server metadata & unit tests
  (jmatthews@redhat.com)
- On a '500' write Request & Exception to splice.log AND
  /var/log/httpd/error_log (jmatthews@redhat.com)
- Fix for timezone aware issues, updated mongo connection to use tz_aware=True,
  updated common utils method to add tzinfo if not set (jmatthews@redhat.com)
- Adding API for uploading splice server metadata (jmatthews@redhat.com)
- Update iptables for 8080 to allow splice-certmaker to accept external upload.
  (jmatthews@redhat.com)
- Small refactor to splice_server_client to support uploading a new data:
  Splice Server Metadata (jmatthews@redhat.com)
- Update for uploading product data to splice-certmaker and changed config val:
  product_json_cache (jmatthews@redhat.com)
- Introduced env var SPLICE_CONFIG. Allows unittests to override logging config
  to silence output to console (jmatthews@redhat.com)
- Update from testing, single script now able to launch a working
  RCS+splice_certmaker (jmatthews@redhat.com)

* Fri Nov 30 2012 John Matthews <jmatthews@redhat.com> 0.87-1
- Fixes being unable to create Splice Server identity certificate on a clean
  install. Ordering was an issue, splice-common %%post was running before the
  requires of python-certutil was installed. (jmatthews@redhat.com)
- Comment for conf file about splice-certmaker being co-located by default
  (jmatthews@redhat.com)

* Thu Nov 29 2012 John Matthews <jmatthews@redhat.com> 0.86-1
- Update config values for new location of splice server identity certificate
  (jmatthews@redhat.com)
- Update to include splice-certmaker, also enhancements for setting hostname
  automatically (jmatthews@redhat.com)

* Thu Nov 29 2012 John Matthews <jmatthews@redhat.com> 0.85-1
- Update for splice-certmaker conf for temporary product_data location Spec
  update for selinux rules for splice server identity certificate context
  labeling (jmatthews@redhat.com)
- Fix spec (jmatthews@redhat.com)

* Thu Nov 29 2012 John Matthews <jmatthews@redhat.com> 0.84-1
- Update to work with co-located splice-certmaker (jmatthews@redhat.com)
- Update location of Splice Server identity certificate (jmatthews@redhat.com)
- Merge branch 'master' of github.com:splice/splice-server (jslagle@redhat.com)
- A few config updates (jslagle@redhat.com)

* Wed Nov 28 2012 John Matthews <jmatthews@redhat.com> 0.83-1
- Update client piece of uploading product usage data to use common
  BaseConnection (jmatthews@redhat.com)
- Moved rhic_serve_client code to use BaseConnection (jmatthews@redhat.com)
- Adding support for 'gzip' encoding to BaseConnection, also changed to return
  (status_code, response_body) (jmatthews@redhat.com)
- Update candlepin_client.py to reuse BaseConnection from common/connect, added
  HTTP option to BaseConnection (jmatthews@redhat.com)
- Spec change: splice-common-config now includes /etc/splice/splice.conf and
  /etc/splice/logging/basic.cfg (jmatthews@redhat.com)
- Set propagate back to 0 to avoid duplicate messages being logged
  (jmatthews@redhat.com)
- Celery tasks will no longer be scheduled if the Splice Server Identity
  Certificate is invalid (jmatthews@redhat.com)
- Remove Splice Server Identity cert/key for now and leave in
  conf.d/server.conf (jmatthews@redhat.com)
- Update dev_setup.py to account for /etc/splice/conf.d (jmatthews@redhat.com)
- Return a '500' with an error message if the servers Identity Certificate is
  invalid (jmatthews@redhat.com)
- Adding Splice Server's identity cert/key to config file so it's explicit and
  easy to modify (jmatthews@redhat.com)

* Mon Nov 26 2012 John Matthews <jmatthews@redhat.com> 0.82-1
- Test tag/build after splice-common work has been merged in


* Wed Nov 14 2012 James Slagle <jslagle@redhat.com> 0.81.common_config-1
- Set branch name in version field instead of release (jslagle@redhat.com)
- common-config subpackage (jslagle@redhat.com)
- api doc update" (jslagle@redhat.com)
- Exclude dev from packaging (jslagle@redhat.com)
- Add mongoengine auth to common/settings.py (jslagle@redhat.com)
- Don't need to check for existence of options as much now that defautls are
  set (jslagle@redhat.com)
- Set full tastypie debug in dev.settings (jslagle@redhat.com)
- Config updates (jslagle@redhat.com)
- Rename _LOG so that it gets imported via * (jslagle@redhat.com)
- Add config for sign_days (jslagle@redhat.com)
- Move logging config to splice.conf (jslagle@redhat.com)
- initialize config from common settings (jslagle@redhat.com)
- Set test db name dynamically (jslagle@redhat.com)
- Common settings.py (jslagle@redhat.com)
- Add missing dev logging config (jslagle@redhat.com)
- Config updates to accomodate fact that CELERYBEAT_SCHEDULE must be set
  directly in settings.py (jslagle@redhat.com)
- Fix config file name (jslagle@redhat.com)
- Include all config files under /etc/splice in common subpackage
  (jslagle@redhat.com)
- Initial config refactoring (jslagle@redhat.com)

* Tue Nov 13 2012 John Matthews <jmatthews@redhat.com> 0.80-1
- Again saw collision with 0.79 (jmatthews@redhat.com)
- Problem tagging 0.78, manual bump of version and will retry
  (jmatthews@redhat.com)
- Fix issue with rhic lookup tasks being marked as expired and not running
  because of how we set a default value for 'initiated' (jmatthews@redhat.com)
- Example to gather system facts (jmatthews@redhat.com)
- Update ProductUsage to sanitize facts on save to mongo (jmatthews@redhat.com)
- Add timing info for product usage import (jmatthews@redhat.com)
- Update script to generate simulated data with valid system facts
  (jmatthews@redhat.com)
- Automatic commit of package [python-ordereddict] minor release [1.1-6].
  (jmatthews@redhat.com)
- Adding python-orderreddict 1.1 version from fedora 18, needed by django-
  celery (jmatthews@redhat.com)
- Update script to upload fake product usage data for X number of instances and
  X entries (jmatthews@redhat.com)

* Tue Nov 13 2012 John Matthews <jmatthews@redhat.com>
- Problem tagging 0.78, manual bump of version and will retry
  (jmatthews@redhat.com)
- Fix issue with rhic lookup tasks being marked as expired and not running
  because of how we set a default value for 'initiated' (jmatthews@redhat.com)
- Example to gather system facts (jmatthews@redhat.com)
- Update ProductUsage to sanitize facts on save to mongo (jmatthews@redhat.com)
- Add timing info for product usage import (jmatthews@redhat.com)
- Update script to generate simulated data with valid system facts
  (jmatthews@redhat.com)
- Automatic commit of package [python-ordereddict] minor release [1.1-6].
  (jmatthews@redhat.com)
- Adding python-orderreddict 1.1 version from fedora 18, needed by django-
  celery (jmatthews@redhat.com)
- Update script to upload fake product usage data for X number of instances and
  X entries (jmatthews@redhat.com)

* Tue Nov 13 2012 John Matthews <jmatthews@redhat.com>
- Fix issue with rhic lookup tasks being marked as expired and not running
  because of how we set a default value for 'initiated' (jmatthews@redhat.com)
- Update ProductUsage to sanitize facts on save to mongo (jmatthews@redhat.com)
- Add timing info for product usage import (jmatthews@redhat.com)

* Fri Nov 02 2012 James Slagle <jslagle@redhat.com> 0.79-1.common_config
- Include all config files under /etc/splice in common subpackage
  (jslagle@redhat.com)

* Fri Nov 02 2012 James Slagle <jslagle@redhat.com> 0.78-1.common_config
- Initial config refactoring (jslagle@redhat.com)

* Wed Oct 31 2012 John Matthews <jmatthews@redhat.com> 0.77-1
- splice-common now owns /var/log/splice (jmatthews@redhat.com)

* Wed Oct 31 2012 John Matthews <jmatthews@redhat.com> 0.76-1
- adding spacewalk splice tool to logging config (pkilambi@redhat.com)

* Wed Oct 31 2012 John Matthews <jmatthews@redhat.com> 0.75-1
- Fixes for upload product usage task (jmatthews@redhat.com)
- Fix typo in upload product usage task (jmatthews@redhat.com)

* Wed Oct 31 2012 John Matthews <jmatthews@redhat.com> 0.74-1
- Allow product usage upload task to not run if 'servers' is commented out in
  config, also added more exception handling in other client pieces
  (jmatthews@redhat.com)

* Wed Oct 31 2012 John Matthews <jmatthews@redhat.com> 0.73-1
- Enable product usage task, needs more testing (jmatthews@redhat.com)
- Bump requires of mongoengine to 0.7.5 (jmatthews@redhat.com)
- Upload logging (jmatthews@redhat.com)

* Wed Oct 31 2012 John Matthews <jmatthews@redhat.com> 0.72-1
- Bump requires of python-certutils (jmatthews@redhat.com)

* Wed Oct 31 2012 John Matthews <jmatthews@redhat.com> 0.71-1
- Fix typo in %%post of splice-common (jmatthews@redhat.com)
- Added check of essential configuration certificates to startup, will LOG a
  warning if something isn't correct (jmatthews@redhat.com)
- Small change to config comments (jmatthews@redhat.com)
- base connection module to make rest calls (pkilambi@redhat.com)

* Wed Oct 31 2012 John Matthews <jmatthews@redhat.com> 0.70-1
- Adding in logging configuration for unit tests (jmatthews@redhat.com)
- Move generation of Splice Server identity certificate to splice-common
  (jmatthews@redhat.com)
- Update how we call config.init(), remove 'config' calling back into
  settings.py to avoid any cyclical dep issues (jmatthews@redhat.com)
- Update config so connections to rhic_serve are secured by the Splice Server
  identity certificate (jmatthews@redhat.com)
- Added celery task for uploading product usage data along with unit tests,
  untested beyond unit tests (jmatthews@redhat.com)

* Mon Oct 29 2012 James Slagle <jslagle@redhat.com> 0.69-1
- Read config file path from settings (jslagle@redhat.com)

* Mon Oct 29 2012 John Matthews <jmatthews@redhat.com> 0.68-1
- packaging fix for %%post in splice-common (jmatthews@redhat.com)

* Mon Oct 29 2012 John Matthews <jmatthews@redhat.com> 0.67-1
- Get SpliceServer uuid from Splice Server identity certificate, also fix so
  'hostname' is recorded on SpliceServer object (jmatthews@redhat.com)
- Logging configuration is now controlled by /etc/splice/logging/basic.cfg,
  specified in /etc/splice/server.conf (jmatthews@redhat.com)
- Update config value name for rhic serve URL (jmatthews@redhat.com)
- Update client side scripts to test X509 auth for syncing rhics
  (jmatthews@redhat.com)
- Update client side of product usage to use the Splice Server Identity
  Certificate for SSL communication (jmatthews@redhat.com)
- Fix type in config for identity certificate private key
  (jmatthews@redhat.com)

* Mon Oct 29 2012 John Matthews <jmatthews@redhat.com> 0.66-1
- Add Splice_testing_root_CA.cert/key to splice-common RPM
  (jmatthews@redhat.com)

* Mon Oct 29 2012 John Matthews <jmatthews@redhat.com> 0.65-1
- Move /etc/splice/server.conf to splice-common so we can share between splice
  applications (jmatthews@redhat.com)
- Update for client side of X509 authentication with syncing RHICs
  (jmatthews@redhat.com)

* Fri Oct 26 2012 John Matthews <jmatthews@redhat.com> 0.64-1
- Correct for cakey in %%post (jmatthews@redhat.com)

* Fri Oct 26 2012 John Matthews <jmatthews@redhat.com> 0.63-1
- Fix for correct name of splice_cert_gen_setup.py (jmatthews@redhat.com)

* Fri Oct 26 2012 John Matthews <jmatthews@redhat.com> 0.62-1
- Generate Splice Server identity certificate now on a new install in %%post
  (jmatthews@redhat.com)
- Split verification CAs into verify RHIC and verify Splice Server Identity,
  changed productusage API to use x509authentication (jmatthews@redhat.com)
- Update so unittests work with rhic_server.rcs requirement
  (jmatthews@redhat.com)
- Add step to actually build the documentation (jslagle@redhat.com)
- Update sphinx conf.py (jslagle@redhat.com)
- Add doc build and packaging (jslagle@redhat.com)

* Fri Oct 26 2012 John Matthews <jmatthews@redhat.com> 0.61-1
- Updated for new location of HTTPS SSL CA Cert (jmatthews@redhat.com)
- Adding %%post step that will auto generate https ssl certs if they don't
  exist (jmatthews@redhat.com)
- Update for name of default https certs (jmatthews@redhat.com)

* Fri Oct 26 2012 John Matthews <jmatthews@redhat.com> 0.60-1
- Update for init.d script to fix a problem see on initial start
  (jmatthews@redhat.com)

* Fri Oct 26 2012 John Matthews <jmatthews@redhat.com> 0.59-1
- Fixes while testing with latest report-server-import & rhic-serve RPMs
  report-server-import is importing rhic-serve-rest, creating a problem where
  requests aren't served the rhic-serve-rest models.py is requiring some
  certificate settings in settings.py, we needed to add them to allow things to
  proceed, this should be re-examined later and changed so we can get all
  values from config file (jmatthews@redhat.com)

* Thu Oct 25 2012 John Matthews <jmatthews@redhat.com> 0.58-1
- Update for CertificateParseException thrown by python-certutils
  (jmatthews@redhat.com)
- Moved location of HTTPS certs to use what python-certutils generates
  (jmatthews@redhat.com)
- Update checkin.py to remove cert validation and rely on
  X509CertificateAuthentication, some refactoring and cleanup to support this
  (jmatthews@redhat.com)
- Added unique constraint to product usage data and unit tests for product
  usage import API (jmatthews@redhat.com)
- ProductUsage.splice_server is now a string, set it to the splice server's
  uuid (jslagle@redhat.com)

* Fri Oct 19 2012 John Matthews <jmatthews@redhat.com> 0.57-1
- Create splice-common RPM and moving model definitions into it to make it
  easier to consume in Report Server (jmatthews@redhat.com)

* Thu Oct 18 2012 John Matthews <jmatthews@redhat.com> 0.56-1
- Integrate with new splice-certgen and update config for new rhic_serve
  instance (jmatthews@redhat.com)
- Beginning to integrate report server's product usage import API, needs more
  work (jmatthews@redhat.com)
- Experimenting with a way to force 500's to be logged/written to apache error
  log, not yet working (jmatthews@redhat.com)
- Automatic commit of package [Django] minor release [1.4.1-6.splice].
  (jslagle@redhat.com)
- Package is just called python-sphinx on fedora (jslagle@redhat.com)

* Tue Oct 16 2012 John Matthews <jmatthews@redhat.com> 0.55-1
- Update for name change of python-django-celery to django-celery to match what
  is in epel (jmatthews@redhat.com)

* Mon Oct 15 2012 James Slagle <jslagle@redhat.com> 0.54-1
- Migrate to python-certutils package (jslagle@redhat.com)

* Mon Oct 15 2012 John Matthews <jmatthews@redhat.com> 0.53-1
- Fix for when log file doesn't exist (jmatthews@redhat.com)

* Fri Oct 12 2012 John Matthews <jmatthews@redhat.com> 0.52-1
- More selinux fixes for packaging (jmatthews@redhat.com)

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

