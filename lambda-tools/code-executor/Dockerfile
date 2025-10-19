FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.11

# Install Node.js 16 from Amazon Linux Extras (compatible with AL2)
RUN yum install -y https://rpm.nodesource.com/pub_16.x/nodistro/repo/nodesource-release-nodistro-1.noarch.rpm && \
    yum install -y nodejs --setopt=nodesource-nodejs.module_hotfixes=1 && \
    yum clean all

# Copy function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD ["lambda_function.lambda_handler"]