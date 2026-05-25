#!/bin/bash

find . -not -path "*/external/*" \
  \( -name "*\.cc" -o -name "*\.h" -o -name "*\.cpp" -o -name "*\.hpp" \) \
  -exec clang-format -i {} \;
