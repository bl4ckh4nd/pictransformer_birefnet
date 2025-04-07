#!/bin/sh
# Exit immediately if a command exits with a non-zero status.
set -e

# Define the directory where your built static files are served from
NGINX_ROOT_DIR="/usr/share/nginx/html"

echo "Substituting environment variables in JS files..."

# Find all JavaScript files in the specified directory and its subdirectories
find "$NGINX_ROOT_DIR" -name '*.js' -print0 | while IFS= read -r -d $'\0' file; do
  echo "Processing $file ..."
  # Create a temporary file
  temp_file=$(mktemp)

  # Get list of environment variables starting with REACT_APP_
  vars_to_subst=$(env | grep '^REACT_APP_' | awk -F= '{print "${" $1 "}"}' | tr '\n' ' ')

  # Substitute variables in the file and write to the temporary file
  # Use 'cat' and pipe to handle potential issues with large files or special characters
  cat "$file" | envsubst "$vars_to_subst" > "$temp_file"

  # Replace the original file with the temporary file
  mv "$temp_file" "$file"
done

echo "Substitution complete."

# Execute the original command (nginx)
echo "Starting Nginx..."
exec "$@"