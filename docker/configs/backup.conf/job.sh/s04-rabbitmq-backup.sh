#!/bin/bash

current_date=$(date +"%Y%m%d-%H%M%S")

source_dir="/backup/in/rabbitmq"

target_dir="/backup/out/rabbitmq"
backup_file="${target_dir}/${current_date}-rabbitmq.cpio.gz"
mkdir -p "$target_dir"

find "$source_dir" -print | cpio -o -H newc | gzip > "$backup_file"
find "$target_dir" -name "*.cpio.gz" -type f -mtime +2 -exec rm {} \;
