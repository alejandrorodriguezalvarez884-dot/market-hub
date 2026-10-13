#!/usr/bin/env bash
# Clone any missing submodule and move each one to the tip of its tracked branch
# (from .gitmodules), on a real branch instead of a detached HEAD.
# Safe to re-run: a submodule with uncommitted changes, or on another branch, is left alone.
set -uo pipefail
cd "$(dirname "$0")/.."

# Only a submodule that is not there yet is cloned. One that is already checked out is never
# moved back to the commit this repo recorded: that pointer is usually older than its branch, and
# another session may be working in that folder.
git submodule status | awk '/^-/ { print $2 }' | while read -r path; do
  git submodule update --init --quiet -- "$path"
done

git config -f .gitmodules --get-regexp '\.path$' | while read -r _ path; do
  branch=$(git config -f .gitmodules --get "submodule.$path.branch" || echo main)
  if [ -n "$(git -C "$path" status --porcelain)" ]; then
    echo "sync: $path has uncommitted changes, left as is"
    continue
  fi
  if ! git -C "$path" fetch --quiet origin "$branch"; then
    echo "sync: $path could not fetch origin/$branch, left as is"
    continue
  fi
  current=$(git -C "$path" symbolic-ref --short -q HEAD || true)
  if [ -z "$current" ]; then
    git -C "$path" checkout --quiet "$branch"
    current=$branch
  fi
  if [ "$current" = "$branch" ]; then
    git -C "$path" merge --quiet --ff-only "origin/$branch" \
      || echo "sync: $path/$branch has diverged from origin, left as is"
  else
    echo "sync: $path is on branch $current, left as is"
  fi
  echo "sync: $path on $(git -C "$path" symbolic-ref --short -q HEAD || echo detached) at $(git -C "$path" rev-parse --short HEAD)"
done
