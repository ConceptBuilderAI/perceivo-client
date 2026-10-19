# GENERATED CODE - DO NOT EDIT BY HAND.
# Regenerate with: python openapi/regen.py (see CONTRIBUTING.md).
# Source: openapi-v1.json, version 1.0.0, sha256 2aa6c183fd1166f3608b84c4ee4e4b3e515b79932f1d17dae9baec570492c85d

from __future__ import annotations

from datetime import date
from enum import Enum, StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class ActivityCounts(BaseModel):
    """
    How many inputs are in each state.
    """

    cancelled: int | None = Field(None, title="Cancelled")
    completed: int | None = Field(None, title="Completed")
    failed: int | None = Field(None, title="Failed")
    queued: int | None = Field(None, title="Queued")
    running: int | None = Field(None, title="Running")


class ChannelType(StrEnum):
    """
    How the channel delivers. It cannot be changed after creation.
    """

    email = "email"
    sms = "sms"
    webhook = "webhook"
    slack = "slack"
    teams = "teams"
    pagerduty = "pagerduty"
    discord = "discord"
    telegram = "telegram"


class AlertChannelCreate(BaseModel):
    """
    A new notification channel. The owning organization comes from the caller.
    """

    channel_type: ChannelType = Field(
        ...,
        description="How the channel delivers. It cannot be changed after creation.",
        title="Channel Type",
    )
    config: dict[str, Any] = Field(
        ...,
        description="The channel's delivery settings. Which settings apply depends on `channel_type`.",
        title="Config",
    )
    is_enabled: bool | None = Field(
        True, description="Whether the channel delivers.", title="Is Enabled"
    )
    name: str = Field(
        ...,
        description="A name for the channel, shown wherever the channel is listed.",
        max_length=255,
        min_length=1,
        title="Name",
    )


class AlertChannelRead(BaseModel):
    """
    A notification channel belonging to the calling organization.
    """

    channel_type: str = Field(..., title="Channel Type")
    config: dict[str, Any] = Field(
        ...,
        description='Channel-specific delivery configuration. **Secret values are never returned.** Only the non-secret settings of this channel type and any `*_secret_id` references are returned as stored; every other setting that holds a value is withheld and reported only by a `*_set` presence flag, for example `"token_set": true`.',
        title="Config",
    )
    created_at: str = Field(..., title="Created At")
    id: str = Field(..., title="Id")
    is_enabled: bool = Field(..., title="Is Enabled")
    name: str = Field(..., title="Name")
    organization_id: str = Field(..., title="Organization Id")


class AlertChannelUpdateName(RootModel[str]):
    root: str = Field(
        ...,
        description="A name for the channel, shown wherever the channel is listed.",
        max_length=255,
        min_length=1,
        title="Name",
    )


