"""Fixed inputs shared by every row of the golden-vector table.

Nothing here is a credential. ``SECRET`` and ``_secret_transport.SECRET_HEX`` are
published test constants, documented as such in the table's ``secret_note``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# One secret for every positive vector, so an implementer has a single value to
# configure. Plain ASCII, so it survives copying into any language. It is a test
# constant and protects nothing.
SECRET = "perceivo-test-signing-secret-v1"


TIMESTAMP = 1767225600  # 2026-01-01T00:00:00Z, fixed so the vectors are stable.
NONCE = "sT8kQ2vX7wLpR4nB1mZ6yH0j"

# Field 3: the API key id as a lowercase 8-4-4-4-12 UUID. Not the key prefix,
# which every key in an organization shares.
KEY_ID = "0f8fad5b-d9cb-469f-a165-70867728950e"

# A second key id, used only by the negative vectors: a key the signature was not
# made with.
OTHER_KEY_ID = "3d1c1a7e-6b54-4b0e-9a2d-8c5f0e21b4aa"

# Field 9: two organization ids, in the lowercase hyphenated form field 9 requires.
# A signature made for ORGANIZATION_A must not verify for ORGANIZATION_B.
ORGANIZATION_A = "8c7e2b41-5d93-4a06-bf12-3e9d70a5c684"
ORGANIZATION_B = "1a4f6d20-9e3b-47c8-85af-b62d0c17e995"

# Body bytes shared by the two multipart vectors. Only the boundary parameter of
# their Content-Type differs.
MULTIPART_BODY = (
    b'------X\r\nContent-Disposition: form-data; name="role"\r\n\r\nviewer\r\n------X--\r\n'
)
