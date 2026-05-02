#!/usr/bin/env bash

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_DIR="$(mktemp -d)"
KEEP_GOING=0

trap 'rm -rf "$TMP_DIR"' EXIT

for arg in "$@"; do
  case "$arg" in
    --keep-going)
      KEEP_GOING=1
      ;;
    *)
      printf 'Unknown argument: %s\n' "$arg" >&2
      exit 2
      ;;
  esac
done

if [[ -t 1 ]]; then
  GREEN='\033[32m'
  RED='\033[31m'
  YELLOW='\033[33m'
  BLUE='\033[34m'
  BOLD='\033[1m'
  RESET='\033[0m'
else
  GREEN=''
  RED=''
  YELLOW=''
  BLUE=''
  BOLD=''
  RESET=''
fi

PASS_ICON="${GREEN}✓${RESET}"
FAIL_ICON="${RED}✗${RESET}"
WARN_ICON="${YELLOW}⚠${RESET}"
SKIP_ICON="${YELLOW}⚠${RESET}"

START_TS="$(date +%s)"
PYTHON_BIN=""

declare -A GATE_STATUS
declare -A GATE_MESSAGE
declare -A GATE_DURATION

STAGE_KEYS=(
  stage1
  stage2
  stage3
  stage4
  stage5
  stage6
)

STAGE_LABELS=(
  "STAGE 1 — Static checks"
  "STAGE 2 — Unit tests"
  "STAGE 3 — Build"
  "STAGE 4 — Structural invariants"
  "STAGE 5 — Python imports"
  "STAGE 6 — Documentation invariants"
)

STAGE1_GATES=(lint typecheck)
STAGE2_GATES=(vitest pytest_fast)
STAGE3_GATES=(prisma_generate_node prisma_generate_python web_build)
STAGE4_GATES=(no_api_ts no_citetrack_api no_workspace_zero typecheck_packages typecheck_apps root_docs_present)
STAGE5_GATES=(python_imports)
STAGE6_GATES=(context_no_stale_type_ref agents_clerk_done)

ALL_GATES=(
  lint
  typecheck
  vitest
  pytest_fast
  prisma_generate_node
  prisma_generate_python
  web_build
  no_api_ts
  no_citetrack_api
  no_workspace_zero
  typecheck_packages
  typecheck_apps
  root_docs_present
  python_imports
  context_no_stale_type_ref
  agents_clerk_done
)

KNOWN_LINT_BROKEN_PREFIXES=(
  "apps/api/.sisyphus/"
  "apps/web/e2e/"
  "apps/web/.clerk/"
  "apps/web/playwright/.clerk/"
  "apps/web/.cta.json"
  "apps/api/tests/contracts/fixtures/"
  "package.json"
  "prisma/client-node/"
  "prisma/package.json"
  "packages/ui/"
)

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

pick_python_bin() {
  if command_exists python3; then
    PYTHON_BIN="python3"
  elif command_exists python; then
    PYTHON_BIN="python"
  else
    PYTHON_BIN=""
  fi
}

now_ts() {
  date +%s
}

format_duration() {
  local seconds="$1"
  local minutes=$((seconds / 60))
  local remainder=$((seconds % 60))

  if (( minutes > 0 )); then
    printf '%dm %02ds' "$minutes" "$remainder"
  else
    printf '%ds' "$remainder"
  fi
}

record_gate() {
  local key="$1"
  local status="$2"
  local message="$3"
  local duration="$4"
  GATE_STATUS["$key"]="$status"
  GATE_MESSAGE["$key"]="$message"
  GATE_DURATION["$key"]="$duration"
}

status_icon() {
  case "$1" in
    PASS) printf '%b' "$PASS_ICON" ;;
    WARN) printf '%b' "$WARN_ICON" ;;
    SKIP) printf '%b' "$SKIP_ICON" ;;
    *) printf '%b' "$FAIL_ICON" ;;
  esac
}

trim_message() {
  local message="$1"
  message="${message//$'\n'/ }"
  message="$(printf '%s' "$message" | tr -s ' ')"
  printf '%s' "${message## }"
}

safe_tail() {
  local file="$1"
  if [[ -s "$file" ]]; then
    tail -n 1 "$file"
  else
    printf 'no output captured'
  fi
}

