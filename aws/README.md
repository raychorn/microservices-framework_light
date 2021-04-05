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
    - [--push-ecr](#--push-ecr)
    - [--single](#--single)
    - [--scanOnPush](#--scanonpush)
    - [--timetags](#--timetags)
    - [--detailed](#--detailed)
  - [Typical Usage(s)](#typical-usages)
    - [Get Help](#get-help)
    - [Push Images (verbose)](#push-images-verbose)
    - [Clean ECR and Push Images (verbose)](#clean-ecr-and-push-images-verbose)
    - [Clean ECR and Push Images with Detailed ECR Reports (verbose)](#clean-ecr-and-push-images-with-detailed-ecr-reports-verbose)
    - [Clean ECR and Push Images (Security Scan Images) with Detailed ECR Reports (verbose)](#clean-ecr-and-push-images-security-scan-images-with-detailed-ecr-reports-verbose)


## About

Automates the Docker Push for AWS ECR via git bash for Windows 10. This assumes your paths are setup correctly.

## Getting Started

Not gonna work in Windows via "git bash"

### Prerequisites

None

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

2. Install the pre-requisites by issuing the following command:

```
sudo ./ecr-push-all.sh
```

3. Push your Images into ECR by issuing the following command:

```
./ecr-push-all.sh [--help] [--verbose] [--push-ecr] [--clean-ecr] [--single] [--scanOnPush] [--timetags] [--detailed]
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

### --push-ecr

```
Pushes all Docker Images into ECR.
```

### --single

```
Pushes all Docker Images into ECR via a single thread or multiple threads when this option is not present.
```

### --scanOnPush

```
Performs scan-on-push when pushing Images into ECR, the default is no scan on push when this option is not used.
```

### --timetags

```
Appends a pseudo-Timestamp on every Image to force all Images to be pushed even when there was no change in the Tag(s).
```

### --detailed

```
Saves a detailed report for each Image pushed. Detailed reports can be found in the "./aws/automated-ecr/reports" directory.
```

## Typical Usage(s)

### Get Help

```
./ecr-push-all.sh [--help]
```

### Push Images (verbose)

```
./ecr-push-all.sh [--verbose] [--push-ecr]
```

### Clean ECR and Push Images (verbose)

```
./ecr-push-all.sh [--verbose] [--push-ecr] [--clean-ecr]
```

### Clean ECR and Push Images with Detailed ECR Reports (verbose)

```
./ecr-push-all.sh [--verbose] [--push-ecr] [--clean-ecr] [--detailed]
```

### Clean ECR and Push Images (Security Scan Images) with Detailed ECR Reports (verbose)

```
./ecr-push-all.sh [--verbose] [--push-ecr] [--clean-ecr] [--scanOnPush] [--detailed]
```
