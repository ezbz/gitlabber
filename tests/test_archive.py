from gitlabber.archive import ArchivedResults


def test_archive_string() -> None:
    assert str(ArchivedResults.EXCLUDE) == "exclude"


def test_archive_repr() -> None:
    assert repr(ArchivedResults.ONLY) == "only"


def test_archive_enum_lookup() -> None:
    assert ArchivedResults["INCLUDE"] is ArchivedResults.INCLUDE
    assert ArchivedResults["EXCLUDE"] is ArchivedResults.EXCLUDE
    assert ArchivedResults["ONLY"] is ArchivedResults.ONLY


def test_archive_api_values() -> None:
    assert ArchivedResults.INCLUDE.api_value is None
    assert ArchivedResults.EXCLUDE.api_value is False
    assert ArchivedResults.ONLY.api_value is True


def test_archive_int_values() -> None:
    assert ArchivedResults.INCLUDE.int_value == 1
    assert ArchivedResults.EXCLUDE.int_value == 2
    assert ArchivedResults.ONLY.int_value == 3
