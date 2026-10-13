"""Convenience resource namespaces for the Perceivo public API."""

from __future__ import annotations

from perceivo_client.resources.alert_channels import AlertChannelsResource
from perceivo_client.resources.alert_rules import AlertRulesResource
from perceivo_client.resources.alerts import AlertsResource
from perceivo_client.resources.assets import AssetsResource
from perceivo_client.resources.auth import AuthResource
from perceivo_client.resources.billing import BillingResource
from perceivo_client.resources.capabilities import CapabilitiesResource
from perceivo_client.resources.components import ComponentsResource
from perceivo_client.resources.experiments import ExperimentsResource
from perceivo_client.resources.files import FilesResource
from perceivo_client.resources.grants import GrantsResource
from perceivo_client.resources.groups import GroupsResource
from perceivo_client.resources.infrastructure import InfrastructureResource
from perceivo_client.resources.intelligence import IntelligenceResource
from perceivo_client.resources.invitations import InvitationsResource
from perceivo_client.resources.members import MembersResource
from perceivo_client.resources.operations import OperationsResource
from perceivo_client.resources.orchestrations import OrchestrationsResource
from perceivo_client.resources.organization import OrganizationResource
from perceivo_client.resources.query import QueryResource
from perceivo_client.resources.queue import QueueResource
from perceivo_client.resources.reviews import ReviewsResource
from perceivo_client.resources.roles import RolesResource
from perceivo_client.resources.runs import RunsResource
from perceivo_client.resources.secrets import SecretsResource
from perceivo_client.resources.service_accounts import ServiceAccountsResource
from perceivo_client.resources.support import SupportResource
from perceivo_client.resources.threads import ThreadsResource
from perceivo_client.resources.triggers import TriggersResource
from perceivo_client.resources.webhooks import WebhooksResource

__all__ = [
    "AlertChannelsResource",
    "AlertRulesResource",
    "AlertsResource",
    "AssetsResource",
    "AuthResource",
    "BillingResource",
    "CapabilitiesResource",
    "ComponentsResource",
    "ExperimentsResource",
    "FilesResource",
    "GrantsResource",
    "GroupsResource",
    "InfrastructureResource",
    "IntelligenceResource",
    "InvitationsResource",
    "MembersResource",
    "OperationsResource",
    "OrchestrationsResource",
    "OrganizationResource",
    "QueryResource",
    "QueueResource",
    "ReviewsResource",
    "RolesResource",
    "RunsResource",
    "SecretsResource",
    "ServiceAccountsResource",
    "SupportResource",
    "ThreadsResource",
    "TriggersResource",
    "WebhooksResource",
]
