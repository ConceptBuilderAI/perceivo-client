"""Train and evaluate; read, register, promote, retire and delete models; training jobs; model families.

One of the mixins that make up
:class:`~perceivo_client.resources.intelligence.IntelligenceResource`.
"""

from __future__ import annotations

from typing import Any

from perceivo_client._paths import segment
from perceivo_client.generated.models import (
    EvaluationRead,
    IntelligenceTrainingJobRead,
    ModelFamilyRead,
    ModelLifecycleResult,
    ModelPromotionResult,
    ModelRead,
    TrainingJobSubmitResponse,
)
from perceivo_client.resources.intelligence._common import _BASE, _MixinBase


class _ModelsMixin(_MixinBase):
    """The ``client.intelligence`` methods this module's docstring lists."""

    # -- training ----------------------------------------------------------
    def train(
        self, intelligence_id: str, body: dict[str, Any] | None = None
    ) -> TrainingJobSubmitResponse:
        """Start a training job (``POST .../train``).

        Training consumes compute. The job runs in the background: poll
        :meth:`get_training_job` with the returned ``id``.

        Args:
            intelligence_id: The intelligence to train.
            body: An optional ``TrainingRequest`` object. Omitted, an empty
                object is sent.

        Returns:
            :class:`TrainingJobSubmitResponse` — the accepted job (``202``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_TRAIN`` and a
                direct grant on the intelligence (``403``).
            PerceivoSubscriptionRequiredError: For an organization with no live
                subscription (``403`` ``subscription_required``); choose a plan
                or start a trial.
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            TrainingJobSubmitResponse,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/train", json=body or {}
            ),
        )

    # -- evaluation & models ----------------------------------------------
    def evaluate(self, intelligence_id: str, body: dict[str, Any] | None = None) -> EvaluationRead:
        """Evaluate the intelligence's models (``POST .../evaluate``).

        Evaluation consumes compute.

        Args:
            intelligence_id: The intelligence to evaluate.
            body: An optional ``EvaluateRequest`` object. Omitted, an empty
                object is sent.

        Returns:
            :class:`EvaluationRead` — the evaluation record.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            EvaluationRead,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/evaluate", json=body or {}
            ),
        )

    def list_models(self, intelligence_id: str) -> list[ModelRead]:
        """List the intelligence's models (``GET .../models``).

        Every model comes in one response; the list takes no filters.

        Args:
            intelligence_id: The intelligence whose models are listed.

        Returns:
            ``list[ModelRead]``.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_READ``
                (``403``).
            PerceivoNotFoundError: For an intelligence your organization
                cannot see (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            ModelRead,
            self._get(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/models"),
        )

    def get_model(self, intelligence_id: str, model_id: str) -> ModelRead:
        """Read one model (``GET .../models/{model_id}``).

        Args:
            intelligence_id: The intelligence that holds the model.
            model_id: The model to read.

        Returns:
            :class:`ModelRead`.

        Raises:
            ValueError: If ``intelligence_id`` or ``model_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoGrantError: For a key without ``INTELLIGENCE_READ``
                (``403``).
            PerceivoNotFoundError: For a model or intelligence your
                organization cannot see (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/models/{segment(model_id, 'model_id')}"
            ),
        )

    def promote_model(
        self, intelligence_id: str, model_id: str, body: dict[str, Any] | None = None
    ) -> ModelPromotionResult:
        """Promote a model, for example to canary or champion (``POST .../models/{model_id}/promote``).

        Promotion deploys serving capacity for the model.

        Args:
            intelligence_id: The intelligence that holds the model.
            model_id: The model to promote.
            body: An optional ``PromoteModelRequest`` (``target_stage``); omitted, ``{}`` is sent.

        Returns:
            :class:`ModelPromotionResult`.

        Raises:
            ValueError: If ``intelligence_id`` or ``model_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoGrantError: For a key without the model-management privilege (``403``).
            PerceivoSubscriptionRequiredError: For an organization with no live
                subscription (``403`` ``subscription_required``); choose a plan
                or start a trial.
            PerceivoNotFoundError: For a model or intelligence your
                organization cannot see (``404``).
            PerceivoConflictError: While a promotion freeze is active on the
                intelligence (``409``); nothing is changed.
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelPromotionResult,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/models/{segment(model_id, 'model_id')}/promote",
                json=body or {},
            ),
        )

    def retire_model(self, intelligence_id: str, model_id: str) -> ModelLifecycleResult:
        """Retire a model (``POST .../models/{model_id}/retire``).

        No body is sent.

        Args:
            intelligence_id: The intelligence that holds the model.
            model_id: The model to retire.

        Returns:
            :class:`ModelLifecycleResult`.

        Raises:
            ValueError: If ``intelligence_id`` or ``model_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoGrantError: Without a required privilege (``403``): ``INTELLIGENCE_READ``
                on the intelligence and ``INTELLIGENCE_MANAGE_MODELS``.
            PerceivoNotFoundError: For a model that does not exist or does not belong to
                the named intelligence; nothing is retired (``404``).
            PerceivoAPIError: On any other error response.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelLifecycleResult,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/models/{segment(model_id, 'model_id')}/retire"
            ),
        )

    # -- training jobs and model registration ------------------------------
    def get_training_job(self, intelligence_id: str, job_id: str) -> IntelligenceTrainingJobRead:
        """One training job and its runs (``GET .../training-jobs/{job_id}``).

        The ``id`` of the :class:`TrainingJobSubmitResponse` that :meth:`train`
        returns is the ``job_id`` here.

        Args:
            intelligence_id: The intelligence that ran the job.
            job_id: The training job to read.

        Returns:
            :class:`IntelligenceTrainingJobRead`.

        Raises:
            ValueError: If ``intelligence_id`` or ``job_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a job of another intelligence or one that does not
                exist, and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            IntelligenceTrainingJobRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/training-jobs/{segment(job_id, 'job_id')}"
            ),
        )

    def register_model(self, intelligence_id: str, body: dict[str, Any]) -> ModelRead:
        """Register a model on the intelligence (``POST .../models``).

        Args:
            intelligence_id: The intelligence to register the model on.
            body: A ``ModelRegisterRequest`` object, sent as the JSON body.

        Returns:
            :class:`ModelRead` — the registered model (``201``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelRead,
            self._post(f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/models", json=body),
        )

    def delete_model(self, intelligence_id: str, model_id: str) -> None:
        """Delete a model (``DELETE .../models/{model_id}``, ``204``).

        Args:
            intelligence_id: The intelligence that holds the model.
            model_id: The model to delete.

        Returns:
            ``None``.

        Raises:
            ValueError: If ``intelligence_id`` or ``model_id`` is empty, ``.``
                or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``404``
                (``PerceivoNotFoundError``) for a model that does not belong to this intelligence or
                does not exist; ``409`` (``PerceivoConflictError``) for a model still referenced by
                a traffic role, a deployment or an evaluation (the body names the constraint; there
                is no force); and ``422`` (``PerceivoValidationError``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/models/{segment(model_id, 'model_id')}"
        )

    # -- model families ----------------------------------------------------
    def list_model_families(
        self, intelligence_id: str, *, active_only: bool | None = None
    ) -> list[ModelFamilyRead]:
        """List model families (``GET .../model-families``).

        Args:
            intelligence_id: The intelligence whose families are listed.
            active_only: ``True`` lists only active families. Omitted, the
                parameter is not sent and the server default, ``false``,
                applies.

        Returns:
            ``list[ModelFamilyRead]``.

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._list(
            ModelFamilyRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/model-families",
                params={"active_only": active_only},
            ),
        )

    def create_model_family(self, intelligence_id: str, body: dict[str, Any]) -> ModelFamilyRead:
        """Create a model family (``POST .../model-families``).

        Args:
            intelligence_id: The intelligence to create the family on.
            body: A ``ModelFamilyCreateRequest`` object, sent as the JSON
                body.

        Returns:
            :class:`ModelFamilyRead` — the family as stored (``201``).

        Raises:
            ValueError: If ``intelligence_id`` is empty, ``.`` or ``..``
                (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a caller without ``INTELLIGENCE_MANAGE_MODELS``; ``404``
                (``PerceivoNotFoundError``) for an intelligence that does not exist or belongs to
                another organization; and ``422`` (``PerceivoValidationError``) for a malformed
                request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelFamilyRead,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/model-families", json=body
            ),
        )

    def get_model_family(self, intelligence_id: str, family_id: str) -> ModelFamilyRead:
        """One model family (``GET .../model-families/{family_id}``).

        Args:
            intelligence_id: The intelligence that holds the family.
            family_id: The family to read.

        Returns:
            :class:`ModelFamilyRead`.

        Raises:
            ValueError: If ``intelligence_id`` or ``family_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response, for example
                ``PerceivoValidationError`` (``422``) for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelFamilyRead,
            self._get(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/model-families/{segment(family_id, 'family_id')}"
            ),
        )

    def update_model_family(
        self, intelligence_id: str, family_id: str, body: dict[str, Any]
    ) -> ModelFamilyRead:
        """Update a model family (``PATCH .../model-families/{family_id}``).

        Args:
            intelligence_id: The intelligence that holds the family.
            family_id: The family to update.
            body: A ``ModelFamilyUpdateRequest`` object, sent as the JSON
                body. Fields it omits are left unchanged.

        Returns:
            :class:`ModelFamilyRead` — the family after the update.

        Raises:
            ValueError: If ``intelligence_id`` or ``family_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a caller without ``INTELLIGENCE_MANAGE_MODELS``, or
                without ``INTELLIGENCE_MANAGE_TRAFFIC`` when the body sets ``traffic_percent`` or
                ``is_active``; ``404`` (``PerceivoNotFoundError``) for an intelligence that does not
                exist or belongs to another organization; and ``422`` (``PerceivoValidationError``)
                for a malformed request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelFamilyRead,
            self._patch(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/model-families/{segment(family_id, 'family_id')}",
                json=body,
            ),
        )

    def activate_model_family(self, intelligence_id: str, family_id: str) -> ModelFamilyRead:
        """Activate a model family (``POST .../model-families/{family_id}/activate``).

        No body is sent.

        Args:
            intelligence_id: The intelligence that holds the family.
            family_id: The family to activate.

        Returns:
            :class:`ModelFamilyRead` — the family, now active.

        Raises:
            ValueError: If ``intelligence_id`` or ``family_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a caller without ``INTELLIGENCE_MANAGE_MODELS``; ``404``
                (``PerceivoNotFoundError``) for an intelligence that does not exist or belongs to
                another organization; and ``422`` (``PerceivoValidationError``) for a malformed
                request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._model(
            ModelFamilyRead,
            self._post(
                f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/model-families/{segment(family_id, 'family_id')}/activate"
            ),
        )

    def deactivate_model_family(self, intelligence_id: str, family_id: str) -> dict[str, Any]:
        """Deactivate a model family (``DELETE .../model-families/{family_id}``).

        The family is marked inactive and its traffic set to zero; nothing is
        destroyed. Needs ``INTELLIGENCE_MANAGE_MODELS`` and ``INTELLIGENCE_MANAGE_TRAFFIC``.

        Args:
            intelligence_id: The intelligence that holds the family.
            family_id: The family to deactivate.

        Returns:
            ``dict[str, Any]`` — ``{"message": ...}``: ``Model family
            deactivated``, or ``Family already inactive`` for a repeat.

        Raises:
            ValueError: If ``intelligence_id`` or ``family_id`` is empty,
                ``.`` or ``..`` (refused before the request is sent).
            PerceivoAPIError: On an error response. The route declares ``403``
                (``PerceivoGrantError``) for a caller missing ``INTELLIGENCE_MANAGE_MODELS`` or
                ``INTELLIGENCE_MANAGE_TRAFFIC`` (nothing is deactivated); ``404``
                (``PerceivoNotFoundError``) for an intelligence that does not exist or belongs to
                another organization; and ``422`` (``PerceivoValidationError``) for a malformed
                request.
            PerceivoConnectionError: If the API cannot be reached.
        """
        return self._delete(
            f"{_BASE}/{segment(intelligence_id, 'intelligence_id')}/model-families/{segment(family_id, 'family_id')}"
        )
