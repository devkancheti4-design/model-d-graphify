#!/bin/sh
# LOCOMO is not redistributed here. This fetches the public file from its authors' repository (snap-research/locomo).
mkdir -p "$(dirname "$0")/locomo/data"
curl -sL -o "$(dirname "$0")/locomo/data/locomo10.json" https://raw.githubusercontent.com/snap-research/locomo/main/data/locomo10.json
echo "saved $(dirname "$0")/locomo/data/locomo10.json"
