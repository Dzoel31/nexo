from pydantic import BaseModel, Field, HttpUrl, field_validator


class Account(BaseModel):
    name: str
    email: str | None = None


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
    homepage: str | None = None

    @field_validator("homepage", mode="before")
    @classmethod
    def empty_str_to_none(cls, value):
        if not value or (isinstance(value, str) and not value.strip()):
            return None
        return str(value).strip()


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
    commits: list[Commit] = []
    head_commit: Commit | None = None


class Branch(BaseModel):
    label: str | None = None
    ref: str | None = None
    sha: str | None = None
    user: User | None = None
    repo: Repository | None = None


class PullRequest(BaseModel):
    html_url: HttpUrl
    issue_url: str | None = None

    @field_validator("issue_url", mode="before")
    @classmethod
    def empty_issue_url_to_none(cls, value):
        if not value or (isinstance(value, str) and not value.strip()):
            return None
        return str(value).strip()

    number: int
    state: str
    title: str
    user: User
    body: str | None = None
    created_at: str
    updated_at: str
    closed_at: str | None = None
    merged_at: str | None = None
    merge_commit_sha: str | None = None
    commits: int | None = 0
    additions: int | None = 0
    deletions: int | None = 0
    changed_files: int | None = 0
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
    name: str | None = None
    draft: bool
    prerelease: bool
    created_at: str
    updated_at: str
    published_at: str | None = None
    body: str | None = None


class ReleaseSchema(BaseModel):
    action: str
    release: Release
    repository: Repository
    sender: User


class HeadCommit(BaseModel):
    id: str
    message: str
    timestamp: str
    author: Account | None = None
    committer: Account | None = None


class WorkflowRun(BaseModel):
    id: int
    name: str
    head_branch: str | None = None
    head_sha: str | None = None
    path: str | None = None
    display_title: str | None = None
    run_number: int
    event: str
    status: str
    conclusion: str | None = None
    html_url: HttpUrl
    created_at: str
    updated_at: str
    triggering_actor: User | None = None
    head_commit: HeadCommit | None = None
    actor: User | None = None


class Workflow(BaseModel):
    id: int
    name: str
    state: str | None = None


class WorkflowSchema(BaseModel):
    action: str
    workflow_run: WorkflowRun
    workflow: Workflow | None = None
    repository: Repository
    sender: User
