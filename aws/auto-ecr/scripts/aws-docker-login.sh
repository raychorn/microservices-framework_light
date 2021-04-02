#!/usr/bin/env bash


aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin $1
