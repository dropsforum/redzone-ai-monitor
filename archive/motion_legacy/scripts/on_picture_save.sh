#!/bin/bash
# Script executed when a picture is saved
# Parameters: filename

FILENAME=$1

# Log the event
echo "Picture saved: ${FILENAME}" >> logs/events.log
