#!/bin/bash

if [ -z "$OPTIMADE_CONFIG_FILE" ]; then
    export OPTIMADE_CONFIG_FILE="./optimade_config.json"
    echo "Using the demo config file at ${OPTIMADE_CONFIG_FILE}."
    echo "Set the environment variable OPTIMADE_CONFIG_FILE to override this behaviour."
    echo "For more configuration options, please see https://www.optimade.org/optimade-python-tools/configuration/."
fi

export OPTIMADE_LOG_LEVEL=info
if [ "$1" == "debug" ]; then
    export OPTIMADE_DEBUG=1
    export OPTIMADE_LOG_LEVEL=debug
fi

if [ "$1" == "index" ]; then
    MAIN="main_index"
    PORT=5001
    if [ "$2" == "debug" ]; then
        export OPTIMADE_DEBUG=1
        export OPTIMADE_LOG_LEVEL=debug
    fi
else
    if [ "${MAIN}" == "main_index" ]; then
        PORT=5001
    else
        MAIN="main"
        PORT=5000
    fi
fi

uvicorn optimade.server.$MAIN:app --reload --port $PORT --log-level $OPTIMADE_LOG_LEVEL
