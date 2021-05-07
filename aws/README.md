# Automated ECR for AWS Projects

## Table of Contents

- [Automated ECR for AWS Projects](#automated-ecr-for-aws-projects)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
    - [docker-compose ECS Integration](#docker-compose-ecs-integration)
  - [Getting Started](#getting-started)
    - [Terraform Support](#terraform-support)
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
    - [--aws_region](#--aws_region)
    - [--terraform](#--terraform)
    - [--terraform=/dir](#--terraformdir)
    - [--provider=aws|azure|gcloud](#--providerawsazuregcloud)
    - [--aws_ecs_cluster=cluster-name](#--aws_ecs_clustercluster-name)
    - [--aws_compute_engine=FARGATE](#--aws_compute_enginefargate)
    - [--json](#--json)
  - [Typical Usage(s)](#typical-usages)
    - [Auto-ECR](#auto-ecr)
      - [Get Help](#get-help)
      - [Push Images (verbose)](#push-images-verbose)
      - [Clean ECR and Push Images (verbose)](#clean-ecr-and-push-images-verbose)
      - [Clean ECR and Push Images with Detailed ECR Reports (verbose)](#clean-ecr-and-push-images-with-detailed-ecr-reports-verbose)
      - [Clean ECR and Push Images (Security Scan Images) with Detailed ECR Reports (verbose)](#clean-ecr-and-push-images-security-scan-images-with-detailed-ecr-reports-verbose)
    - [Auto-Terraform](#auto-terraform)
      - [Get Help](#get-help-1)
      - [Typical Auto Terraform Session](#typical-auto-terraform-session)


## About

Automates the Docker Push for AWS ECR via git bash for Windows 10. This assumes your paths are setup correctly.

### docker-compose ECS Integration

[Docker Compose ECS Integration](https://docs.docker.com/cloud/ecs-integration/)

## Getting Started

Not gonna work in Windows via "git bash".

### Terraform Support

The Terraform Automation builds the main.tf file which you can use to do a "terraform apply" to repeat the deployment however every time the terraform automation runs it will rebuild and reapply the main.tf file. (See the script named "./scripts/terraform-cli-installer.sh" to install the terraform command line which is done automatically when you run the terraform automation.)

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
sudo ./commander.sh
```

3. Push your Images into ECR by issuing the following command:

```
./commander.sh [--help] [--verbose] [--push-ecr] [--clean-ecr] [--single] [--scanOnPush] [--timetags] [--detailed] [--terraform] [--terraform=/dir] [--provider=aws|azure|gcloud] [--aws_ecs_cluster=cluster-name] [--json] [--aws_region]
```

## Usage

Use of this Command Line tool can result in the user needing to perform a docker login if this was done from the Linux Command before running this tool.

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

### --aws_region
```
Overrides the AWS region found in the typical AWS Config file, if used.
```

### --terraform

```
Performs Terraform processing on the apparent root directory based on the location of any .env files.  If there is no main.tf file present then one will be created otherwise the main.tf file will be used.
```

### --terraform=/dir

```
Performs Terraform processing on a directory that must exist.  This allows the user to define the directory where the terraform configuration files reside or where they will be created. If there is no main.tf file present then one will be created otherwise the main.tf file will be used.

The main.tf file will be created in the ./terraform directory which will either be the directory you supply as the optional directory for the "--terraform" command line option or it will be defined by the presence of the ".env" file which generally appears in the project root.  If you want to control where the main.tf file lands then define the directory when you issue the "--terraform=./dir" command line option. Please note the directory you use with this option must exist.
```

### --provider=aws|azure|gcloud

```
If used this option must appear AFTER the "--terraform" option and must be one of the acceptable options (aws, azure, or gcloud) and if not one of these then 'aws' will be used.
```

### --aws_ecs_cluster=cluster-name

```
If used this option must appear AFTER the "--terraform" option and must identify the name for the ECS cluster.
```

### --aws_compute_engine=FARGATE

```
This option defaults to FARGATE and is an option for future use.
```

### --json

```
If used this option must appear AFTER the "--terraform" option and saves the docker-compose.yml file as json in the same directory as the source file (for debugging purposes only).
```

## Typical Usage(s)

### Auto-ECR

#### Get Help

```
./commander.sh [--help]
```

#### Push Images (verbose)

```
./commander.sh [--verbose] [--push-ecr]
```

#### Clean ECR and Push Images (verbose)

```
./commander.sh [--verbose] [--push-ecr] [--clean-ecr]
```

#### Clean ECR and Push Images with Detailed ECR Reports (verbose)

```
./commander.sh [--verbose] [--push-ecr] [--clean-ecr] [--detailed]
```

#### Clean ECR and Push Images (Security Scan Images) with Detailed ECR Reports (verbose)

```
./commander.sh [--verbose] [--push-ecr] [--clean-ecr] [--scanOnPush] [--detailed]
```

### Auto-Terraform

#### Get Help

```
./commander.sh [--help]
```

#### Typical Auto Terraform Session

```
./commander.sh --terraform=/dir --provider=aws --aws_ecs_cluster=name-the-cluster --aws_compute_engine=FARGATE --json
```

