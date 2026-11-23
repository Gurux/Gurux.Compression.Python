# Agent instructions — Python projects

## General coding rules

- Follow PEP 8, PEP 257 and the repository's established conventions. Use four spaces for indentation; do not use tabs for Python indentation.
- Use CRLF (`\r\n`) line endings in newly created or modified text files when required by this repository; preserve existing encoding and avoid unrelated line-ending changes.
- Preserve the user's uncommitted work, behavior, supported Python versions and existing public API. Limit changes to the requested module and its necessary tests.
- Use type hints for new or changed public APIs, where compatible with the supported Python versions. Avoid unnecessary runtime dependencies.
- Do not change release versions or publish packages without authorization.

## Python documentation requirements

All new and modified Python source code must have complete, meaningful English docstrings.

- Document modules, classes, exceptions, functions, methods, constructors (`__init__` where meaningful), properties and public constants.
- Document arguments, return values, yielded values, relevant exceptions, side effects, blocking behavior, thread safety, timeouts and cancellation when applicable.
- Use the existing repository docstring format consistently (Google, NumPy or reStructuredText); do not mix styles within a module.
- For overridden methods, reference inherited documentation where appropriate; do not copy misleading or stale descriptions.
- Explain actual behavior rather than repeating identifiers. Never add meaningless placeholder documentation.
- Keep type hints and documentation consistent. Update docstrings when behavior changes.
- Do not modify unrelated code solely to add documentation unless explicitly requested.
- Validate documentation with the repository's existing tooling (for example Sphinx or pydocstyle) when available.

## Mandatory Gurux copyright header

Every applicable new or modified Python source file must contain the following header, with Python `#` comments:

```python
# --------------------------------------------------------------------------
# Gurux Ltd
#
# Copyright (c) Gurux Ltd.
#
# This file is part of Gurux Device Framework.
#
# Commit: $Format:%H$
# Date:   $Format:%cI$
#
# This software is available under either of the following licenses:
#
# 1. GNU General Public License, version 2 only (GPL-2.0-only).
#    See the LICENSE file included with this distribution.
#
# 2. A commercial license granted by Gurux Ltd under a separate written
#    agreement. Use under this option requires a valid commercial license
#    and is governed by the terms of that agreement.
#
# If you have not obtained a commercial license from Gurux Ltd,
# use of this software is governed by GPL-2.0-only.
#
# Commercial licensing: https://www.gurux.fi/
#
# SPDX-License-Identifier: GPL-2.0-only OR LicenseRef-Gurux-Commercial
# --------------------------------------------------------------------------
```

- Check each changed source file. Insert a missing header; replace an outdated Gurux header without duplicating it.
- Preserve the exact license text, SPDX identifier and `$Format:%H$` / `$Format:%cI$` placeholders; do not fill them manually.
- Preserve shebang and Python encoding declarations in their required positions, before the header if necessary.
- Do not overwrite third-party copyright notices; report conflicts.
- Apply the corresponding comment syntax to other maintained source files where appropriate. Do not add comments to JSON, binary, vendored or generated files.
- Ensure `LICENSE` contains the GPL-2.0-only license text and `LICENSES/LicenseRef-Gurux-Commercial` exists. Create `LICENSES` if necessary. Never invent commercial license terms or overwrite existing license files without review.
- Confirm each changed applicable file has exactly one valid header and still parses.

## Class and file organization

- Use one top-level class per Python module (`.py`) where practical for this project, with a filename corresponding to the class name in `snake_case` (for example `GXDLMSReader` → `gxdlms_reader.py`). **Preserve existing import paths and public module names**; do not rename files solely for style if it breaks users.
- Keep public classes, exceptions and enums in separate modules when doing so is safe. Small private helper types may stay near their implementation.
- Preserve package structure and `__init__.py` exports. If moving a public class, keep an import-compatible re-export at its previous location and document the migration.
- Avoid circular imports and import-time side effects. Keep generated code unchanged unless explicitly requested.
- Do not reorganize unrelated files. Verify imports, package discovery, typing, documentation and tests after moving code.

## Localization and string resources

All user-visible text must use the project's existing localization infrastructure. Prefer `gettext` and `.po` / `.mo` catalogs when no other mechanism is already established.

- Never hardcode new user-facing labels, messages, dialog text, tooltips, errors, warnings or notifications in application code.
- Store complete sentences in translatable messages. Avoid concatenating translated fragments or constructing sentences from separately translated words.
- Use named placeholders (`{device}`, `{count}`) or the existing gettext-compatible formatting convention; translators must be able to reorder placeholders.
- Reuse existing message IDs and keys; preserve punctuation and context. Use locale-aware formatting for dates, numbers and times.
- Use plural-aware translation (`ngettext`) when needed. Do not assume English plural rules.
- Do not translate protocol constants, identifiers, API routes, JSON keys, file extensions or internal developer-only log templates unless required by existing conventions.
- Do not create a second localization framework. Update localization only in touched code unless broader migration is requested.

