#!/bin/bash
# Script executed when motion is detected
# Parameters: year month day hour minute second

YEAR=$1
MONTH=$2
DAY=$3
HOUR=$4
MINUTE=$5
SECOND=$6

TIMESTAMP="${YEAR}-${MONTH}-${DAY} ${HOUR}:${MINUTE}:${SECOND}"

# Log the event
echo "Motion detected at ${TIMESTAMP}" >> logs/events.log

# Create event flag file for event listener
echo "${TIMESTAMP}" > logs/motion_event.flag
