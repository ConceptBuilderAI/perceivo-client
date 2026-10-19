"""The ``--model-name-map`` that ``regen.py`` passes to the generator."""

from __future__ import annotations

# Inline schemas renamed so they do not take the names of component schemas such
# as ``Operation`` and ``Privilege``. Keys are the generator's reference paths
# (datamodel-code-generator 0.83.0).
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
    # Inline field types named after their owning schema and field rather than
    # the generator's numbered bare field names (``Name1``, ``Role1``). A suffix
    # that only repeats the schema's role (``Read``, ``Item``, ``V1``) is dropped.
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
    # The inline ``principal_type`` enums of ``GroupMemberAdd`` and ``GroupMemberRead``.
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
    # ``ComponentCreate``'s three ``anyOf`` branches, named after the field each
    # requires; each field type is named after ``ComponentCreate`` and its field,
    # with ``None`` marking the nullable alternative.
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