Example with `gettext`:

```python
from gettext import gettext as _

message = _("Connection to {device} established successfully.").format(
    device=device_name
)
```

Incorrect:

```python
message = "Connection to " + device_name + " established successfully."
message = _("Connection to ") + device_name + _(" established successfully.")
```

- Verify extraction, placeholder consistency, plural forms, fallback language and packaging of translation catalogs.

## Asynchronous I/O, lifecycle and cancellation

- Use `async def` / `await` and `asyncio` for asynchronous I/O where suitable and consistent with the existing API. Do not assume that declaring `async def` makes blocking I/O nonblocking.
- Never call blocking socket operations, `time.sleep()` or other long-running synchronous work directly in the event loop. Use async-compatible I/O or `asyncio.to_thread()` when appropriate.
- Use `asyncio.Task`, task groups where supported, and `asyncio.Event` / queues / locks with correct ownership and cancellation semantics.
- Support explicit timeouts and cancellation (`asyncio.CancelledError`) and clean up connections, buffers and tasks in `finally` blocks or async context managers.
- Do not swallow `CancelledError`; propagate it after cleanup unless there is a documented reason otherwise.
- Do not hold a `threading.Lock` while awaiting. Avoid waiting synchronously for asynchronous work on the event-loop thread.
- Preserve existing synchronous public APIs. When adding asynchronous variants, use clear names such as `read_data_async()` if the project follows that convention, and avoid calling `asyncio.run()` from an already running event loop.
- Keep transport libraries independent of GUI frameworks and optional adapters. Each media session must own independent receive buffers and lifecycle state. Preserve packet-fragment handling, EOP matching, count constraints, peek, partial data, timeout and reconnect isolation where applicable.
- Validate behavior against tests, not by mechanically translating C# `Task` or Java `CompletableFuture` implementations.

## Project guidance and boundaries

- Preserve existing Gurux package boundaries and public import paths. Keep common media contracts and shared receive buffering independent of Serial, Net, Terminal, SMS and UI frameworks; concrete media may depend on Common, not the reverse.
- Keep implementation-specific events and behavior in their own media modules unless the public contract explicitly requires otherwise.
- Reuse shared receive-buffer logic rather than cloning it into each transport.
- Preserve supported Python versions and operating systems. Do not introduce new minimum Python requirements without authorization.
- Preserve uncommitted changes and distinguish unit tests, integration tests and real-device testing in the report.

## Python project configuration and dependency maintenance

Review the relevant `pyproject.toml`, `setup.cfg`, `setup.py`, `requirements*.txt`, lockfiles, `MANIFEST.in`, `tox.ini`, `pytest.ini` and CI configuration when changing project structure, dependencies or packaging.

1. **Configuration:** Verify `requires-python`, supported classifiers, build backend, package discovery, entry points, resource inclusion, lint/type-check settings and platform compatibility.
2. **Dependencies:** Check runtime and optional dependency ranges, compatibility and known vulnerabilities when possible. Avoid unnecessary major upgrades or removing dependencies without verification.
3. **Internal packages:** Validate imports, distribution names and dependency directions; avoid circular dependencies. Prefer the repository's established workspace/development dependency approach.
4. **Packaging:** Check package name, metadata, README, license, included package data, wheels and source distributions. Preserve PyPI / Trusted Publishing workflows.
5. **Localization:** Ensure catalogs and resource files are included in distributions and usable after installation.
6. **Consistency:** Prefer existing tooling (`uv`, Poetry, pip, setuptools, Hatch, etc.); do not migrate build systems without approval.
7. **Validation:** Run applicable tests and build checks, such as `python -m compileall`, `python -m pytest`, `python -m build`, plus existing lint and type-check commands. Do not install or publish packages unnecessarily.

### Versioning and release management

- Do not automatically change `project.version`, `__version__`, dynamic version configuration, package names, release tags or publishing metadata.
- Preserve the existing release and GitHub Actions conventions; avoid conflicting version sources.
- Version changes require explicit user approval or a documented authorized release process.
- Do not create Git tags, upload to PyPI, publish releases or trigger release workflows without an explicit request.
- Dependency updates must not inadvertently change the library's own release version.
- If a version change appears necessary, explain why and request approval first.

## Python Naming Conventions and Backward-Compatible API Migration

The agent must review **all classes, methods, functions, properties, attributes, constants, enum names and members in the affected module** and migrate names toward Python naming conventions while retaining legacy public entry points wherever technically feasible.

### Naming rules

