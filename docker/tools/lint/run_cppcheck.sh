#!/bin/bash

if [[ ! -d .git ]]; then
  echo "Run this script in top directory."
  exit 1
fi
cppcheck --enable=all \
  -iexternal \
  --inline-suppr \
  --suppressions-list=./cppcheck_suppressions.txt ./
