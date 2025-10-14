#!/bin/bash
# Script executed when a movie is completed
# Parameters: filename

FILENAME=$1

# Log the event
echo "Movie saved: ${FILENAME}" >> logs/events.log
