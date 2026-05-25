#!/bin/bash

find . -name "*\.sh" -exec shfmt -w -i 2 -ci {} \;
