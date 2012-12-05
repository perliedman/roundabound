roundabound
===========

It appears there is no simple and easy to understand solution for rotating
logs in Windows. **roundabound** attempts to fix this simple problem.

It will also work on UNIX, if you would want it for some reason.

Configuration is done in JSON:

```json
{
    "sets": {
        "logs": {
            "pattern": "C:\\logs\\*.log.????????",
            "archive_age": 7,
            "archive_path": "c:\\archive"
        },
        "logs2": {
            "pattern": "C:\\logs\\*.log????????",
            "archive_age": 14,
            "archive_path": "c:\\archive"
        }
    }
}
```

To run:

```
python -m Roundabound [configfile]
```

```configfile``` will default to ```roundabound.cfg``` if omitted.
