Name:           python-django-celery
Version:        3.0.9
Release:        6%{?dist}
Summary:        Celery integration with Django

Group:          Development/Libraries
License:        MIT
URL:            http://pypi.python.org/pypi/django-celery
Source0:        http://pypi.python.org/packages/source/d/django-celery/django-celery-%{version}.tar.gz
BuildArch:      noarch
Requires:       python-celery >= 3.0.9
Requires:       Django >= 1.4.1
BuildRequires:  python-devel
BuildRequires:  python-setuptools

%description
django-celery provides Celery integration for Django.
Using the Django ORM and cache backend for storing results,
autodiscovery of task modules for applications listed in
INSTALLED_APPS, and more

%prep
%setup -q -n django-celery-%{version}


%build
CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

 
%files
%doc docs/ CHANGES LICENSE README PKG-INFO
%{python_sitelib}/*.egg-info
%{python_sitelib}/djcelery

%changelog
* Tue Sep 18 2012 John Matthews <jmatthews@redhat.com> 3.0.9-6
- Spec updates (jmatthews@redhat.com)

* Tue Sep 18 2012 John Matthews <jmatthews@redhat.com> 3.0.9-5
- Spec updates (jmatthews@redhat.com)

* Tue Sep 18 2012 John Matthews <jmatthews@redhat.com> 3.0.9-4
- Spec updates (jmatthews@redhat.com)

* Tue Sep 18 2012 John Matthews <jmatthews@redhat.com> 3.0.9-3
- python-django-celery update (jmatthews@redhat.com)

* Tue Sep 18 2012 John Matthews <jmatthews@redhat.com> 3.0.9-2
- new package built with tito

* Tue Sep 18 2012 John Matthews <jmatthews@redhat.com> 3.0.9-1
- Initial RPM

