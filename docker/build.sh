#!/bin/bash -ex
steward_version=$(python3 -c "import steward; print(steward.__version__)")
docker build --network host -t steward:$steward_version -f docker/Dockerfile .
docker tag steward:$steward_version steward:latest
