from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, field_validator


class Account(BaseModel):
    name: str
    email: Optional[str] = None


class Commit(BaseModel):
    id: str
    message: str
    url: HttpUrl
    author: Account
    committer: Account
    timestamp: str


class User(BaseModel):
    login: str
    id: int
    avatar_url: HttpUrl
    html_url: HttpUrl


class Repository(BaseModel):
    name: str
    full_name: str
    private: bool
    html_url: HttpUrl
    owner: User
    homepage: Optional[HttpUrl] = None


class DockerServiceSchema(BaseModel):
    id: str = Field(
        ..., description="Unique identifier for the Docker service", alias="ID"
    )
    name: str = Field(..., description="Name of the Docker service", alias="Name")
    state: str = Field(
        ..., description="Current state of the Docker service", alias="State"
    )
    createdAt: str = Field(
        ..., description="Creation timestamp of the Docker service", alias="CreatedAt"
    )
    status: str = Field(
        ..., description="Status message of the Docker service", alias="Status"
    )
    image: str = Field(
        ..., description="Docker image used by the service", alias="Image"
    )

    @field_validator("*", mode="before")
    def strip_whitespace(cls, value):
        return value.strip() if isinstance(value, str) else value

    def get_color(self) -> int:
        state_color_map = {
            "running": 3066993,
            "healthy": 3066993,
            "starting": 15105570,
            "unhealthy": 15158332,
            "stopped": 10070709,
            "exited": 10070709,
        }
        return state_color_map.get(self.state.lower(), 8421504)


class PushSchema(BaseModel):
    ref: str
    before: str
    after: str
    repository: Repository
    pusher: Account
    sender: User
    created: bool
    deleted: bool
    forced: bool
    compare: HttpUrl
    commits: List[Commit]
    head_commit: Commit


class Branch(BaseModel):
    label: str
    ref: str
    sha: str
    user: User
    repo: Repository


class PullRequest(BaseModel):
    html_url: HttpUrl
    issue_url: HttpUrl
    number: int
    state: str
    title: str
    user: User
    body: Optional[str] = None
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    merged_at: Optional[str] = None
    merge_commit_sha: Optional[str] = None
    commits: int
    additions: int
    deletions: int
    changed_files: int
    head: Branch
    base: Branch


class PullRequestSchema(BaseModel):
    action: str
    number: int
    pull_request: PullRequest
    repository: Repository
    sender: User


class Release(BaseModel):
    url: HttpUrl
    html_url: HttpUrl
    id: int
    author: User
    tag_name: str
    name: Optional[str] = None
    draft: bool
    prerelease: bool
    created_at: str
    updated_at: str
    published_at: Optional[str] = None
    body: Optional[str] = None


class ReleaseSchema(BaseModel):
    action: str
    release: Release
    repository: Repository
    sender: User


class HeadCommit(BaseModel):
    id: str
    message: str
    timestamp: str
    author: Account
    committer: Account


class WorkflowRun(BaseModel):
    id: int
    name: str
    head_branch: str
    head_sha: str
    path: str
    display_title: str
    run_number: int
    event: str
    status: str
    conclusion: Optional[str] = None
    html_url: HttpUrl
    created_at: str
    updated_at: str
    triggering_actor: User
    head_commit: HeadCommit
    actor: User


class Workflow(BaseModel):
    id: int
    name: str
    state: str


class WorkflowSchema(BaseModel):
    action: str
    workflow_run: WorkflowRun
    workflow: Workflow
    repository: Repository
    sender: User
