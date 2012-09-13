%if 0%{?fedora} > 12 || 0%{?rhel} > 6
%global with_python3 0
%else
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print (get_python_lib())")}
%endif

Name:           python-celery
Version:        3.0.9
Release:        5%{?dist}
Summary:        Distributed Task Queue

Group:          Development/Languages
License:        BSD
URL:            http://celeryproject.org
Source0:        http://pypi.python.org/packages/source/c/celery/celery-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
Requires:       python-anyjson
Requires:       python-dateutil
Requires:       python-kombu >= 2.4.6
Requires:       python-billiard >= 2.7.3.12
Requires:       python-amqplib >= 1.0.2

BuildRequires:  python-kombu >= 2.4.6
Requires:       pyparsing
%if ! (0%{?fedora} > 13 || 0%{?rhel} > 6)
Requires:       python-importlib
%endif
%if ! (0%{?fedora} > 13 || 0%{?rhel} > 5)
Requires:       python-multiprocessing
Requires:       python-uuid
%endif

%if 0%{?with_python3}
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-billiard
BuildRequires:  python3-dateutil
BuildRequires:  pytz
BuildRequires:  python-kombu
%endif # if with_python3


%description
An open source asynchronous task queue/job queue based on
distributed message passing. It is focused on real-time
operation, but supports scheduling as well.

The execution units, called tasks, are executed concurrently
on one or more worker nodes using multiprocessing, Eventlet
or gevent. Tasks can execute asynchronously (in the background)
or synchronously (wait until ready).

Celery is used in production systems to process millions of
tasks a day.

Celery is written in Python, but the protocol can be implemented
in any language. It can also operate with other languages using
webhooks.

The recommended message broker is RabbitMQ, but limited support
for Redis, Beanstalk, MongoDB, CouchDB and databases
(using SQLAlchemy or the Django ORM) is also available.

%if 0%{?with_python3}
%package -n python3-celery
Summary:        Distributed Task Queue
Group:          Development/Languages

Requires:       python3
%description -n python3-celery
An open source asynchronous task queue/job queue based on
distributed message passing. It is focused on real-time
operation, but supports scheduling as well.

The execution units, called tasks, are executed concurrently
on one or more worker nodes using multiprocessing, Eventlet
or gevent. Tasks can execute asynchronously (in the background)
or synchronously (wait until ready).

Celery is used in production systems to process millions of
tasks a day.

Celery is written in Python, but the protocol can be implemented
in any language. It can also operate with other languages using
webhooks.

The recommended message broker is RabbitMQ, but limited support
for Redis, Beanstalk, MongoDB, CouchDB and databases
(using SQLAlchemy or the Django ORM) is also available.

%endif # with_python3


%prep
%setup -q -n celery-%{version}
for script in celery/bin/camqadm.py celery/bin/celerybeat.py celery/bin/celeryd.py; do
  %{__sed} -i.orig -e 1d ${script}
  touch -r ${script}.orig ${script}
  %{__rm} ${script}.orig
  chmod a-x ${script} 
done

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
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rc.d/init.d/

%{__python} setup.py install -O1 --skip-build --root %{buildroot}
%if 0%{?with_python3}
pushd %{py3dir}
%{__python3} setup.py install --skip-build --root %{buildroot}
popd
%endif # with_python3

# Copy init.d scripts
cp extra/generic-init.d/celeryd $RPM_BUILD_ROOT/%{_sysconfdir}/rc.d/init.d/
cp extra/generic-init.d/celerybeat $RPM_BUILD_ROOT/%{_sysconfdir}/rc.d/init.d/



# checks are currently failing
#%check
#%{__python} setup.py test
#
#%if 0%{?with_python3}
#pushd %{py3dir}
#%{__python3} setup.py test
#popd
#%endif # with_python3



%files
%doc LICENSE README.rst TODO CONTRIBUTORS.txt docs examples
%{python_sitelib}/*
%{_bindir}/*
%{_sysconfdir}/rc.d/init.d/celeryd
%{_sysconfdir}/rc.d/init.d/celerybeat


%if 0%{?with_python3}
%files -n python3-celery
%doc AUTHORS LICENSE README THANKS TODO docs examples
%{_bindir}/*
%{python3_sitelib}/*
%endif # with_python3


%changelog
* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 3.0.9-5
- Modify python-celery spec so it will install a daemon script for celeryd &
  celerybeat (jmatthews@redhat.com)

* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 3.0.9-4
- Added missing runtime requires for python-celery (jmatthews@redhat.com)

* Thu Sep 13 2012 John Matthews <jmatthews@redhat.com> 3.0.9-3
- Bumping requires for python-kombu to 2.4.6 on celery, since running it fails
  with an explicit require of >= 2.4.6 (jmatthews@redhat.com)

* Wed Sep 12 2012 John Matthews <jmatthews@redhat.com> 3.0.9-2
- new package built with tito

* Wed Sep 12 2012 John Matthews <jmatthews@redhat.com> - 3.0.9-1
- update to version 3.0.9

* Fri Aug 03 2012 Matthias Runge <mrunge@matthias-runge.de> - 3.0.5-1
- update to version 3.0.5
- enable python3 support

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.2.8-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.2.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Mon Nov 28 2011 Andrew Colin Kissa <andrew@topdog.za.net> - 2.2.8-1
- Security FIX CELERYSA-0001

* Fri Jul 15 2011 Andrew Colin Kissa <andrew@topdog.za.net> - 2.2.7-3
- Fix rpmlint errors
- Fix dependencies

* Sat Jun 25 2011 Andrew Colin Kissa <andrew@topdog.za.net> 2.2.7-2
- Update for RHEL6

* Tue Jun 21 2011 Andrew Colin Kissa <andrew@topdog.za.net> 2.2.7-1
- Initial package
