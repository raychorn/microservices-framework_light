#!/bin/bash

tail -n 10 /home/ubuntu/microservices-framework_light/scripts/cron-job.log > /home/ubuntu/microservices-framework_light/scripts/cron-job.log.tmp
mv -f /home/ubuntu/microservices-framework_light/scripts/cron-job.log.tmp /home/ubuntu/microservices-framework_light/scripts/cron-job.log