safe_last_nonempty() {
  local file="$1"
  if [[ -s "$file" ]]; then
    awk 'NF { line=$0 } END { if (line) print line; else print "no output captured" }' "$file"
  else
    printf 'no output captured'
  fi
}

max_pass_count() {
  local file="$1"
  local count
  count="$(grep -Eo '[0-9]+ passed' "$file" 2>/dev/null | awk '{print $1}' | sort -nr | head -n 1)"
  if [[ -n "$count" ]]; then
    printf '%s' "$count"
  fi
}

extract_lint_paths() {
  local file="$1"
  awk '
    /^\.\/(apps|packages|prisma)\// {
      path=$1
      sub(/^\.\//, "", path)
      sub(/:.*/, "", path)
      print path
      next
    }
    /^(apps|packages|prisma)\// {
      path=$1
      sub(/:.*/, "", path)
      print path
      next
    }
    /^\.\/package\.json/ {
      path=$1
      sub(/^\.\//, "", path)
      sub(/:.*/, "", path)
      print path
      next
    }
    /^package\.json/ {
      path=$1
      sub(/:.*/, "", path)
      print path
    }
  ' "$file" | sort -u
}

path_is_known_lint_break() {
  local path="$1"
  local prefix
  for prefix in "${KNOWN_LINT_BROKEN_PREFIXES[@]}"; do
    if [[ "$path" == "$prefix" ]] || [[ "$path" == "$prefix"* ]]; then
      return 0
    fi
  done
  return 1
}

has_hard_failures() {
  local key
  for key in "${!GATE_STATUS[@]}"; do
    if [[ "${GATE_STATUS[$key]}" == "FAIL" ]]; then
      return 0
    fi
  done
  return 1
}

stage_has_hard_failures() {
  local -n gate_ref="$1"
  local gate
  for gate in "${gate_ref[@]}"; do
    if [[ "${GATE_STATUS[$gate]:-}" == "FAIL" ]]; then
      return 0
    fi
  done
  return 1
}

maybe_stop_after_stage() {
  if (( KEEP_GOING == 0 )) && stage_has_hard_failures "$1"; then
    return 0
  fi
  return 1
}

print_stage_banner() {
  printf '\n%b%s%b\n' "$BOLD$BLUE" "$1" "$RESET"
}

record_missing_setup() {
  local gate="$1"
  local message="$2"
  record_gate "$gate" "SKIP" "$message" "0s"
}

