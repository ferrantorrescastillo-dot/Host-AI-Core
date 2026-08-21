from __future__ import annotations

from .contracts import AuthorizedExecutionContext, OperationClass, ToolDefinition


class PlatformPolicy:
    def authorize(
        self, definition: ToolDefinition, context: AuthorizedExecutionContext,
    ) -> tuple[bool, str]:
        valid, reason = context.validate()
        if not valid:
            return False, reason
        missing = definition.required_scopes - context.scopes
        if missing:
            return False, "missing_required_scope"
        if definition.operation_class == OperationClass.CONFIRM and not definition.required_scopes:
            return False, "confirm_scope_required"
        return True, ""
