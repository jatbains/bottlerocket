%global goproject github.com/containernetworking
%global gorepo cni
%global goimport %{goproject}/%{gorepo}

%global gover 0.8.0
%global rpmver %{gover}

%global _dwz_low_mem_die_limit 0

Name: %{_cross_os}%{gorepo}
Version: %{rpmver}
Release: 1%{?dist}
Summary: Plugins for container networking
License: Apache-2.0
URL: https://%{goimport}
Source0: https://%{goimport}/archive/v%{gover}/%{gorepo}-%{gover}.tar.gz
BuildRequires: git
BuildRequires: %{_cross_os}glibc-devel
Requires: %{_cross_os}iptables

%description
%{summary}.

%prep
%autosetup -Sgit -n %{gorepo}-%{gover} -p1
%cross_go_setup %{gorepo}-%{gover} %{goproject} %{goimport}

%build
%cross_go_configure %{goimport}
go build -buildmode=pie -ldflags=-linkmode=external -o "bin/cnitool" %{goimport}/cnitool

%install
install -d %{buildroot}%{_cross_factorydir}/opt/cni/bin
install -p -m 0755 bin/cnitool %{buildroot}%{_cross_factorydir}/opt/cni/bin

%files
%license LICENSE
%{_cross_attribution_file}
%dir %{_cross_factorydir}/opt/cni/bin
%{_cross_factorydir}/opt/cni/bin/cnitool

%changelog
