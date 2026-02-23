#!/usr/bin/env bash

.venv/Scripts/python.exe -m pre_commit run --all-files --verbose --show-diff-on-failure