class AlertChannelUpdate(BaseModel):
    """
    Fields of a notification channel that may be changed after creation.

    Every field is optional and only the fields you send are changed.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    config: dict[str, Any] | None = Field(
        None,
        description="The channel's delivery settings. **Replaced wholesale, not merged** — send every setting you want kept. Secret values are not returned on read, so every secret setting must be resent on each update, or referenced through its `*_secret_id`; a secret left out is removed from the channel. A `*_set` flag from a read reports presence only and is discarded if sent.",
        title="Config",
    )
    is_enabled: bool | None = Field(
        None, description="Whether the channel delivers.", title="Is Enabled"
    )
    name: AlertChannelUpdateName | None = Field(
        None,
        description="A name for the channel, shown wherever the channel is listed.",
        title="Name",
    )


class AlertRead(BaseModel):
    """
    An alert raised by the platform.
    """

    acknowledged_at: str | None = Field(None, title="Acknowledged At")
    acknowledged_by: str | None = Field(None, title="Acknowledged By")
    alert_type: str = Field(
        ...,
        description="Event domain, for example `training.job.failed`.",
        title="Alert Type",
    )
    auto_resolve_after_hours: int | None = Field(None, title="Auto Resolve After Hours")
    channels_sent: list[str] | None = Field(None, title="Channels Sent")
    created_at: str = Field(..., title="Created At")
    id: str = Field(..., title="Id")
    is_read: bool | None = Field(False, title="Is Read")
    message: str = Field(..., title="Message")
    metadata: dict[str, Any] | None = Field(None, title="Metadata")
    organization_id: str = Field(..., title="Organization Id")
    resolution_notes: str | None = Field(None, title="Resolution Notes")
    resolved_at: str | None = Field(None, title="Resolved At")
    resolved_by: str | None = Field(None, title="Resolved By")
    severity: str = Field(..., title="Severity")
    source_id: str | None = Field(None, title="Source Id")
    source_name: str | None = Field(None, title="Source Name")
    source_type: str = Field(..., title="Source Type")
    status: str = Field(
        ..., description="`active`, `acknowledged` or `resolved`.", title="Status"
    )
    title: str = Field(..., title="Title")


class ResolutionNotes(RootModel[str]):
    root: str = Field(
        ...,
        description="Why the condition is considered resolved.",
        max_length=2000,
        title="Resolution Notes",
    )


class AlertResolve(BaseModel):
    """
    Optional resolution details.
    """

    resolution_notes: ResolutionNotes | None = Field(
        None,
        description="Why the condition is considered resolved.",
        title="Resolution Notes",
    )


class AlertRuleConditionType(BaseModel):
    """
    One kind of condition an alert rule can fire on.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    condition_fields: list[str] | None = Field(
        None,
        description="The keys a rule's `condition` object takes for this kind.",
        title="Condition Fields",
    )
    condition_type: str = Field(
        ...,
        description="The value to send as a rule's `condition_type`.",
        title="Condition Type",
    )
    description: str = Field(..., title="Description")
    evaluated: bool = Field(
        ...,
        description="Whether the platform evaluates this kind of condition. Only evaluated kinds are listed; a rule of any other kind is refused.",
        title="Evaluated",
    )
    label: str = Field(..., title="Label")


class Description(RootModel[str]):
    root: str = Field(
        ...,
        description="What the rule is for, in your own words.",
        max_length=2000,
        title="Description",
    )


class Severity(StrEnum):
    """
    The severity of the alerts the rule raises.
    """

    warning = "warning"
    critical = "critical"


class TargetType(StrEnum):
    """
    Who receives the rule's alerts: `creator` (the default) is the rule's author, `user` is the people named in `target_user_subs`, and `organization` is every member of your organization who can read alerts. An `organization` rule needs a `cooldown_minutes` of at least 15.
    """

    creator = "creator"
    user = "user"
    organization = "organization"


class AlertRuleCreate(BaseModel):
    """
    A new alert rule. The owning organization is resolved from the caller.
    """

    condition: dict[str, Any] = Field(
        ...,
        description="The condition itself. Its keys depend on `condition_type`; the catalogue lists them for each kind.",
        title="Condition",
    )
    condition_type: Literal["event_pattern"] = Field(
        ...,
        description="The kind of condition the rule carries. `GET /v1/alert-rules/catalog` lists the kinds and whether each is evaluated.",
        title="Condition Type",
    )
    cooldown_minutes: int | None = Field(
        60,
        description="Minutes after the rule fires during which it does not fire again. The platform may hold some rules to a longer minimum.",
        ge=0,
        title="Cooldown Minutes",
    )
    description: Description | None = Field(
        None,
        description="What the rule is for, in your own words.",
        title="Description",
    )
    is_enabled: bool | None = Field(
        True,
        description="Whether the rule fires. A disabled rule is kept and can be enabled again.",
        title="Is Enabled",
    )
    message_template: str = Field(
        ...,
        description="The message of each alert the rule raises.",
        max_length=4000,
        min_length=1,
        title="Message Template",
    )
    name: str = Field(
        ...,
        description="A name for the rule, shown wherever the rule is listed.",
        max_length=255,
        min_length=1,
        title="Name",
    )
    notify_channels: list[str] | None = Field(
        None,
        description="The kinds of channel the rule delivers on, such as `in_app` or `email`. These are channel kinds from the catalogue, not channel identifiers.",
        title="Notify Channels",
    )
    severity: Severity | None = Field(
        "warning",
        description="The severity of the alerts the rule raises.",
        title="Severity",
    )
    target_type: TargetType | None = Field(
        "creator",
        description="Who receives the rule's alerts: `creator` (the default) is the rule's author, `user` is the people named in `target_user_subs`, and `organization` is every member of your organization who can read alerts. An `organization` rule needs a `cooldown_minutes` of at least 15.",
        title="Target Type",
    )
    target_user_subs: list[str] | None = Field(
        None,
        description="The people a `user` rule delivers to, by user identifier. Required and non-empty when `target_type` is `user`, and refused for any other target type. Each must be a member of your organization; a rule naming anyone else is refused with `404`.",
        title="Target User Subs",
    )
    title_template: str = Field(
        ...,
        description="The title of each alert the rule raises.",
        max_length=500,
        min_length=1,
        title="Title Template",
    )


