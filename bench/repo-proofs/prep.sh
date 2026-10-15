#!/bin/zsh
# Fetch each snapshot, build Graphify's graph (output outside the repo) and Model D's index.
W=~/neos/outreach/repo-proofs; G=~/neos/outreach/graphify-pr/graphify
export OCM_OFFLINE=1 HF_HUB_OFFLINE=1
for spec in "plane makeplane/plane 3618ffc2c38eb793a0b6c04e6fbac6d6b1f14eef" "signoz SigNoz/signoz 8a0c5bc3c8a9ee41d6bf10c7cf30845f5643d3a9"; do
  set -- ${=spec}; n=$1; repo=$2; sha=$3
  mkdir -p $W/repos/$n && cd $W/repos/$n && git init -q 2>/dev/null; git fetch -q --depth 1 https://github.com/$repo $sha && git checkout -q FETCH_HEAD
  echo "$n at $(git rev-parse --short HEAD), $(git ls-files | wc -l | tr -d ' ') files"
  s=$(date +%s); (cd $G && GRAPHIFY_OUT=$W/graphs/$n/graphify-out uv run --no-sync graphify update $W/repos/$n --no-cluster > $W/graphs/$n.log 2>&1); echo "  graphify graph in $(( $(date +%s) - s ))s"
  s=$(date +%s); r=$(PYTHONPATH=~/optimal-context-mapping ~/ocm-eval/venvs/t021/bin/python -m ocm build $W/repos/$n --out $W/ws/$n 2>&1 | grep -o "workspace ready.*"); echo "  model d index in $(( $(date +%s) - s ))s: $r"
done
echo "PREP DONE"