- Use `PascalCase` for classes and exceptions (for example `GXDLMSReader`).
- Use `snake_case` for functions, methods, modules, packages, parameters, instance attributes and properties (for example `read_data`, `connection_timeout`).
- Use `UPPER_SNAKE_CASE` for constants. Follow the existing project's public enum-member convention unless a deliberate migration is requested.
- Prefix non-public implementation details with a single underscore where appropriate; do not introduce double-underscore name mangling without a specific need.
- Preserve Python special method names (`__init__`, `__enter__`, `__aenter__`, etc.).
- Do not rename protocol identifiers, serialized fields, wire-format names, external database columns or other compatibility-critical strings simply for style.
- Follow PEP 8, but do not change public names without providing compatible aliases or wrappers.

### Backward compatibility and deprecation

- Introduce a new correctly named implementation. The **new name owns the logic**; the old name must delegate to it rather than duplicate code.
- Preserve legacy public methods and callable signatures, including positional/keyword arguments, defaults, sync/async nature, return values and exception behavior.
- Add a `DeprecationWarning` using `warnings.warn(..., DeprecationWarning, stacklevel=2)` in old callable wrappers and document the replacement in their docstrings.
- `DeprecationWarning` is normally filtered by default for library consumers; do not force warnings to become errors or use `FutureWarning` without a project-specific reason.
- Preserve legacy properties with delegating `@property` getters/setters/deleters where supported. Warn on access and assignment if the old property is deprecated. Keep mutable semantics and validation consistent.
- For renamed classes, provide a legacy alias or a compatibility subclass/wrapper as appropriate. **A simple alias cannot emit a warning on instantiation** and a subclass can change type identity and behavior; choose deliberately, test `isinstance`, serialization and imports, and report limitations.
- For renamed modules, retain a compatibility import module that re-exports public symbols where possible. Preserve `__all__` and existing import paths.
- For legacy public constants and enum members, aliases may preserve access but cannot reliably warn on every use; document and report this limitation rather than introducing fragile metaprogramming.
- Do not rename externally visible constructor keyword arguments without accepting the old keyword as a compatibility alias and detecting conflicting inputs.
- Do not rename `__dict__` fields or stored state blindly: consider pickle, dataclasses, `__slots__`, descriptors, ORM mappings, JSON, reflection and plugin loading.
- Never remove old names or introduce breaking changes unless explicitly authorized. If compatibility cannot be maintained safely, leave the old API intact and report the issue.
- New internal code and tests should call the recommended names. Keep dedicated tests for old names and warnings.
- Do not mark new names as deprecated. Deprecation is an API migration step, not automatic removal permission.

### Example: methods

```python
import warnings


class GXDLMSReader:
    """Reads data from a DLMS device."""

    def read_data(self) -> bytes:
        """Read data from the device."""
        return self._read_data_impl()

    def ReadData(self) -> bytes:
        """Deprecated: use :meth:`read_data` instead."""
        warnings.warn(
            "ReadData() is deprecated; use read_data() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.read_data()
```

### Example: properties

```python
import warnings


class GXConnection:
    def __init__(self) -> None:
        self._connection_timeout = 30

    @property
    def connection_timeout(self) -> int:
        """Return the connection timeout in seconds."""
        return self._connection_timeout

    @connection_timeout.setter
    def connection_timeout(self, value: int) -> None:
        """Set the connection timeout in seconds."""
        self._connection_timeout = value

    @property
    def ConnectionTimeout(self) -> int:
        """Deprecated: use :attr:`connection_timeout` instead."""
        warnings.warn(
            "ConnectionTimeout is deprecated; use connection_timeout.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.connection_timeout

    @ConnectionTimeout.setter
    def ConnectionTimeout(self, value: int) -> None:
        warnings.warn(
            "ConnectionTimeout is deprecated; use connection_timeout.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.connection_timeout = value
```

### Migration scope and verification

1. Inventory legacy names and define their PEP 8 replacements, including classes, methods, properties, module names, constants and enums.
2. Implement the recommended names and compatible delegating wrappers or aliases. Preserve public imports, signatures and observable behavior.
3. Update the affected module's internal calls to the new names without changing wire protocols or serialization formats.
4. Add tests for new APIs, legacy APIs, deprecation warnings, sync/async behavior, keyword arguments, properties and serialization where relevant.
5. Check package exports, documentation, examples, type hints and CI against the updated API.
6. Produce a migration table of `old name → new name`, identify compatibility limitations and do not remove legacy APIs without approval.

## Verification and reporting

Before completing any task:

1. Verify headers, docstrings, naming, localization and Python syntax in all new or changed files.
2. Verify dependency direction, packaging, public import compatibility and asynchronous cancellation behavior.
3. Run the project's relevant build, lint, type-check and test commands. Clearly distinguish executed checks from unverified assumptions.
4. Ensure deprecated wrappers call the new implementation, and verify old APIs still work.
5. Do not publish packages, create tags or change release versions as part of ordinary verification.
6. Report files changed, old/new API mappings, test results, remaining warnings and any unresolved compatibility risks.

These instructions apply to all future Python development in this repository, subject to applicable parent repository instructions.
