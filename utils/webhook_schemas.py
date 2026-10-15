"""Legacy compatibility facade. Do not add new logic here."""

from schemas.github.webhooks import (
    Account,
    Branch,
    Commit,
    DockerServiceSchema,
    HeadCommit,
    PullRequest,
    PullRequestSchema,
    PushSchema,
    Release,
    ReleaseSchema,
    Repository,
    User,
    Workflow,
    WorkflowRun,
    WorkflowSchema,
)

__all__ = [
    "Account",
    "Branch",
    "Commit",
    "DockerServiceSchema",
    "HeadCommit",
    "PullRequest",
    "PullRequestSchema",
    "PushSchema",
    "Release",
    "ReleaseSchema",
    "Repository",
    "User",
    "Workflow",
    "WorkflowRun",
    "WorkflowSchema",
]
