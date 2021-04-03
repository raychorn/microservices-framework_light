# Automated ECR for AWS Projects

## Table of Contents

- [Automated ECR for AWS Projects](#automated-ecr-for-aws-projects)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
  - [Installing](#installing)
  - [Usage](#usage)
    - [--help](#--help)
    - [--verbose](#--verbose)
    - [--clean-ecr](#--clean-ecr)


## About

Automates the Docker Push for AWS ECR via git bash for Windows 10. This assumes your paths are setup correctly.

## Getting Started

Not gonna work in Windows via "git bash"

### Prerequisites

Requires Docker without sudo.

Add the docker group if it doesn't already exist:

 sudo groupadd docker

Add the connected user "$USER" to the docker group. Change the user name to match your preferred user if you do not want to use your current user:

 sudo gpasswd -a $USER docker

Either do a "newgrp docker" or log out/in to activate the changes to groups.

## Installing

1. Edit the ./.aws/credentials file.

Say what the step will be

```
Put your AWS Credentials into the ./.aws/credentials file.
```

As shown below:

```
[default]
aws_access_key_id = ...
aws_secret_access_key = ...
```

2. Install the aws cli by issuing the following command:

```
./scripts/aws-cli-installer.sh
```

3. Configure aws by issuing the following command:

```
aws configure
```

4. Install the pre-requisites by issuing the following command:

```
sudo ./ecr-push-all.sh
```

5. Push your Images into ECR by issuing the following command:

```
./ecr-push-all.sh [--help] [--verbose] [--push-ecr] [--clean-ecr]
```

## Usage

### --help

```
Display help information about command line options.
```
### --verbose

```
Display verbose information to help diagose issues.
```
### --clean-ecr

```
removes all known repos from the ECR - this is for development purposes only.
```