class AlertRuleRead(BaseModel):
    """
    An alert rule belonging to the calling organization.
    """

    condition: dict[str, Any] = Field(..., title="Condition")
    condition_type: str = Field(..., title="Condition Type")
    cooldown_minutes: int = Field(..., title="Cooldown Minutes")
    created_at: str = Field(..., title="Created At")
    created_by_user_sub: str = Field(..., title="Created By User Sub")
    description: str | None = Field(None, title="Description")
    id: str = Field(..., title="Id")
    is_enabled: bool = Field(..., title="Is Enabled")
    last_triggered_at: str | None = Field(None, title="Last Triggered At")
    message_template: str = Field(..., title="Message Template")
    name: str = Field(..., title="Name")
    notify_channels: list[str] = Field(..., title="Notify Channels")
    organization_id: str = Field(..., title="Organization Id")
    severity: str = Field(..., title="Severity")
    target_role_id: str | None = Field(None, title="Target Role Id")
    target_type: str = Field(..., title="Target Type")
    target_user_subs: list[str] | None = Field(None, title="Target User Subs")
    title_template: str = Field(..., title="Title Template")
    updated_at: str = Field(..., title="Updated At")


class AlertRuleTest(BaseModel):
    """
    An optional synthetic event to evaluate a rule against.

    Send nothing to test the rule against a default event. Any field you do send
    replaces that field of the synthetic event.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    event_type: str | None = Field(
        None,
        description="The event type to evaluate the rule against.",
        title="Event Type",
    )
    message: str | None = Field(
        None, description="Body of the synthetic event.", title="Message"
    )
    source_name: str | None = Field(
        None,
        description="The source the synthetic event appears to come from.",
        title="Source Name",
    )


class AlertRuleTestResult(BaseModel):
    """
    The outcome of test-firing a rule.
    """

    model_config = ConfigDict(
        extra="allow",
    )
    detail: str = Field(
        ..., description="A human-readable account of the outcome.", title="Detail"
    )
    dispatched: bool = Field(
        ...,
        description="Whether a notification was actually sent as a result.",
        title="Dispatched",
    )
    event_type: str = Field(
        ...,
        description="The event type the rule was evaluated against.",
        title="Event Type",
    )
    matched: bool = Field(
        ...,
        description="Whether the rule's condition matched the event.",
        title="Matched",
    )
    notify_channels: list[str] | None = Field(
        None,
        description="The channels the rule would deliver to.",
        title="Notify Channels",
    )
    recipients: int = Field(
        ...,
        description="How many recipients the delivery resolved to.",
        title="Recipients",
    )
    rule_id: str = Field(..., title="Rule Id")


class ConditionTypeEnum(StrEnum):
    """
    The kind of condition the rule carries. `GET /v1/alert-rules/catalog` lists the kinds and whether each is evaluated.
    """

    event_pattern = "event_pattern"


class ConditionType(RootModel[ConditionTypeEnum | None]):
    root: ConditionTypeEnum | None = Field(
        None,
        description="The kind of condition the rule carries. `GET /v1/alert-rules/catalog` lists the kinds and whether each is evaluated.",
        title="Condition Type",
    )


class CooldownMinutes(RootModel[int]):
    root: int = Field(
        ...,
        description="Minutes after the rule fires during which it does not fire again. The platform may hold some rules to a longer minimum.",
        ge=0,
        title="Cooldown Minutes",
    )


class MessageTemplate(RootModel[str]):
    root: str = Field(
        ...,
        description="The message of each alert the rule raises.",
        max_length=4000,
        min_length=1,
        title="Message Template",
    )


class AlertRuleUpdateName(RootModel[str]):
    root: str = Field(
        ...,
        description="A name for the rule, shown wherever the rule is listed.",
        max_length=255,
        min_length=1,
        title="Name",
    )


class TitleTemplate(RootModel[str]):
    root: str = Field(
        ...,
        description="The title of each alert the rule raises.",
        max_length=500,
        min_length=1,
        title="Title Template",
    )
