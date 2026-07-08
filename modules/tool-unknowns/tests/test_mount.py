"""Iron Law tests: mount() must register a tool and return metadata."""

from unittest.mock import AsyncMock, MagicMock

import pytest

# importorskip is not enough: a partial amplifier_core install can exist
# without ToolResult. Skip unless the real symbol imports.
try:
    from amplifier_core import ToolResult  # noqa: F401
except Exception:  # ImportError or namespace-package weirdness
    pytest.skip("amplifier-core peer dependency not usable", allow_module_level=True)

from amplifier_module_tool_unknowns import mount  # noqa: E402


@pytest.mark.asyncio
async def test_mount_registers_tool():
    coordinator = MagicMock()
    coordinator.mount = AsyncMock()

    result = await mount(coordinator)

    coordinator.mount.assert_called_once()
    assert coordinator.mount.call_args[0][0] == "tools"
    assert result is not None
    assert result["name"] == "tool-unknowns"
    assert "unknowns_map" in result["provides"]


@pytest.mark.asyncio
async def test_tool_has_required_properties():
    coordinator = MagicMock()
    coordinator.mount = AsyncMock()

    await mount(coordinator)

    tool = coordinator.mount.call_args[0][1]
    assert isinstance(tool.name, str) and tool.name == "unknowns_map"
    assert isinstance(tool.description, str) and tool.description
    assert isinstance(tool.input_schema, dict)
    assert callable(tool.execute)
