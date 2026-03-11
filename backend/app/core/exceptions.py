from __future__ import annotations

from typing import Any


class AppException(Exception):
    """Base exception for all application-level errors."""

    def __init__(self, message: str, details: Any = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details!r})"


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, identifier: Any = None) -> None:
        self.resource = resource
        self.identifier = identifier
        message = (
            f"{resource} not found"
            if identifier is None
            else f"{resource} with id '{identifier}' not found"
        )
        super().__init__(message, details={"resource": resource, "identifier": str(identifier) if identifier else None})


class PermissionError(AppException):
    """Raised when the current user lacks permission to perform an action."""

    def __init__(self, action: str = "perform this action", resource: str | None = None) -> None:
        self.action = action
        self.resource = resource
        message = (
            f"You do not have permission to {action}"
            if resource is None
            else f"You do not have permission to {action} on {resource}"
        )
        super().__init__(message, details={"action": action, "resource": resource})


class InvalidStateTransitionError(AppException):
    """Raised when an illegal state machine transition is attempted."""

    def __init__(self, current_state: str, target_state: str) -> None:
        self.current_state = current_state
        self.target_state = target_state
        message = (
            f"Cannot transition from '{current_state}' to '{target_state}'"
        )
        super().__init__(
            message,
            details={"current_state": current_state, "target_state": target_state},
        )


class VideoProcessingError(AppException):
    """Raised when video processing (FFmpeg, etc.) fails."""

    def __init__(self, message: str, job_id: str | None = None, details: Any = None) -> None:
        self.job_id = job_id
        super().__init__(message, details=details or {"job_id": job_id})


class PublishingError(AppException):
    """Raised when publishing to a social platform fails."""

    def __init__(
        self,
        message: str,
        platform: str | None = None,
        job_id: str | None = None,
        details: Any = None,
    ) -> None:
        self.platform = platform
        self.job_id = job_id
        super().__init__(
            message,
            details=details or {"platform": platform, "job_id": job_id},
        )
