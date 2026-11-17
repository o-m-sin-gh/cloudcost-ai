import logging as _logging


def setup_logging(level: int = _logging.INFO) -> None:
    _logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # Never log credentials; keep botocore quiet.
    _logging.getLogger("botocore").setLevel(_logging.WARNING)
    _logging.getLogger("boto3").setLevel(_logging.WARNING)
