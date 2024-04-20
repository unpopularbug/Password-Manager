
if [ "$ENVIRONMENT" = "development" ]; then
    export DEBUG=True
else
    export DEBUG=False
fi

exec "$@"
