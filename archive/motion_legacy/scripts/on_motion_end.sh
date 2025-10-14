#!/bin/bash
# Script executed when motion ends
# Parameters: year month day hour minute second

YEAR=$1
MONTH=$2
DAY=$3
HOUR=$4
MINUTE=$5
SECOND=$6

TIMESTAMP="${YEAR}-${MONTH}-${DAY} ${HOUR}:${MINUTE}:${SECOND}"

# Log the event
echo "Motion ended at ${TIMESTAMP}" >> logs/events.log
