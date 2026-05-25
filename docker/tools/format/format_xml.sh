#!/bin/bash

find . \( -name "*\.xml" -o -name "*\.launch" -o -name "*\.test" \) -exec xmllint --format \
  --output {} {} \;
