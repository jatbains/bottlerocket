# Building Bottlerocket

If you'd like to build your own image instead of relying on an Amazon-provided image, follow these steps.
You can skip to the [setup guide for Kubernetes](QUICKSTART-EKS.md) or the [setup guide for Amazon ECS](QUICKSTART-ECS.md) to use an existing image in Amazon EC2.
(We're still working on other use cases!)

## Build an image

### Dependencies

#### System Requirements

The build process artifacts and resulting images can consume in excess of 80GB in the local directory.

The build process is also fairly demanding on your CPU, since we build all included software from scratch.
(The first time.  Package builds are cached, and only changes are built afterward.)
The build scales well to 32+ cores.
The first time you build, the fastest machines can take about 12 minutes while slower machines with only a couple cores can take 3-4 hours.

#### Linux

The build system requires certain operating system packages to be installed.

Ensure the following OS packages are installed:

##### Ubuntu

```
apt install build-essential openssl libssl-dev pkg-config liblz4-tool
```

##### Fedora

```
yum install make automake gcc openssl openssl-devel pkg-config lz4 perl-FindBin perl-lib
```


#### Rust

The build system is based on the Rust language.
We recommend you install the latest stable Rust using [rustup](https://rustup.rs/), either from the official site or your development host's package manager.

To organize build tasks, we use [cargo-make](https://sagiegurari.github.io/cargo-make/).
We also use [cargo-deny](https://github.com/EmbarkStudios/cargo-deny) during the build process.
To get these, run:

```
cargo install cargo-make
cargo install cargo-deny --version 0.6.2
```

#### Docker

Bottlerocket uses [Docker](https://docs.docker.com/install/#supported-platforms) to orchestrate package and image builds.

We recommend Docker 19.03 or later.
Builds rely on Docker's integrated BuildKit support, which has received many fixes and improvements in newer versions.

You'll need to have Docker installed and running, with your user account added to the `docker` group.
Docker's [post-installation steps for Linux](https://docs.docker.com/install/linux/linux-postinstall/) will walk you through that.

> Note: If you're on a newer Linux distribution using the unified cgroup hierarchy with cgroups v2, you may need to disable it to work with current versions of runc.
> You'll know this is the case if you see an error like `docker: Error response from daemon: OCI runtime create failed: this version of runc doesn't work on cgroups v2: unknown.`
> Set the kernel parameter `systemd.unified_cgroup_hierarchy=0` in your boot configuration (e.g. GRUB) and reboot.

### Build process

To build an image, run:

```
cargo make
```

This will build an image for the default variant, `aws-k8s-1.17`.
All packages will be built in turn, and then compiled into an `img` file in the `build/images/` directory.

The version number in [Release.toml](Release.toml) will be used in naming the file, and will be used inside the image as the release version.
If you're planning on [publishing your build](PUBLISHING.md), you may want to change the version.

To build an image for a different variant, run:

```
cargo make -e BUILDSYS_VARIANT=my-variant-here
```

To build an image for a different architecture, run:

```
cargo make -e BUILDSYS_ARCH=my-arch-here
```

(You can use variant and arch arguments together, too.)

### Register an AMI

To use the image in Amazon EC2, we need to register the image as an AMI.

For a simple start, pick an [EC2 region](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-available-regions), then run:

```
cargo make ami -e PUBLISH_REGIONS=your-region-here
```

Your new AMI ID will be printed after it's registered.

If you built your image for a different architecture or variant, just use the same arguments here:

```
cargo make ami -e PUBLISH_REGIONS=your-region-here -e BUILDSYS_VARIANT=my-variant-here
```

(There's a lot more detail on building and managing AMIs in the [PUBLISHING](PUBLISHING.md) guide.)

## Use your image

See the [setup guide for Kubernetes](QUICKSTART-EKS.md) or the [setup guide for Amazon ECS](QUICKSTART-ECS.md) for information on running Bottlerocket images.

## Publish your image

See the [PUBLISHING](PUBLISHING.md) guide for information on deploying Bottlerocket images and repositories.

## Building out-of-tree kernel modules

To further extend Bottlerocket, you may want to build extra kernel modules.
The specifics of building an out-of-tree module will vary by project, but the first step is to download the "kmod kit" that contains the kernel headers and toolchain you'll need to use.

### Downloading the kmod kit

kmod kits are included in the official Bottlerocket repos starting with Bottlerocket v1.0.6.
Let's say you want to download the kit for building x86_64 modules for v1.0.6 and variant aws-k8s-1.18.

First, you need tuftool:
```bash
cargo install tuftool
```

Next, you need the Bottlerocket root role, which is used by tuftool to verify the kmod kit.
This will download and verify the root role itself:
```bash
curl -O "https://cache.bottlerocket.aws/root.json"
sha512sum -c <<<"90393204232a1ad6b0a45528b1f7df1a3e37493b1e05b1c149f081849a292c8dafb4ea5f7ee17bcc664e35f66e37e4cfa4aae9de7a2a28aa31ae6ac3d9bea4d5  root.json"
```

Next, set your desired parameters, and download the kmod kit:
```bash
ARCH=x86_64
VERSION=v1.0.6
VARIANT=aws-k8s-1.18

tuftool download . --target-name ${VARIANT}-${ARCH}-kmod-kit-${VERSION}.tar.xz \
   --root ./root.json \
   --metadata-url "https://updates.bottlerocket.aws/2020-07-07/${VARIANT}/${ARCH}/" \
   --targets-url "https://updates.bottlerocket.aws/targets/"
```

### Using the kmod kit

To use the kmod kit, extract it, and update your PATH to use its toolchain:
```bash
tar xf "${VARIANT}-${ARCH}-kmod-kit-${VERSION}.tar.xz"

export CROSS_COMPILE="${ARCH}-bottlerocket-linux-musl-"
export KERNELDIR="${PWD}/${VARIANT}-${ARCH}-kmod-kit-${VERSION}/kernel-devel
export PATH="${PWD}/${VARIANT}-${ARCH}-kmod-kit-${VERSION}/toolchain/usr/bin:${PATH}"
```

Now you can compile modules against the kernel headers in `${KERNELDIR}`.
