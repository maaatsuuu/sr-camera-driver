#!/bin/bash

find . -not -path "*/external/*" -name "*\.py" | xargs yapf3 -i {} \;
