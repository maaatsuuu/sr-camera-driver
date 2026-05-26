#########################################################################################
# ROS 2 environment
#########################################################################################

ARG ROS_DISTRO=jazzy
FROM docker.io/osrf/ros:${ROS_DISTRO}-desktop-full

ARG DEBIAN_FRONTEND=noninteractive


#########################################################################################
# Japanese Language Support
#########################################################################################

RUN apt-get update && apt-get install -y --no-install-recommends \
        language-pack-ja-base \
        language-pack-ja \
        fonts-ipafont-gothic \
    && rm -rf /var/lib/apt/lists/*

#########################################################################################
# Japanese Input Module Installation
# Reference: https://zenn.dev/ysuito/articles/c196ae84c95e31
#########################################################################################
RUN apt update && apt install -y --no-install-recommends \
        dbus-x11 \
    && rm -rf /var/lib/apt/lists/*

#########################################################################################
# Set TimeZone
#########################################################################################

ENV TZ='Asia/Tokyo'

#########################################################################################
# Development Tools Installation
#########################################################################################

RUN apt-get update && apt install -y --no-install-recommends \
        bash-completion \
        ca-certificates \
        apt-transport-https \
        curl \
        gosu \
        policykit-1 \
        xvfb \
        iproute2 \
        openssh-server \
        rsync \
        vim \
        git \
        ccache \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

# link python to python3
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 2

# Python virtual environment for pip
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv --prompt ${VIRTUAL_ENV} --system-site-packages ${VIRTUAL_ENV}
ENV PATH=${VIRTUAL_ENV}/bin:${PATH}

#########################################################################################
# ccache setting
#########################################################################################

ENV PATH=/usr/lib/ccache:${PATH}

##############################################
# OpenGL support
# Reference: https://gitlab.com/nvidia/container-images/opengl/blob/ubuntu16.04/glvnd/runtime/Dockerfile
##############################################

ENV LIBGLVND_VERSION="v1.6.0"
ENV nproc=4

RUN apt-get update && apt install -y --no-install-recommends \
        automake \
        autoconf \
        libtool \
        libxext-dev \
        libx11-dev \
        x11proto-gl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/libglvnd
RUN git clone --branch="${LIBGLVND_VERSION}" https://github.com/NVIDIA/libglvnd.git . && \
    ./autogen.sh && \
    ./configure --prefix=/usr/local --libdir=/usr/local/lib/x86_64-linux-gnu && \
    make -j"$(nproc)" install-strip && \
    find /usr/local/lib/x86_64-linux-gnu -type f -name 'lib*.la' -delete

RUN echo '/usr/local/lib/x86_64-linux-gnu' >> /etc/ld.so.conf.d/glvnd.conf && \
    ldconfig

#########################################################################################
# test, format, lint tools installation
#########################################################################################

COPY docker/scripts/install_test_tools.sh .
RUN sed -i "s/sudo //" install_test_tools.sh
RUN /bin/bash -c "apt update && \
                 ./install_test_tools.sh && \
                 rm -rf /var/lib/apt/lists/* && \
                 rm install_test_tools.sh"

COPY docker/requirements/test.txt test.txt
RUN ${VIRTUAL_ENV}/bin/python -m pip install --no-cache-dir -r test.txt && \
    rm -f test.txt

COPY docker/scripts/install_lcov.sh .
RUN sed -i "s/sudo //" install_lcov.sh
RUN /bin/bash -c "./install_lcov.sh && \
                 rm install_lcov.sh"

COPY docker/scripts/install_clang_format.sh .
RUN sed -i "s/sudo //" install_clang_format.sh
RUN /bin/bash -c "apt update && \
                 ./install_clang_format.sh && \
                 rm -rf /var/lib/apt/lists/* && \
                 rm install_clang_format.sh"

COPY docker/requirements/cpplint.txt cpplint.txt
RUN ${VIRTUAL_ENV}/bin/python -m pip install --no-cache-dir -r cpplint.txt && \
    rm -f cpplint.txt

COPY docker/scripts/install_cppcheck.sh .
RUN sed -i "s/sudo //" install_cppcheck.sh
RUN /bin/bash -c "apt update && \
                 ./install_cppcheck.sh && \
                 rm -rf /var/lib/apt/lists/* && \
                 rm install_cppcheck.sh"

COPY docker/scripts/install_yapf3.sh .
RUN sed -i "s/sudo //" install_yapf3.sh
RUN /bin/bash -c "apt update && \
                 ./install_yapf3.sh && \
                 rm -rf /var/lib/apt/lists/* && \
                 rm install_yapf3.sh"

COPY docker/scripts/install_flake8.sh .
RUN sed -i "s/sudo //" install_flake8.sh
RUN /bin/bash -c "apt update && \
                 ./install_flake8.sh && \
                 rm -rf /var/lib/apt/lists/* && \
                 rm install_flake8.sh"

COPY docker/scripts/install_xmllint.sh .
RUN sed -i "s/sudo //" install_xmllint.sh
RUN /bin/bash -c "apt update && \
                 ./install_xmllint.sh && \
                 rm -rf /var/lib/apt/lists/* && \
                 rm install_xmllint.sh"

COPY docker/scripts/install_shfmt.sh .
RUN sed -i "s/sudo //" install_shfmt.sh
RUN /bin/bash -c "apt update && \
                 ./install_shfmt.sh && \
                 rm -rf /var/lib/apt/lists/* && \
                 rm install_shfmt.sh"


#########################################################################################
# ROS related additional package installation
#########################################################################################

COPY docker/scripts/install_ros_packages.sh .
RUN sed -i "s/sudo //" install_ros_packages.sh
RUN /bin/bash -c "apt update && \
                 ./install_ros_packages.sh && \
                 rm -rf /var/lib/apt/lists/* && \
                 rm install_ros_packages.sh"


#########################################################################################
# LiDAR SDK installation
#########################################################################################

# COPY docker/scripts/install_livox_sdk2.sh .
# COPY src/third_party/livox/Livox-SDK2 /tmp/Livox-SDK2
# RUN sed -i "s/sudo //" install_livox_sdk2.sh
# RUN /bin/bash -c "apt update && \
#                  ./install_livox_sdk2.sh /tmp/Livox-SDK2 && \
#                  rm -rf /var/lib/apt/lists/* && \
#                  rm -rf /tmp/Livox-SDK2 && \
#                  rm install_livox_sdk2.sh"


#########################################################################################
# entrypoint generation for workspace initialization
# - delete default user (ubuntu) to avoid conflicts with host user.
# - create user with the same UID and GID as the host user, and switch to that user.
# - user password is same as username for simplicity.
#########################################################################################

COPY docker/resources/_bashrc /tmp/_bashrc
RUN echo '#!/bin/bash' >> /start.sh \
    && echo "userdel -r ubuntu" >> /start.sh \
    && echo "groupadd -g \${3} \${1}" >> /start.sh \
    && echo "useradd -u \${2} -g \${3} \${1} -p \$(perl -se 'print crypt(\${var}, \"\\\$6\\\$saltsalt\")' -- -var=\${1})" >> /start.sh \
    && echo "usermod -G sudo \${1}" >> /start.sh \
    && echo "chown -R \${1}:\${1} /home/\${1}" >> /start.sh \
    && echo "gosu \${1}:\${1} cp /tmp/_bashrc /home/\${1}/.bashrc" >> /start.sh \
    && echo "service dbus start " >> /start.sh \
    && echo "gosu \${1}:\${1} \"/bin/bash\"" >> /start.sh \
    && chmod 755 /start.sh

ENTRYPOINT ["/start.sh"]
