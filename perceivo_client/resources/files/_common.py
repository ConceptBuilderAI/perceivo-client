"""Path constants shared by the ``files`` mixins."""

_FILES = "/v1/files"
#: The file name a replacement part carries. The API keeps the entry's own name
#: and reads only the bytes, so this is a label, not data.
_REPLACE_FILENAME = "content"