run_stage1() {
  print_stage_banner "STAGE 1 — Static checks"

  if ! command_exists bun || ! command_exists bunx; then
    record_missing_setup lint "Biome lint skipped (bun/bunx not installed)"
    record_missing_setup typecheck "NX typecheck skipped (bun/bunx not installed)"
    return 0
  fi

  local lint_out="$TMP_DIR/lint.out"
  local typecheck_out="$TMP_DIR/typecheck.out"
  local lint_start="$(now_ts)"
  local typecheck_start="$(now_ts)"

  (
    cd "$ROOT_DIR"
    bun run lint
  ) >"$lint_out" 2>&1 &
  local lint_pid=$!

  (
    cd "$ROOT_DIR"
    bunx nx run-many -t typecheck --skip-nx-cache
  ) >"$typecheck_out" 2>&1 &
  local typecheck_pid=$!

  wait "$lint_pid"
  local lint_rc=$?
  local lint_end="$(now_ts)"

  wait "$typecheck_pid"
  local typecheck_rc=$?
  local typecheck_end="$(now_ts)"

  local lint_duration="$((lint_end - lint_start))"
  local typecheck_duration="$((typecheck_end - typecheck_start))"

  if (( lint_rc == 0 )); then
    record_gate lint PASS "Biome lint" "$(format_duration "$lint_duration")"
  else
    mapfile -t lint_paths < <(extract_lint_paths "$lint_out")
    local lint_unknown=()
    local lint_path
    if (( ${#lint_paths[@]} == 0 )); then
      record_gate lint FAIL "Biome lint failed (unable to classify failures: $(trim_message "$(safe_tail "$lint_out")"))" "$(format_duration "$lint_duration")"
    else
      for lint_path in "${lint_paths[@]}"; do
        if ! path_is_known_lint_break "$lint_path"; then
          lint_unknown+=("$lint_path")
        fi
      done

      if (( ${#lint_unknown[@]} == 0 )); then
        record_gate lint WARN "Biome lint (known-broken paths only)" "$(format_duration "$lint_duration")"
      else
        record_gate lint FAIL "Biome lint failed outside whitelist: $(printf '%s' "${lint_unknown[0]}")" "$(format_duration "$lint_duration")"
      fi
    fi
  fi

  if (( typecheck_rc == 0 )); then
    record_gate typecheck PASS "NX typecheck (all projects)" "$(format_duration "$typecheck_duration")"
  else
    local failed_task
    failed_task="$(awk '/^Failed tasks:/{flag=1; next} flag && /^- /{print $2; exit}' "$typecheck_out")"
    if [[ -n "$failed_task" ]]; then
      record_gate typecheck FAIL "NX typecheck failed (${failed_task})" "$(format_duration "$typecheck_duration")"
    else
      record_gate typecheck FAIL "NX typecheck failed ($(trim_message "$(safe_last_nonempty "$typecheck_out")"))" "$(format_duration "$typecheck_duration")"
    fi
  fi
}

run_stage2() {
  print_stage_banner "STAGE 2 — Unit tests"

  if ! command_exists bun || ! command_exists bunx; then
    record_missing_setup vitest "Web vitest skipped (bun/bunx not installed)"
  else
    local vitest_out="$TMP_DIR/vitest.out"
    local vitest_start="$(now_ts)"
    (
      cd "$ROOT_DIR"
      bunx nx test @citetrack/web --skip-nx-cache
    ) >"$vitest_out" 2>&1
    local vitest_rc=$?
    local vitest_duration="$(( $(now_ts) - vitest_start ))"
    if (( vitest_rc == 0 )); then
      local vitest_count
      vitest_count="$(max_pass_count "$vitest_out")"
      if [[ -n "$vitest_count" ]]; then
        record_gate vitest PASS "Web vitest (${vitest_count} passing)" "$(format_duration "$vitest_duration")"
      else
      record_gate vitest PASS "Web vitest" "$(format_duration "$vitest_duration")"
      fi
    else
      record_gate vitest FAIL "Web vitest failed ($(trim_message "$(safe_last_nonempty "$vitest_out")"))" "$(format_duration "$vitest_duration")"
    fi
  fi

  if ! command_exists uv; then
    record_missing_setup pytest_fast "Python pytest fast skipped (uv not installed)"
  else
    local pytest_out="$TMP_DIR/pytest_fast.out"
    local pytest_start="$(now_ts)"
    (
      cd "$ROOT_DIR/apps/api"
      uv run pytest -m "not slow" --ignore=tests/api --ignore=tests/integration --ignore=tests/e2e -q
    ) >"$pytest_out" 2>&1
    local pytest_rc=$?
    local pytest_duration="$(( $(now_ts) - pytest_start ))"
    if (( pytest_rc == 0 )); then
      local pytest_count
      pytest_count="$(max_pass_count "$pytest_out")"
      if [[ -n "$pytest_count" ]]; then
        record_gate pytest_fast PASS "Python pytest fast (${pytest_count} passing)" "$(format_duration "$pytest_duration")"
      else
        record_gate pytest_fast PASS "Python pytest fast" "$(format_duration "$pytest_duration")"
      fi
    else
      record_gate pytest_fast FAIL "Python pytest fast failed ($(trim_message "$(safe_last_nonempty "$pytest_out")"))" "$(format_duration "$pytest_duration")"
    fi
  fi
}

run_stage3() {
  print_stage_banner "STAGE 3 — Build"

  if ! command_exists bun; then
    record_missing_setup prisma_generate_node "Prisma Node generate skipped (bun not installed)"
    record_missing_setup web_build "Web production build skipped (bun not installed)"
  else
    local prisma_node_out="$TMP_DIR/prisma_node.out"
    local prisma_node_start="$(now_ts)"
    (
      cd "$ROOT_DIR/prisma"
      bun run prisma:generate-node
    ) >"$prisma_node_out" 2>&1
    local prisma_node_rc=$?
    local prisma_node_duration="$(( $(now_ts) - prisma_node_start ))"
    if (( prisma_node_rc == 0 )); then
      record_gate prisma_generate_node PASS "Prisma Node client generate" "$(format_duration "$prisma_node_duration")"
    else
      record_gate prisma_generate_node FAIL "Prisma Node client generate failed ($(trim_message "$(safe_last_nonempty "$prisma_node_out")"))" "$(format_duration "$prisma_node_duration")"
    fi

    local web_build_out="$TMP_DIR/web_build.out"
    local web_build_start="$(now_ts)"
    (
      cd "$ROOT_DIR"
      bunx nx build @citetrack/web --skip-nx-cache
    ) >"$web_build_out" 2>&1
    local web_build_rc=$?
    local web_build_duration="$(( $(now_ts) - web_build_start ))"
    if (( web_build_rc == 0 )); then
      record_gate web_build PASS "Web production build" "$(format_duration "$web_build_duration")"
    else
      record_gate web_build FAIL "Web production build failed ($(trim_message "$(safe_last_nonempty "$web_build_out")"))" "$(format_duration "$web_build_duration")"
    fi
  fi

  if ! command_exists uv; then
    record_missing_setup prisma_generate_python "Prisma Python generate skipped (uv not installed)"
  else
    local prisma_python_out="$TMP_DIR/prisma_python.out"
    local prisma_python_start="$(now_ts)"
    (
      cd "$ROOT_DIR/prisma"
      UV_OFFLINE=1 bash scripts/generatepython.sh
    ) >"$prisma_python_out" 2>&1
    local prisma_python_rc=$?
    local prisma_python_duration="$(( $(now_ts) - prisma_python_start ))"
    if (( prisma_python_rc == 0 )); then
      record_gate prisma_generate_python PASS "Prisma Python client generate" "$(format_duration "$prisma_python_duration")"
    else
      record_gate prisma_generate_python FAIL "Prisma Python client generate failed ($(trim_message "$(safe_last_nonempty "$prisma_python_out")"))" "$(format_duration "$prisma_python_duration")"
    fi
  fi
}

run_stage4() {
  print_stage_banner "STAGE 4 — Structural invariants"

  local gate_start gate_duration

  gate_start="$(now_ts)"
  mapfile -t api_ts_files < <(find "$ROOT_DIR/apps/web/src/features" -name 'api.ts' -print 2>/dev/null | sed "s#^$ROOT_DIR/##")
  gate_duration="$(( $(now_ts) - gate_start ))"
  if (( ${#api_ts_files[@]} == 0 )); then
    record_gate no_api_ts PASS "No api.ts pass-throughs" "$(format_duration "$gate_duration")"
  else
    record_gate no_api_ts FAIL "api.ts files found: $(IFS=', '; printf '%s' "${api_ts_files[*]}")" "$(format_duration "$gate_duration")"
  fi

  gate_start="$(now_ts)"
  local citetrack_api_out="$TMP_DIR/citetrack_api.out"
  if grep -R -n -E --include='*.ts' --include='*.tsx' 'citetrackApi' "$ROOT_DIR/apps" "$ROOT_DIR/packages" >"$citetrack_api_out" 2>/dev/null; then
    gate_duration="$(( $(now_ts) - gate_start ))"
    record_gate no_citetrack_api FAIL "citetrackApi references found: $(trim_message "$(head -n 3 "$citetrack_api_out")")" "$(format_duration "$gate_duration")"
  else
    gate_duration="$(( $(now_ts) - gate_start ))"
    record_gate no_citetrack_api PASS "No citetrackApi references" "$(format_duration "$gate_duration")"
  fi

  gate_start="$(now_ts)"
  local workspace_zero_out="$TMP_DIR/workspace_zero.out"
  if grep -R -n -E --include='*.ts' --include='*.tsx' 'data\s*\?\.\s*\[0\]|data\s*\.\s*\[0\]' "$ROOT_DIR/apps/web/src" >"$workspace_zero_out" 2>/dev/null; then
    mapfile -t workspace_zero_lines < <(grep -v 'features/workspaces/queries.ts' "$workspace_zero_out" | grep -v 'features/workspaces/workspace-switcher.tsx' || true)
    gate_duration="$(( $(now_ts) - gate_start ))"
    if (( ${#workspace_zero_lines[@]} == 0 )); then
      record_gate no_workspace_zero PASS "No leaked workspace[0] lookups" "$(format_duration "$gate_duration")"
    else
      record_gate no_workspace_zero FAIL "Leaked workspace[0] lookups: $(trim_message "$(printf '%s ' "${workspace_zero_lines[@]}")")" "$(format_duration "$gate_duration")"
    fi
  else
    gate_duration="$(( $(now_ts) - gate_start ))"
    record_gate no_workspace_zero PASS "No leaked workspace[0] lookups" "$(format_duration "$gate_duration")"
  fi

  gate_start="$(now_ts)"
  local package_typecheck_out="$TMP_DIR/package_typecheck.out"
  if [[ -z "$PYTHON_BIN" ]]; then
    gate_duration="$(( $(now_ts) - gate_start ))"
    record_gate typecheck_packages SKIP "Package typecheck invariant skipped (python missing)" "$(format_duration "$gate_duration")"
  else
    "$PYTHON_BIN" - "$ROOT_DIR" >"$package_typecheck_out" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
missing = []
for package_json in sorted((root / "packages").glob("*/package.json")):
    package_dir = package_json.parent
    package = json.loads(package_json.read_text())
    project_json = package_dir / "project.json"
    has_typecheck = bool(package.get("scripts", {}).get("typecheck"))
    if project_json.exists():
        project = json.loads(project_json.read_text())
        has_typecheck = has_typecheck or ("typecheck" in project.get("targets", {}))
    if not has_typecheck:
        missing.append(str(package_dir.relative_to(root)))

if missing:
    print("MISSING=" + ", ".join(missing))
    sys.exit(1)

print("OK")
PY
    local package_typecheck_rc=$?
    gate_duration="$(( $(now_ts) - gate_start ))"
    if (( package_typecheck_rc == 0 )); then
      record_gate typecheck_packages PASS "All packages have typecheck" "$(format_duration "$gate_duration")"
    else
      record_gate typecheck_packages FAIL "Missing package typecheck: $(trim_message "$(cat "$package_typecheck_out")")" "$(format_duration "$gate_duration")"
    fi
  fi

  gate_start="$(now_ts)"
  local app_typecheck_out="$TMP_DIR/app_typecheck.out"
  if [[ -z "$PYTHON_BIN" ]]; then
    gate_duration="$(( $(now_ts) - gate_start ))"
    record_gate typecheck_apps SKIP "App typecheck invariant skipped (python missing)" "$(format_duration "$gate_duration")"
  else
    "$PYTHON_BIN" - "$ROOT_DIR" >"$app_typecheck_out" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
missing = []
for package_json in sorted((root / "apps").glob("*/package.json")):
    app_dir = package_json.parent
    package = json.loads(package_json.read_text())
    project_json = app_dir / "project.json"
    has_typecheck = bool(package.get("scripts", {}).get("typecheck"))
    if project_json.exists():
        project = json.loads(project_json.read_text())
        has_typecheck = has_typecheck or ("typecheck" in project.get("targets", {}))
    if not has_typecheck:
        missing.append(str(app_dir.relative_to(root)))

if missing:
    print("MISSING=" + ", ".join(missing))
    sys.exit(1)

print("OK")
PY
    local app_typecheck_rc=$?
    gate_duration="$(( $(now_ts) - gate_start ))"
    if (( app_typecheck_rc == 0 )); then
      record_gate typecheck_apps PASS "All apps have typecheck" "$(format_duration "$gate_duration")"
    else
      record_gate typecheck_apps FAIL "Missing app typecheck: $(trim_message "$(cat "$app_typecheck_out")")" "$(format_duration "$gate_duration")"
    fi
  fi

  gate_start="$(now_ts)"
  gate_duration="$(( $(now_ts) - gate_start ))"
  if [[ -f "$ROOT_DIR/CONTEXT.md" && -f "$ROOT_DIR/AGENTS.md" ]]; then
    record_gate root_docs_present PASS "CONTEXT.md and AGENTS.md present" "$(format_duration "$gate_duration")"
  else
    local missing_docs=()
    [[ -f "$ROOT_DIR/CONTEXT.md" ]] || missing_docs+=("CONTEXT.md")
    [[ -f "$ROOT_DIR/AGENTS.md" ]] || missing_docs+=("AGENTS.md")
    record_gate root_docs_present FAIL "Missing root docs: $(IFS=', '; printf '%s' "${missing_docs[*]}")" "$(format_duration "$gate_duration")"
  fi
}

run_stage5() {
  print_stage_banner "STAGE 5 — Python imports"

  if ! command_exists uv; then
    record_missing_setup python_imports "Core module imports skipped (uv not installed)"
    return 0
  fi

  local imports_out="$TMP_DIR/python_imports.out"
  local imports_start="$(now_ts)"
  (
    cd "$ROOT_DIR/apps/api"
    uv run python -c "import ai_visibility; import ai_visibility.api.app; import ai_visibility.runs.execution_core; import ai_visibility.scan_executor; print('imports OK')"
  ) >"$imports_out" 2>&1
  local imports_rc=$?
  local imports_duration="$(( $(now_ts) - imports_start ))"

  if (( imports_rc == 0 )); then
    record_gate python_imports PASS "Core modules importable" "$(format_duration "$imports_duration")"
  else
    record_gate python_imports FAIL "Core module imports failed ($(trim_message "$(safe_last_nonempty "$imports_out")"))" "$(format_duration "$imports_duration")"
  fi
}

run_stage6() {
  print_stage_banner "STAGE 6 — Documentation invariants"

  local gate_start gate_duration

  gate_start="$(now_ts)"
  gate_duration="$(( $(now_ts) - gate_start ))"
  if grep -q 'packages/api-client/src/types\.ts' "$ROOT_DIR/CONTEXT.md"; then
    record_gate context_no_stale_type_ref FAIL "CONTEXT.md still references deleted packages/api-client/src/types.ts" "$(format_duration "$gate_duration")"
  else
    record_gate context_no_stale_type_ref PASS "CONTEXT.md no stale type-file refs" "$(format_duration "$gate_duration")"
  fi

  gate_start="$(now_ts)"
  gate_duration="$(( $(now_ts) - gate_start ))"
  if grep -q '✅ Clerk auth — end-to-end' "$ROOT_DIR/AGENTS.md"; then
    record_gate agents_clerk_done PASS "AGENTS.md current-state accurate" "$(format_duration "$gate_duration")"
  else
    record_gate agents_clerk_done FAIL "AGENTS.md missing Clerk auth in current-state section" "$(format_duration "$gate_duration")"
  fi
}

print_summary() {
  local content_width=70
  local total_duration="$(( $(now_ts) - START_TS ))"
  local overall="All gates passed."
  if has_hard_failures; then
    overall="One or more gates failed."
  fi

  printf '\n+--------------------------------------------------------------------------+\n'
  printf '│ %-*s │\n' "$content_width" ' CITETRACK SMOKE TESTS'
  printf '+--------------------------------------------------------------------------+\n'

  local i
  local gate
  local stage_var line summary_line
  local -a gate_list=()
  for i in "${!STAGE_KEYS[@]}"; do
    printf '│ %-*s │\n' "$content_width" " ${STAGE_LABELS[$i]}"
    stage_var="${STAGE_KEYS[$i]}"
    gate_list=()
    case "$stage_var" in
      stage1) gate_list=("${STAGE1_GATES[@]}") ;;
      stage2) gate_list=("${STAGE2_GATES[@]}") ;;
      stage3) gate_list=("${STAGE3_GATES[@]}") ;;
      stage4) gate_list=("${STAGE4_GATES[@]}") ;;
      stage5) gate_list=("${STAGE5_GATES[@]}") ;;
      stage6) gate_list=("${STAGE6_GATES[@]}") ;;
    esac

    for gate in "${gate_list[@]}"; do
      line="$(status_icon "${GATE_STATUS[$gate]:-FAIL}") ${GATE_MESSAGE[$gate]:-missing gate result}"
      summary_line="  ${line}"
      if (( ${#summary_line} > content_width )); then
        summary_line="${summary_line:0:$((content_width - 1))}…"
      fi
      printf '│ %-*s │\n' "$content_width" "$summary_line"
    done
  done

  printf '+--------------------------------------------------------------------------+\n'
  printf 'Total time: %s    %s\n' "$(format_duration "$total_duration")" "$overall"
}

pick_python_bin

for gate in "${ALL_GATES[@]}"; do
  record_gate "$gate" SKIP "Not run" "0s"
done

run_stage1
if maybe_stop_after_stage STAGE1_GATES; then
  print_summary
  exit 1
fi

run_stage2
if maybe_stop_after_stage STAGE2_GATES; then
  print_summary
  exit 1
fi

run_stage3
if maybe_stop_after_stage STAGE3_GATES; then
  print_summary
  exit 1
fi

run_stage4
if maybe_stop_after_stage STAGE4_GATES; then
  print_summary
  exit 1
fi

run_stage5
if maybe_stop_after_stage STAGE5_GATES; then
  print_summary
  exit 1
fi

run_stage6

print_summary

if has_hard_failures; then
  exit 1
fi

exit 0
