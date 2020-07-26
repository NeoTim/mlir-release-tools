# Build:
#   docker build -t gcr.io/iree-oss/manylinux2014-bazel-x64:latest manylinux2014-bazel-x64
# Generate launch script:
#   docker run gcr.io/iree-oss/manylinux2014-bazel-x64:latest > dockcross-manylinux2014-bazel-x64
#   chmod a+x dockcross-manylinux2014-bazel-x64
# Get a shell:
#   ./dockcross-manylinux2014-bazel-x64 bash
FROM dockcross/manylinux2014-x64
ENV DEFAULT_DOCKCROSS_IMAGE gcr.io/iree-oss/manylinux2014-bazel-x64
RUN yum install -y java-1.8.0-openjdk-devel
RUN rm -Rf /usr/include/c++
RUN curl https://storage.googleapis.com/install-cache-iree-oss/binaries/bazel-3.4.1-centos6 > /usr/local/bin/bazel-3.4.1
RUN chmod a+x /usr/local/bin/bazel-3.4.1
RUN ln -s bazel-3.4.1 /usr/local/bin/bazel
