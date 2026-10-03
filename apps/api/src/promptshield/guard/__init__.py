"""Guard package — import submodules directly to avoid circular imports."""

__all__ = ["guard_tool_call", "guard_output"]


def __getattr__(name: str):
    if name == "guard_tool_call":
        from promptshield.guard.tool_firewall import guard_tool_call

        return guard_tool_call
    if name == "guard_output":
        from promptshield.guard.egress import guard_output

        return guard_output
    raise AttributeError(name)
