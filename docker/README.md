# ROS 2 Docker

Sample ROS 2 environment in Docker.

## Prerequisites

- docker

## Getting Started

1. Specify ROS distribution and Docker image settings:

    - Edit `image.env` to specify the desired ROS distribution and Docker image.
    Changes will automatically reflect in the `build.sh` and `start_env.sh` scripts.

    ```sh
    ROS_DISTRO=jazzy
    DOCKER_IMAGE_NAME=kjm/ros2/${ROS_DISTRO}
    IMAGE_TAG=latest
    ```

    - Options available : `humble`, `Iron`, `jazzy`, `kilted`
    - Default Distribution is `jazzy`
    - `DOCKER_IMAGE_NAME` controls the repository/name, and `IMAGE_TAG` controls the default tag.
    - `image.env` is loaded with `source`, so variables are evaluated top-down as shell syntax. For example, `DOCKER_IMAGE_NAME=kjm/ros2/${ROS_DISTRO}` expands using the `ROS_DISTRO` defined above it.
    - `build.sh -t {tag}`, `start_env.sh -t {tag}`, and `attach.sh -t {tag}` override `IMAGE_TAG` from `image.env`.

2. Build the Docker image:

    ```sh
    ./build.sh
    ```

    - Override only the image tag for this build:

    ```sh
    ./build.sh -t dev
    ```

    - When you build with a custom tag, use the same tag with `start_env.sh -t {tag}` when starting the container.

3. Prepare files and directories for bind mount (if they do not already exist):

    ```sh
    touch ~/.gitconfig
    mkdir -p ~/.ros ~/.ssh
    ```

4. Prepare local Livox configuration files:

    ```sh
    cd ../tools
    ./copy_assets.sh
    ```

    Existing files are kept. Use `./copy_assets.sh -f` only when you want to overwrite local configuration files.

5. Edit host-specific LiDAR settings:

    Edit `docker/host_cfg.env` from the repository root.

    ```sh
    LIVOX_HOST_IP="192.168.1.50"
    LIVOX_MID360_IP="192.168.1.116"
    LIVOX_FRAME_ID_NAME="mid360_frame"
    LIVOX_POINTCLOUD_TOPIC_NAME="sensor/lidar/livox/front/pointcloud"
    LIVOX_IMU_TOPIC_NAME="sensor/lidar/livox/front/imu"
    ```

6. Apply the host-specific settings:

    ```sh
    cd ../tools
    ./set_host_cfg.sh
    ```

    This updates the Livox config files used by the bringup launch files.

7. Run the container:

    On startup, the container creates a user account with the same username, UID, and GID as the host user.  
    For simplicity, the password for that account is set to the same value as the username.

    - Using the default host directory `./ws` as the bind mount for the container's workspace:

    ```sh
    ./start_env.sh
    ```

    - Using a custom image tag when starting the container:

    ```sh
    ./start_env.sh -t dev
    ```

    - Using a custom workspace host directory as the bind mount for the container's workspace:

    ```sh
    ./start_env.sh -w {path/to/workspace}
    ```

    - Display help information:

    ```sh
    ./start_env.sh -h
    ```

8. Attach to a running container:

    `attach.sh` reads `image.env`, searches for running containers that match `DOCKER_IMAGE_NAME:IMAGE_TAG`, and attaches to the matched container.

    ```sh
    ./attach.sh
    ```

    - Using a custom image tag when attaching to the container:

    ```sh
    ./attach.sh -t dev
    ```

    If multiple containers match the same image and tag, a list is displayed and you can choose one by entering its 0-based index.

## Docker Image Customization

To extend the Docker image with additional packages, add a new file under `requirements/` or `scripts/`, and then add the corresponding installation step to `Dockerfile`.  
The existing `requirements/test.txt`, `scripts/install_test_tools.sh`, and `scripts/install_ros_packages.sh` entries in `Dockerfile` are good reference patterns.

1. Add Python packages under `requirements/` when they should be installed with `pip`.

    These packages are installed into the Python virtual environment created at `/opt/venv` inside the Docker image.  
    When the container starts, `/opt/venv` is automatically activated, so `python` and `pip` use that virtual environment by default.  
    The system Python also remains in the image, so the virtual environment and the base system Python coexist.  
    Because the virtual environment is created with `--system-site-packages`, packages installed in the system Python environment can still be imported and used from the activated virtual environment.  
    If the same package exists in both `/opt/venv` and the system Python environment, the version installed in `/opt/venv` takes precedence.

    Example file:

    ```txt
    # requirements/custom.txt
    requests==2.32.3
    ```

    Example `Dockerfile` entry:

    ```Dockerfile
    COPY ./requirements/custom.txt custom.txt
    RUN ${VIRTUAL_ENV}/bin/python -m pip install --no-cache-dir -r custom.txt && \
        rm -f custom.txt
    ```

2. Add apt packages or ROS packages under `scripts/` when they should be installed by `apt`.

    Example file:

    ```bash
    #!/bin/bash -eu

    sudo apt install -y \
      tmux \
      jq
    ```

    Example `Dockerfile` entry:

    ```Dockerfile
    COPY ./scripts/install_custom_packages.sh .
    RUN sed -i "s/sudo //" install_custom_packages.sh
    RUN /bin/bash -c "apt update && \
                     ./install_custom_packages.sh && \
                     rm -rf /var/lib/apt/lists/* && \
                     rm install_custom_packages.sh"
    ```

3. Place the new `Dockerfile` block near the related existing section so the image definition stays organized.

4. Build a tool from source when the distro package is unavailable or too old.

    The current `lcov` installation is the recommended pattern for this case. It builds from source because the distro package is too old, and the build procedure is kept in `scripts/install_lcov.sh` instead of being written inline in `Dockerfile`.

    Recommended example script:

    ```bash
    #!/bin/bash -eu

    LCOV_VERSION=2.4

    pushd /tmp
    sudo rm -rf lcov-${LCOV_VERSION}

    curl -SL https://github.com/linux-test-project/lcov/releases/download/v${LCOV_VERSION}/lcov-${LCOV_VERSION}.tar.gz | \
      tar -xz

    pushd lcov-${LCOV_VERSION}
    sudo make install
    popd  # back to /tmp

    rm -rf lcov-${LCOV_VERSION}
    popd  # back to original directory
    ```

    Recommended `Dockerfile` entry:

    ```Dockerfile
    COPY ./scripts/install_lcov.sh .
    RUN sed -i "s/sudo //" install_lcov.sh
    RUN /bin/bash -c "./install_lcov.sh && \
                     rm install_lcov.sh"
    ```

    For source builds, prefer this split approach: keep the build logic in a dedicated script under `scripts/`, and keep `Dockerfile` responsible for copying and running that script. This keeps `Dockerfile` shorter and makes the install procedure easier to reuse and maintain.

5. Rebuild the image after updating `Dockerfile`, `requirements/`, or `scripts/`.

    ```sh
    ./build.sh -t custom
    ```
