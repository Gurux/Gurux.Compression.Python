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
"""Legacy listener contract retained for existing direct module imports."""

import abc
from typing import Any

ABC = abc.ABCMeta("ABC", (object,), {"__slots__": ()})
"""Abstract base shared by the legacy listener contract."""


# pylint: disable=too-few-public-methods
class IGXCompressionListener(ABC):
    """Describe the historical two-argument compression trace callback.

    Concrete subclasses implement on_trace. Current codecs instead accept
    a single-event callable assigned to on_trace; they do not use this contract.
    """

    __metaclass__ = abc.ABCMeta
    """Compression component will notify events through this interface."""

    @abc.abstractmethod
    def on_trace(self, sender: Any, e: Any) -> None:
        """Handle a trace notification synchronously in the caller's thread.

        Args:
            sender: Component emitting the notification.
            e: Event arguments supplied by that component.

        Returns:
            None. The abstract base implementation performs no work.

        Subclasses define handling, exceptions and synchronization. The base
        provides no timeout, cancellation mechanism or thread-safety guarantee.
        """
