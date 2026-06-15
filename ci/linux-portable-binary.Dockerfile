# Debian Bookworm (stable).
# Used to produce a portable Linux binary of PyOxidizer via a containerized build
# with a pinned toolchain. The resulting binary is statically linked against musl.
FROM debian:bookworm-slim
MAINTAINER Gregory Szorc <gregory.szorc@gmail.com>

RUN groupadd -g 1000 build && \
    useradd -u 1000 -g 1000 -d /build -s /bin/bash -m build && \
    mkdir /tools && \
    chown -R build:build /build /tools

ENV HOME=/build \
    SHELL=/bin/bash \
    USER=build \
    LOGNAME=build \
    HOSTNAME=builder \
    DEBIAN_FRONTEND=noninteractive

CMD ["/bin/bash", "--login"]
WORKDIR '/build'

RUN ( echo 'quiet "true";'; \
      echo 'APT::Get::Assume-Yes "true";'; \
      echo 'APT::Install-Recommends "false";'; \
      echo 'Acquire::Retries "5";'; \
    ) > /etc/apt/apt.conf.d/99builder

RUN apt-get update && apt-get install --no-install-recommends \
  ca-certificates \
  curl \
  file \
  gcc \
  gcc-multilib \
  make \
  musl-tools \
  xz-utils

USER build

# Install Rust toolchain via rustup.
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > rustup-init.sh && \
  chmod +x rustup-init.sh && \
  ./rustup-init.sh -y --default-toolchain 1.82.0 --profile minimal && \
  ~/.cargo/bin/rustup target add x86_64-unknown-linux-musl

# Install a recent Python for build-time scripting.
RUN curl -L https://github.com/indygreg/python-build-standalone/releases/download/20260602/cpython-3.11.15+20260602-x86_64-unknown-linux-gnu-install_only.tar.gz > python.tar.gz && \
  tar -xf python.tar.gz && \
  rm python.tar.gz && \
  echo 'export PATH="$HOME/python/bin:$PATH"' >> ~/.bashrc

# Force a snapshot of the Cargo index into the image. This should hopefully
# speed up subsequent operations needing to fetch the index.
RUN ~/.cargo/bin/cargo init cargo-fetch && \
  cd cargo-fetch && \
  echo 'pyembed = "0"' >> Cargo.toml && \
  ~/.cargo/bin/cargo update && \
  cd && \
  rm -rf cargo-fetch
