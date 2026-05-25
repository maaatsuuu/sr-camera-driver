#!/bin/bash

find . \( -name "*\.cc" -o -name "*\.h" -o -name "*\.cpp" -o -name "*\.hpp" \) \
  -exec cpplint --quiet {} \;
