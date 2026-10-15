#!/usr/bin/env bash
set -euo pipefail
usage() { echo "Usage: install.sh DESTINATION [--dry-run]" >&2; exit 2; }
[[ $# -ge 1 && $# -le 2 ]] || usage
dest="$1"
dry_run="${2:-}"
[[ -z "$dry_run" || "$dry_run" == '--dry-run' ]] || usage
src="$(cd "$(dirname "${BASH_SOURCE[0]}")/../skills" && pwd -P)"
dest_abs="$(realpath -m -- "$dest")"
case "$dest_abs" in "$src"|"$src"/*) echo 'Destination must not be inside the source skills tree' >&2; exit 1;; esac
probe="$dest_abs"
while [[ "$probe" != '/' ]]; do
  [[ ! -L "$probe" ]] || { echo "Target symlink rejected: $probe" >&2; exit 1; }
  probe="$(dirname "$probe")"
done
mkdir_plan=()
count=0
while IFS= read -r -d '' skill; do
  skill_dir="$(dirname "$skill")"
  name="$(basename "$skill_dir")"
  while IFS= read -r -d '' file; do
    [[ ! -L "$file" ]] || { echo "Symlink rejected: $file" >&2; exit 1; }
    relative="${file#"$skill_dir"/}"
    target="$dest/$name/$relative"
    if [[ -e "$target" ]]; then
      cmp -s -- "$file" "$target" || { echo "Existing local file differs: $target" >&2; exit 1; }
    else
      mkdir_plan+=("$file" "$target")
    fi
  done < <(find "$skill_dir" -type f -print0)
  count=$((count + 1))
done < <(find "$src" -name SKILL.md -type f -print0)
[[ $count -gt 0 ]] || { echo "No skills found" >&2; exit 1; }
if [[ "$dry_run" == '--dry-run' ]]; then
  echo "Would install $((${#mkdir_plan[@]} / 2)) files from $count skills into $dest"
  exit 0
fi
for ((i=0; i<${#mkdir_plan[@]}; i+=2)); do
  mkdir -p -- "$(dirname "${mkdir_plan[i+1]}")"
  cp -- "${mkdir_plan[i]}" "${mkdir_plan[i+1]}"
done
echo "Installed $((${#mkdir_plan[@]} / 2)) files from $count skills into $dest"
