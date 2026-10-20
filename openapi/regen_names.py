"""The ``--model-name-map`` that ``regen.py`` passes to the generator.

Loaded by ``regen.py`` by path, like ``regen_parts.py``. Standard library only:
it is data, and the comments say why each entry exists.
"""

from __future__ import annotations

# Inline schemas the generator would otherwise name first, ahead of the component
# schema whose name they take. It names classes in document order and inline
# enums after their title or field, so the grants schemas
# (CascadeApply, ChangeSet, ...) -- which sort before ``Operation`` and
# ``GroupMemberPrivileges`` -- took ``Operation`` from the operation-record model
# that ``client.operations`` returns and ``Privilege`` from the group privilege
# enum, renumbering both as ``Operation4`` and ``Privilege3``. Renaming the
# inline schemas leaves every component its own name. The keys are the
# generator's reference paths (fragment form, datamodel-code-generator 0.83.0);
# a key that stops matching restores the collision, which
# tests/test_generated_model_names.py fails on.
_ENUM = "#-datamodel-code-generator-#-enum-#-special-#"
_ARRAY = "#-datamodel-code-generator-#-array-#-special-#"
_ANY_OF_ARRAY = f"#-datamodel-code-generator-#-anyOf-#-special-#/0{_ARRAY}"
_ANY_OF = "#-datamodel-code-generator-#-anyOf-#-special-#"
_OBJECT = "#-datamodel-code-generator-#-object-#-special-#"
_COMPONENT_CREATE_BRANCH = f"#/components/schemas/ComponentCreate{_ANY_OF}"
_MODEL_NAME_MAP = {
    f"#/components/schemas/CascadeApply/operation{_ENUM}": "CascadeApplyOperation",
    f"#/components/schemas/CascadeApplyResult/operation{_ENUM}": "CascadeApplyResultOperation",
    f"#/components/schemas/CascadeOperation/operation{_ENUM}": "CascadeOperationOperation",
    f"#/components/schemas/ChangeSet/operation{_ENUM}": "ChangeSetOperation",
    f"#/components/schemas/CascadeApply/privilege{_ANY_OF_ARRAY}": "CascadeApplyPrivilege",
    f"#/components/schemas/CascadeApply/privileges{_ANY_OF_ARRAY}{_ARRAY}/0{_ARRAY}": (
        "CascadeApplyPrivilegesItem"
    ),
    f"#/components/schemas/CascadeOperation/privilege{_ANY_OF_ARRAY}": "CascadeOperationPrivilege",
    # Inline field types the generator would otherwise name after the bare field
    # and then number in document order (``Name``, ``Name1`` ... ``Name11``,
    # ``Role1``). Those names are public through
    # ``perceivo_client.models``, say nothing about what they constrain, and
    # change meaning whenever the document reorders. Each is named after the
    # schema that owns the field instead: the owner's name followed by the
    # field's. Most owners keep their full name. Six drop a suffix that only
    # repeats the schema's role: ``Read`` (``GrantGranteeType``,
    # ``InvitationRole``, ``InvitationStatus``, ``MemberRole``,
    # ``MemberRoleChangeRole``), ``Item`` (``FileUploadStatus``) and ``V1``
    # (``RoleUpdateName``).
    # ``GrantCreateGranteeType`` keeps ``Create`` because ``GrantGranteeType``
    # already names the ``GrantRead`` field.
    f"#/components/schemas/AlertChannelUpdate/name{_ANY_OF_ARRAY}": "AlertChannelUpdateName",
    f"#/components/schemas/AlertRuleUpdate/name{_ANY_OF_ARRAY}": "AlertRuleUpdateName",
    f"#/components/schemas/CapabilityCopyRequest/new_name{_ANY_OF_ARRAY}": (
        "CapabilityCopyRequestNewName"
    ),
    f"#/components/schemas/CascadeOperation/privileges{_ANY_OF_ARRAY}": (
        "CascadeOperationPrivileges"
    ),
    f"#/components/schemas/CascadeOperation/privileges{_ANY_OF_ARRAY}{_ARRAY}/0{_ARRAY}": (
        "CascadeOperationPrivilegesItem"
    ),
    f"#/components/schemas/ComponentDefinitionValidate/manifest_yaml{_ANY_OF_ARRAY}": (
        "ComponentDefinitionValidateManifestYaml"
    ),
    f"#/components/schemas/CreateGraphConfigRequest/description{_ANY_OF_ARRAY}": (
        "CreateGraphConfigRequestDescription"
    ),
    f"#/components/schemas/ExperimentUpdate/name{_ANY_OF_ARRAY}": "ExperimentUpdateName",
    f"#/components/schemas/FileEntryUpdate/name{_ANY_OF_ARRAY}": "FileEntryUpdateName",
    f"#/components/schemas/FileUploadItem/status{_ENUM}": "FileUploadStatus",
    f"#/components/schemas/GrantCreate/grantee_type{_ENUM}": "GrantCreateGranteeType",
    f"#/components/schemas/GrantRead/grantee_type{_ENUM}": "GrantGranteeType",
    f"#/components/schemas/GrantUpdate/direct_privileges{_ANY_OF_ARRAY}": (
        "GrantUpdateDirectPrivileges"
    ),
    # ``GroupMemberAdd`` and ``GroupMemberRead`` each declare an inline
    # ``principal_type`` enum, which the generator would name ``PrincipalType``
    # and ``PrincipalType1`` in document order. ``GroupMemberPrincipalType``
    # drops ``Read``, as ``GrantGranteeType`` does.
    f"#/components/schemas/GroupMemberAdd/principal_type{_ANY_OF}/0{_ENUM}": (
        "GroupMemberAddPrincipalType"
    ),
    f"#/components/schemas/GroupMemberRead/principal_type{_ANY_OF}/0{_ENUM}": (
        "GroupMemberPrincipalType"
    ),
    f"#/components/schemas/GroupUpdate/name{_ANY_OF_ARRAY}": "GroupUpdateName",
    f"#/components/schemas/InvitationRead/role{_ENUM}": "InvitationRole",
    f"#/components/schemas/InvitationRead/status{_ENUM}": "InvitationStatus",
    f"#/components/schemas/MemberInvite/role{_ENUM}": "MemberInviteRole",
    f"#/components/schemas/MemberRead/role{_ENUM}": "MemberRole",
    f"#/components/schemas/MemberRoleChangeRead/role{_ENUM}": "MemberRoleChangeRole",
    f"#/components/schemas/MemberRoleUpdate/role{_ENUM}": "MemberRoleUpdateRole",
    f"#/components/schemas/NodepoolWrite/name{_ANY_OF_ARRAY}": "NodepoolWriteName",
    f"#/components/schemas/OrganizationUpdate/name{_ANY_OF_ARRAY}": "OrganizationUpdateName",
    f"#/components/schemas/RoleUpdateV1/name{_ANY_OF_ARRAY}": "RoleUpdateName",
    f"#/components/schemas/StorageSpaceUpdate/name{_ANY_OF_ARRAY}": "StorageSpaceUpdateName",
    f"#/components/schemas/ThreadCreate/title{_ANY_OF_ARRAY}": "ThreadCreateTitle",
    f"#/components/schemas/ThreadUpdate/title{_ANY_OF_ARRAY}": "ThreadUpdateTitle",
    f"#/components/schemas/TrainingConfigurationUpdate/name{_ANY_OF_ARRAY}": (
        "TrainingConfigurationUpdateName"
    ),
    f"#/components/schemas/TrainingGroupUpdate/name{_ANY_OF_ARRAY}": "TrainingGroupUpdateName",
    # ``ComponentCreate`` is an ``anyOf`` of three branches, each requiring one of
    # ``type``, ``component_type`` or ``category``. The generator would name the
    # branches ``ComponentCreate1`` .. ``ComponentCreate3`` and their field types
    # ``Type``/``Type1``, ``ComponentType``/``ComponentType1`` and
    # ``Category``/``Category1`` -- the last taking ``Category`` from the
    # ``TicketCreate`` category enum, which it renumbered ``Category2``. Each
    # branch is named after the field it requires, and each field type after
    # ``ComponentCreate`` and its field; the ``None`` suffix marks the type built
    # from the field's nullable alternative.
    **{
        f"{_COMPONENT_CREATE_BRANCH}/{index}{_OBJECT}": branch
        for index, branch in enumerate(
            (
                "ComponentCreateWithType",
                "ComponentCreateWithComponentType",
                "ComponentCreateWithCategory",
            )
        )
    },
    f"{_COMPONENT_CREATE_BRANCH}/0{_OBJECT}/type{_ANY_OF}/0{_ARRAY}": "ComponentCreateType",
    f"{_COMPONENT_CREATE_BRANCH}/0{_OBJECT}/type{_ANY_OF}/1{_ARRAY}": "ComponentCreateTypeNone",
    f"{_COMPONENT_CREATE_BRANCH}/1{_OBJECT}/component_type{_ANY_OF}/0{_ARRAY}": (
        "ComponentCreateComponentType"
    ),
    f"{_COMPONENT_CREATE_BRANCH}/1{_OBJECT}/component_type{_ANY_OF}/1{_ARRAY}": (
        "ComponentCreateComponentTypeNone"
    ),
    f"{_COMPONENT_CREATE_BRANCH}/2{_OBJECT}/category{_ANY_OF}/0{_ENUM}": "ComponentCreateCategory",
    f"{_COMPONENT_CREATE_BRANCH}/2{_OBJECT}/category{_ANY_OF}/1{_ENUM}": (
        "ComponentCreateCategoryNone"
    ),
}
