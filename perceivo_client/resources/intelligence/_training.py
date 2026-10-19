"""Training configurations and training groups.

One of the mixins that make up
:class:`~perceivo_client.resources.intelligence.IntelligenceResource`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    TrainingConfigurationRead,
    TrainingGroupDetail,
    TrainingGroupMemberRead,
    TrainingGroupRead,
)
from perceivo_client.resources.intelligence._common import _BASE, _MixinBase


class _TrainingMixin(_MixinBase):
    """The ``client.intelligence`` methods this module's docstring lists."""

    # -- training configurations -------------------------------------------
    def list_training_configurations(
        self, intelligence_id: str, *, family_id: str | None = None
    ) -> list[TrainingConfigurationRead]:
        """List training configurations (``GET .../training-configurations``).

        ``family_id`` narrows the list to one model family. The body is a bare
        array and the route takes no page parameters.

        Args:
            intelligence_id: The intelligence whose configurations are listed.
            family_id: Only configurations of this model family. Omitted,
                every family's are listed.

        Returns:
            ``list[TrainingConfigurationRead]`` — every configuration, in one
            response.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            TrainingConfigurationRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-configurations",
                params={"family_id": family_id},
            ),
        )

    def create_training_configuration(
        self, intelligence_id: str, body: dict[str, Any]
    ) -> TrainingConfigurationRead:
        """Create a training configuration (``POST .../training-configurations``).

        Args:
            intelligence_id: The intelligence to create the configuration on.
            body: A ``TrainingConfigurationCreate`` object, sent as the JSON
                body.

        Returns:
            :class:`TrainingConfigurationRead` — the configuration as stored
            (``201``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingConfigurationRead,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-configurations",
                json=body,
            ),
        )

    def get_training_configuration(
        self, intelligence_id: str, config_id: str
    ) -> TrainingConfigurationRead:
        """One training configuration (``GET .../training-configurations/{config_id}``).

        Args:
            intelligence_id: The intelligence that holds the configuration.
            config_id: The configuration to read.

        Returns:
            :class:`TrainingConfigurationRead`.

        Raises:
            ValueError: If ``intelligence_id`` or ``config_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingConfigurationRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-configurations/{segment(config_id, 'config_id')}"
            ),
        )

    def update_training_configuration(
        self, intelligence_id: str, config_id: str, body: dict[str, Any]
    ) -> TrainingConfigurationRead:
        """Update a training configuration (``PATCH .../training-configurations/{config_id}``).

        Only the fields sent are changed.

        Args:
            intelligence_id: The intelligence that holds the configuration.
            config_id: The configuration to update.
            body: A ``TrainingConfigurationUpdate`` object, sent as the JSON
                body.

        Returns:
            :class:`TrainingConfigurationRead` — the configuration after the
            update.

        Raises:
            ValueError: If ``intelligence_id`` or ``config_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingConfigurationRead,
            self._patch(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-configurations/{segment(config_id, 'config_id')}",
                json=body,
            ),
        )

    def delete_training_configuration(self, intelligence_id: str, config_id: str) -> dict[str, Any]:
        """Delete a training configuration (``DELETE .../training-configurations/{config_id}``).

        A configuration that is a member of a training group is removed from it.

        Args:
            intelligence_id: The intelligence that holds the configuration.
            config_id: The configuration to delete.

        Returns:
            ``dict[str, Any]`` — ``{"message": "Training configuration
            deleted"}``.

        Raises:
            ValueError: If ``intelligence_id`` or ``config_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-configurations/{segment(config_id, 'config_id')}"
        )

    # -- training groups ---------------------------------------------------
    def list_training_groups(
        self, intelligence_id: str, *, include_members: bool | None = None
    ) -> list[TrainingGroupRead]:
        """List training groups (``GET .../training-groups``).

        ``include_members`` asks for each group's members. The body is a bare
        array and the route takes no page parameters.

        Args:
            intelligence_id: The intelligence whose groups are listed.
            include_members: ``True`` includes each group's members.
                Omitted, the parameter is not sent and the server default,
                ``false``, applies.

        Returns:
            ``list[TrainingGroupRead]`` — every group, in one response.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            TrainingGroupRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups",
                params={"include_members": include_members},
            ),
        )

    def create_training_group(
        self, intelligence_id: str, body: dict[str, Any]
    ) -> TrainingGroupDetail:
        """Create a training group (``POST .../training-groups``).

        Args:
            intelligence_id: The intelligence to create the group on.
            body: A ``TrainingGroupCreate`` object, sent as the JSON body.

        Returns:
            :class:`TrainingGroupDetail` — the group as stored (``201``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingGroupDetail,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups", json=body
            ),
        )

    def get_training_group(self, intelligence_id: str, group_id: str) -> TrainingGroupDetail:
        """One training group and its members (``GET .../training-groups/{group_id}``).

        Args:
            intelligence_id: The intelligence that holds the group.
            group_id: The group to read.

        Returns:
            :class:`TrainingGroupDetail`.

        Raises:
            ValueError: If ``intelligence_id`` or ``group_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingGroupDetail,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups/{segment(group_id, 'group_id')}"
            ),
        )

    def update_training_group(
        self, intelligence_id: str, group_id: str, body: dict[str, Any]
    ) -> TrainingGroupDetail:
        """Update a training group (``PATCH .../training-groups/{group_id}``).

        Args:
            intelligence_id: The intelligence that holds the group.
            group_id: The group to update.
            body: A ``TrainingGroupUpdate`` object, sent as the JSON body.

        Returns:
            :class:`TrainingGroupDetail` — the group after the update.

        Raises:
            ValueError: If ``intelligence_id`` or ``group_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingGroupDetail,
            self._patch(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups/{segment(group_id, 'group_id')}",
                json=body,
            ),
        )

    def delete_training_group(self, intelligence_id: str, group_id: str) -> dict[str, Any]:
        """Delete a training group (``DELETE .../training-groups/{group_id}``).

        Args:
            intelligence_id: The intelligence that holds the group.
            group_id: The group to delete.

        Returns:
            ``dict[str, Any]`` — ``{"message": "Training group deleted"}``.

        Raises:
            ValueError: If ``intelligence_id`` or ``group_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups/{segment(group_id, 'group_id')}"
        )

    def replace_training_group_member(
        self, intelligence_id: str, group_id: str, member_id: str, body: dict[str, Any]
    ) -> TrainingGroupMemberRead:
        """Put a configuration in a group.

        Calls ``PUT .../training-groups/{group_id}/members/{member_id}``.
        Answers ``201`` for a new member and ``200`` for a replaced one; both
        carry a ``TrainingGroupMemberRead``.

        Args:
            intelligence_id: The intelligence that holds the group.
            group_id: The group to put the member in.
            member_id: The member to create or replace.
            body: A ``TrainingGroupMemberReplace`` object, sent as the JSON
                body. The model family is taken from the configuration it
                names and cannot be set.

        Returns:
            :class:`TrainingGroupMemberRead` — the member as stored.

        Raises:
            ValueError: If ``intelligence_id``, ``group_id`` or ``member_id``
                is empty, ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a group or configuration that does not exist under
                this intelligence, or belongs to another organization; ``409``
                (``PerceivoConflictError``) for a second membership for a model family the group
                already covers; and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingGroupMemberRead,
            self._put(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups/{segment(group_id, 'group_id')}/members/{segment(member_id, 'member_id')}",
                json=body,
            ),
        )

    def remove_training_group_member(
        self, intelligence_id: str, group_id: str, member_id: str
    ) -> dict[str, Any]:
        """Remove a member from a group.

        Calls ``DELETE .../training-groups/{group_id}/members/{member_id}``.

        Args:
            intelligence_id: The intelligence that holds the group.
            group_id: The group to remove the member from.
            member_id: The member to remove.

        Returns:
            ``dict[str, Any]`` — ``{"message": "Member removed from training
            group"}``.

        Raises:
            ValueError: If ``intelligence_id``, ``group_id`` or ``member_id``
                is empty, ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups/{segment(group_id, 'group_id')}/members/{segment(member_id, 'member_id')}"
        )

    def run_training_group(self, intelligence_id: str, group_id: str) -> dict[str, Any]:
        """Train every configuration in a group (``POST .../training-groups/{group_id}/run``).

        Submits one training job per member, as one batch. Training consumes
        compute. No body is sent. Not safe to retry blindly: a member that
        fails answers ``500`` after earlier members' jobs were already queued.

        Args:
            intelligence_id: The intelligence that holds the group.
            group_id: The group to run.

        Returns:
            ``dict[str, Any]`` — ``message``, ``job_ids``, ``run_count``,
            ``group_id`` and ``group_name``. A batch that could not be started
            still answers here, with a ``message`` beginning ``Training batch
            was not started:``; read it before assuming jobs exist.

        Raises:
            ValueError: If ``intelligence_id`` or ``group_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._post(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-groups/{segment(group_id, 'group_id')}/run"
        )
