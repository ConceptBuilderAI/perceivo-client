"""Shared pieces of the capabilities namespace's mixins.

``_MixinBase`` is :class:`~perceivo_client.resources._base.BaseResource` to a type
checker and ``object`` at runtime, so each mixin sees the request helpers without
putting ``BaseResource`` into the method resolution order more than once.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

_BASE = "/v1/capabilities"

if TYPE_CHECKING:
    from perceivo_client.resources._base import BaseResource as _MixinBase
else:
    _MixinBase = object
