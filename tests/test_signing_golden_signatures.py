"""Every canonical request and signature in the golden-vector table, pinned as literals.

The table, its generator and the signer can change together and stay consistent
with one another while the wire format changes underneath all three. These pins
cannot: any change to a canonical request or a signature in the shipped table,
or to the signer that reproduces them, fails here. Descriptive text in the table
is not pinned.

Each pin is ``(sha256 hex of the canonical request, signature)``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

import pytest

from perceivo_client.signing import (
    build_canonical_request,
    compute_signature,
    load_golden_vectors,
    split_target,
)

PINNED_POSITIVE: dict[str, tuple[str, str]] = {
    "v01-get-empty-body-empty-query": (
        "6cdcc5f5228e002c5e286e567b9370d6da385f2ff87a23a20aacc4b4b4a17377",
        "v1=ee71c0810679e5b5477186d4d1ca0444d7823b8be284a0a9bc4a07bd9e1ebdd8",
    ),
    "v02-post-json-body": (
        "29e38ed94eca336ab5d0e399edb8b52ab84cba9b98e7104dbda84b94dbc12a53",
        "v1=66d1c00a8243a671026f09cb5ad8f2b528fa2d21c7166ae19459cafe8e43b9a0",
    ),
    "v03-query-order-is-preserved": (
        "6e1a432c5bed0d7fdf9d2b5c01cf236602111f837951dbd63009096db876ae5a",
        "v1=3c1734d1e379f702820e7c0c18cfb7efaadb9b7e941d0e62da19230d5b2892bf",
    ),
    "v04-valueless-key": (
        "5e5cb921cb6c1640d3907688dac44a14fe76d66b455e501f6fe7e206b6f26aef",
        "v1=f7b99a09524058eb8dcfc721f0988122b42f67b928e94c5d7bd312437cd82390",
    ),
    "v05-empty-value": (
        "6df6cfe90256db019d24f21734f7deebfe8565294adf8bfdacb3021cd8055afc",
        "v1=15c03b2354a826291c2b4f766aa55dee0e151a4cbb472c4aa4a3e5f21771f675",
    ),
    "v06-repeated-key": (
        "fffed2a27f9700568a40096379c32bd0a88c2b1f9d6513b37173fa1e7eb9c43e",
        "v1=e42558f7891064ef2fa35ab3f61124047574d8db5ce780883ff7645cf7178928",
    ),
    "v07-percent-2f-in-path": (
        "ee09148b6762c657e881edfbc13dbff1ca00a615252aaf3da1ddeb2ded062da4",
        "v1=aa475e3a77175462496a24e63321b44988bd5a580e6d7ee9e1184b290540e129",
    ),
    "v08-percent-encoding-case-preserved": (
        "927f0acc8f71492f4460b57ed5fb8ded9d1d0eed038937a1361e3d0f7871dd4c",
        "v1=10aa9d8278851a701bea2ad7e3608701705b33bcbda139ba47eeae6a461ecc0e",
    ),
    "v09-plus-in-query-value": (
        "64e0771fce83aa9d629e9e4246369546c54f35ef31fb6668e2b6979e406a9514",
        "v1=97d705e3eef1b2f8adcbaec1b49cc7d36c67c61234c9909317af1c826be7a8b3",
    ),
    "v10-double-slash-path": (
        "676de5388a5e918992587d938c37f639c5cc64953dd3ad73a995b68d1b0c362b",
        "v1=2eefe148e44932df1e25aca66e09994084e1b7570421df1b713c0c4e702867f1",
    ),
    "v11-non-ascii-path": (
        "9e56f7813114bd4bde2860c6777d9d5feb8cff78a3da4d52906a06c9c7ecb7b7",
        "v1=2207d703cfca9d75e2a43cf0b760c8f2977424ace6b8bf7a5b92b0dc8122adf3",
    ),
    "v12-non-utf8-body": (
        "4df57554e178a8ef8e946c8b8cc6af5f2d5d171acc743b345f8d7d21a9cd6388",
        "v1=d945123667886418162dcd2786c2eecdbbf1fcb6157642fbcf3f92d06afb10af",
    ),
    "v13-trailing-slash-significant": (
        "f04df8c4de39e668d826bc3823265464f762e567f3071f6395351c7be482596e",
        "v1=acc9f79ed9ce3159bb5884579d5686f53affb3da5b68104a757be93f2cdadd58",
    ),
    "v14-delete-with-query": (
        "02d58cf7801549ed34e0949610ae9ed58ae7a3480398aabfe5d91984cc0ca004",
        "v1=f82b00983308a401189fa1a4d296ef3b8e7626adca021e80d3957b76f532f38b",
    ),
    "v15-empty-query-element": (
        "4490704f35c383754fa2235768c3e409ee1e45372d5983f328ba5bfa0cc30fd9",
        "v1=72d5cb321ca991de8740d3c334f2d0f45cfc97416e93be24b2cfaec00a3c852c",
    ),
    "v16-value-containing-equals": (
        "297999c4882008cddd5485f35f06250e5592c964b85d376606d18fbe33683a57",
        "v1=9362663e94cbcad1f0b2b3e3804dcef9d06aa8f54a85d03a6b5bd761e5b33b01",
    ),
    "v17-utf8-body": (
        "57e53774737b82c768443bd1b7aff44871e35d6fb4ff43f7e98699fd498954b7",
        "v1=6d1ca77942d4a86727ebc2559cad3b6d81db3a75bfb8cbd2818896153eddab36",
    ),
    "v18-explicitly-empty-body": (
        "334fec080e6bd810f2e84721fc7ff55d1ca3c92362e2112cf2d573fd2bca58ea",
        "v1=9b250b3b30d7ff7a4c22b6ccdb3a2e5dc1334cbc3a20aa797bb70cad4daffd73",
    ),
    "v19-permutation-pair-a": (
        "112f7b65c21c7e2756643f952e3e47a70a12b49f72aca4aab150ab1115db2548",
        "v1=c298778030b3764bc9e3b62a9c4854d6a51629c0cd318e1614934a42220d4028",
    ),
    "v20-permutation-pair-b": (
        "9c036cc9f6df615051723799b9b423722ef8749468138d01fc1ee219c87946e8",
        "v1=2ca93fef85fbeb87977ca75fa323f28f3949670d10e787932b8ff3e46540d2cf",
    ),
    "v21-bare-key-order-preserved": (
        "afe7df9f26e9f5365c1f874c96fb27c905cae721c12e4f26698b2cdeecfc5da3",
        "v1=dd65238a832cbe364d4dacaf679232466f03a09a78f5f5e4123a46e8aca2dee7",
    ),
    "v22-unreserved-escape-lowercase-hex": (
        "e887dc9cadaa553f6c26ba082c542d1dfe46e1191a8331338d473cf43bdd2592",
        "v1=d13a6aef2b65287ec4280f2b333a1e2b75110e635f87d94507a6dd4b3cac427e",
    ),
    "v23-unreserved-escape-uppercase-hex": (
        "e887dc9cadaa553f6c26ba082c542d1dfe46e1191a8331338d473cf43bdd2592",
        "v1=d13a6aef2b65287ec4280f2b333a1e2b75110e635f87d94507a6dd4b3cac427e",
    ),
    "v24-literal-unreserved-character": (
        "e887dc9cadaa553f6c26ba082c542d1dfe46e1191a8331338d473cf43bdd2592",
        "v1=d13a6aef2b65287ec4280f2b333a1e2b75110e635f87d94507a6dd4b3cac427e",
    ),
    "v25-dot-segment-removed": (
        "e1bb4aef6faa1776c4508ac9437a9bcae6afea2165a15a36f8455e3220b4b45d",
        "v1=101c53ace603bda8afad404245abc035201dd3e2fe7fbcae524c90b758f1791d",
    ),
    "v26-single-dot-segment-removed": (
        "e1bb4aef6faa1776c4508ac9437a9bcae6afea2165a15a36f8455e3220b4b45d",
        "v1=101c53ace603bda8afad404245abc035201dd3e2fe7fbcae524c90b758f1791d",
    ),
    "v27-encoded-dot-segment-decode-then-remove": (
        "e1bb4aef6faa1776c4508ac9437a9bcae6afea2165a15a36f8455e3220b4b45d",
        "v1=101c53ace603bda8afad404245abc035201dd3e2fe7fbcae524c90b758f1791d",
    ),
    "v28-key-id-mixed-case-normalised": (
        "6cdcc5f5228e002c5e286e567b9370d6da385f2ff87a23a20aacc4b4b4a17377",
        "v1=ee71c0810679e5b5477186d4d1ca0444d7823b8be284a0a9bc4a07bd9e1ebdd8",
    ),
    "v29-absent-content-type-with-a-body": (
        "29a7e4c0248608d7041c2b72a7f7d3786b0e2ff6208413e78c6a26179fcb5666",
        "v1=78807ced50656f40c375c25cb63648f769d5658c666631c7c20cd783447f589b",
    ),
    "v30-multipart-boundary-pair-a": (
        "0b57df7fc0158ebca6221f4863e92c3e68f945fda3532ac8d76e15929f62adf2",
        "v1=8add09b39f2158cf06bc8bb61a7ebc5c2b5a7a54d7d21e6c96c1f5c6736250c6",
    ),
    "v31-multipart-boundary-pair-b": (
        "82af236c03309d4e61271b90e330b25240fdf49ee5e3bd1c5e1f4ec6902fa810",
        "v1=e0d9ba56ae878b3c90ef15c6a40e91d59bf3054209446b50a7dcc34b49e953cd",
    ),
    "v32-charset-pair-a": (
        "efca365ba5ce880e70ab3dbbc87678a70178fdb94443822a5230f2dcbf23edd2",
        "v1=d962730d07db3b37eb41cabc606edc644294e1cdc3cfced1336e5e6ff223d90d",
    ),
    "v33-charset-pair-b": (
        "40f7e7e611386e7912d930f27215da1764914169f48524ebbc4067c2df37be6b",
        "v1=870aa845bb232f75a9544b7818e15009539aee6a2e07b2c90e563427348ae08a",
    ),
    "v34-organization-present": (
        "22a7837846776159b0c8a1fb2bd689eb2a826100f28816783e78307cdadfb106",
        "v1=169b50b644cf5649874f5ffec076fcca495bd501ff3d7e1bb2d74f0323e3fd28",
    ),
    "v35-organization-pair-a": (
        "99cd2eb07cb911abf7663440d19ebba179f694fd83d8ed20f11436241250bcd2",
        "v1=73b01d23acd990e52afdc4aecb2f0695c70bece9ff947059af78b9e5270c6052",
    ),
    "v36-organization-pair-b": (
        "3c573c1c30354cb0bd9ea017c5ceefe82443633058a5800fd7f5f4816e51e2ac",
        "v1=5027f8fa2dc5e55a90b42ceb7c75b64dd584c8bc4f2ced38f77ecd985230e355",
    ),
}

PINNED_NEGATIVE: dict[str, tuple[str, str]] = {
    "n01-six-field-downgrade": (
        "b4e3577631cecea96772fdf99e5d414415c8483ea93b316908c2b33bc0839776",
        "v1=8ed8f544f28a9f3c0be30fa76af11c2ccff4967a4c1f70e2afe2100adf889e7d",
    ),
    "n02-nine-field-downgrade": (
        "64f812c3a234a5088ba99df4821c625665004746df4183295e66557feef89484",
        "v1=27a69dc02ea210832831b29cfe0b39f367e3cf268f277074948f6c812117db21",
    ),
    "n03-wrong-domain-separator": (
        "7d98b7a990baddcbe726dad0c3e032da6619a3e8954e5f0e99d8622d50624ee7",
        "v1=53645de57765145e3debfae86ff0e2239c9c66ba10bfbce3ab9a7127a394939b",
    ),
    "n04-audience-mismatch": (
        "0bc86f47b4878b840e6af626c563fa465c694c31d70ca4409becce9cbc7ab25b",
        "v1=bca717be03aecad20bd3982be514eb51a91a44b3486fab6514ad60b83f8a298e",
    ),
    "n05-key-id-mismatch": (
        "da9be99e25574ad1d429d51636ba8d70dc1ab395732b4d2f27361aa367c1ad5a",
        "v1=1eb722e689e806c1335bf2371bbb736205f6c4edfac3a2d326079594980d997f",
    ),
    "n06-ten-field-downgrade": (
        "1436acfa78499dcadc57d9f076a508bd09bf7f82d11f0e7f6c91b4cb27e3a137",
        "v1=2eba2062672cd7c5bfeff593614a50d2eee10ed835bdfc3ac8a5f4928d4eaa9e",
    ),
    "n07-organization-metadata-unbound": (
        "3c573c1c30354cb0bd9ea017c5ceefe82443633058a5800fd7f5f4816e51e2ac",
        "v1=5027f8fa2dc5e55a90b42ceb7c75b64dd584c8bc4f2ced38f77ecd985230e355",
    ),
}

PINNED_SECRET_TRANSPORT: dict[str, tuple[str, str]] = {
    "t01-hex-disclosure-decoded": (
        "6cdcc5f5228e002c5e286e567b9370d6da385f2ff87a23a20aacc4b4b4a17377",
        "v1=85818b89a0e9dc3fc15c9d20a72593970eb35441a19b4bc4bd5115d1488f53a5",
    ),
    "t02-hex-disclosure-utf8-encoded-WRONG": (
        "6cdcc5f5228e002c5e286e567b9370d6da385f2ff87a23a20aacc4b4b4a17377",
        "v1=80eec7a955b2f0c0a72b4c18f03e624c20618d83a568d3509425d612ab0a911a",
    ),
    "t03-hex-disclosure-uppercase-decoded": (
        "6cdcc5f5228e002c5e286e567b9370d6da385f2ff87a23a20aacc4b4b4a17377",
        "v1=85818b89a0e9dc3fc15c9d20a72593970eb35441a19b4bc4bd5115d1488f53a5",
    ),
    "t04-non-hex-secret-utf8-encoded": (
        "6cdcc5f5228e002c5e286e567b9370d6da385f2ff87a23a20aacc4b4b4a17377",
        "v1=ee71c0810679e5b5477186d4d1ca0444d7823b8be284a0a9bc4a07bd9e1ebdd8",
    ),
    "t05-sixty-four-chars-not-hex": (
        "6cdcc5f5228e002c5e286e567b9370d6da385f2ff87a23a20aacc4b4b4a17377",
        "v1=df438c2557f0056f1833074efbc0f04b525d35f0b148bf971bc505098b6cf464",
    ),
}

PINNED_LISTS = [
    pytest.param("vectors", PINNED_POSITIVE, id="positive"),
    pytest.param("negative_vectors", PINNED_NEGATIVE, id="negative"),
    pytest.param("secret_transport_vectors", PINNED_SECRET_TRANSPORT, id="secret-transport"),
]


@pytest.fixture(scope="module")
def table() -> dict:
    return load_golden_vectors()


def _rows(table: dict, name: str) -> dict[str, dict]:
    return {row["id"]: row for row in table[name]}


def _hmac(key: bytes, canonical_request: str) -> str:
    """HMAC-SHA256 with the standard library only, independent of the signer."""
    digest = hmac.new(key, canonical_request.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"v1={digest}"


@pytest.mark.parametrize(("name", "pinned"), PINNED_LISTS)
def test_the_table_carries_exactly_the_pinned_rows(table, name, pinned):
    assert set(_rows(table, name)) == set(pinned)


@pytest.mark.parametrize(("name", "pinned"), PINNED_LISTS)
def test_every_canonical_request_and_signature_matches_its_pin(table, name, pinned):
    rows = _rows(table, name)
    changed = [
        row_id
        for row_id, (canonical_sha256, signature) in pinned.items()
        if hashlib.sha256(rows[row_id]["canonical_request"].encode("utf-8")).hexdigest()
        != canonical_sha256
        or rows[row_id]["signature"] != signature
    ]
    assert changed == []


def test_the_signer_reproduces_every_pinned_positive_vector_from_its_inputs(table):
    secret = table["secret_utf8"]
    mismatched = []
    for row in table["vectors"]:
        canonical_sha256, signature = PINNED_POSITIVE[row["id"]]
        raw_path, query = split_target(row["target"])
        body = None if row["body_base64"] is None else base64.b64decode(row["body_base64"])
        canonical = build_canonical_request(
            audience=row["audience"],
            key_id=row["key_id_input"],
            method=row["method"],
            raw_path=raw_path,
            query_string=query,
            body=body,
            content_type=row["content_type"],
            organization=row["organization"],
            timestamp=row["timestamp"],
            nonce=row["nonce"],
        )
        reproduced = (
            hashlib.sha256(canonical.encode("utf-8")).hexdigest() == canonical_sha256
            and compute_signature(canonical, secret) == signature
            and _hmac(secret.encode("utf-8"), canonical) == signature
        )
        if not reproduced:
            mismatched.append(row["id"])
    assert mismatched == []


def test_every_pinned_negative_signature_is_a_correct_mac(table):
    key = table["secret_utf8"].encode("utf-8")
    mismatched = [
        row["id"]
        for row in table["negative_vectors"]
        if _hmac(key, row["canonical_request"]) != PINNED_NEGATIVE[row["id"]][1]
    ]
    assert mismatched == []


def test_every_pinned_secret_transport_signature_is_reproduced(table):
    mismatched = []
    for row in table["secret_transport_vectors"]:
        signature = PINNED_SECRET_TRANSPORT[row["id"]][1]
        key = bytes.fromhex(row["hmac_key_hex"])
        reproduced = _hmac(key, row["canonical_request"]) == signature
        if row["must_verify"]:
            reproduced = reproduced and (
                compute_signature(row["canonical_request"], row["secret_input"]) == signature
            )
        if not reproduced:
            mismatched.append(row["id"])
    assert mismatched == []
