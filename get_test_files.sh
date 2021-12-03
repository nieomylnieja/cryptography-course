#!/bin/bash

set -e

wget http://corpus.canterbury.ac.nz/resources/cantrbry.tar.gz -O canterbury.tar.gz
wget http://corpus.canterbury.ac.nz/resources/large.tar.gz -O large.tar.gz
wget http://corpus.canterbury.ac.nz/resources/artificl.tar.gz -O artificial.tar.gz

for archive in "canterbury.tar.gz" "large.tar.gz" "artificial.tar.gz"; do
  target_dir="$(sed 's/\..*$//' <<<"$archive")"
  mkdir -p ./resources/test_files/"$target_dir"
  tar -xzf "$archive" -C ./resources/test_files/"$target_dir"
  rm "$archive"
done