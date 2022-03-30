%{?!python3_pkgversion:%global python3_pkgversion 3}

%global srcname rpmindex

Name:           %{srcname}
Version:        0.1.0
Release:        1%{?dist}
Summary:        Display index of rpm repository
License:        GPLv3
URL:            http://www.nieslony.at/rpmindex
Source0:        %{srcname}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools

Requires:       python%{python3_pkgversion}-%{srcname}
Requires:       python%{python3_pkgversion}-flask python%{python3_pkgversion}-pyyaml

Recommends:     httpd python%{python3_pkgversion}-mod_wsgi

%{?python_enable_dependency_generator}

%description
Web application to display index of rpm repository

%package -n python%{python3_pkgversion}-%{srcname}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{srcname}}

%description -n python%{python3_pkgversion}-%{srcname}
Python package for %{srcname}

%prep
%autosetup -p1 -n %{srcname}-%{version}

%build
%py3_build

%install
rm -rf $RPM_BUILD_ROOT
%py3_install

mkdir -vp $RPM_BUILD_ROOT/var/www/rpmindex/{static,templates}
mkdir -vp $RPM_BUILD_ROOT/etc/httpd/conf.d
install rpmindex.wsgi rpmindex.yml $RPM_BUILD_ROOT/var/www/rpmindex
install -v -D rpmindex/web/static/* -t $RPM_BUILD_ROOT/var/www/rpmindex/static
install -v -D rpmindex/web/templates/* -t $RPM_BUILD_ROOT/var/www/rpmindex/templates
install -v rpmindex.conf $RPM_BUILD_ROOT/etc/httpd/conf.d/rpmindex.conf

%files -n  python%{python3_pkgversion}-%{srcname}
%{!?_licensedir:%global license %%doc}
%license LICENSE
%doc README.md
# For noarch packages: sitelib
%{python3_sitelib}/%{srcname}
%{python3_sitelib}/%{srcname}-%{version}-py%{python3_version}.egg-info

%files
/var/www/rpmindex
%config(noreplace) /etc/httpd/conf.d/rpmindex.conf
