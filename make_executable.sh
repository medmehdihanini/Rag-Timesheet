#!/bin/bash
# Add execute permissions to shell scripts and Python scripts in the scripts directory

# Make shell scripts executable
chmod +x *.sh

# Make Python scripts in the scripts directory executable
find scripts/ -name "*.py" -exec chmod +x {} \;

echo "Execute permissions added to scripts!"
