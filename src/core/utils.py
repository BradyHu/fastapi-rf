import datetime
import inspect


def format_datetime_into_isoformat(date_time: datetime.datetime) -> str:
    return date_time.replace(tzinfo=datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def return_type(func: callable):
    return inspect.signature(func).return_annotation
