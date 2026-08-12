# CHANGELOG

<!-- version list -->

## v1.4.0 (2026-08-12)

### Features

- **deploy**: Configure VPS deployment paths and update gateway port to 8002
  ([`4b3c7ca`](https://github.com/ksm-aiot-upnvj/nexo/commit/4b3c7ca3e0e16ff6827f3e11345c2b0d55ede8e5))


## v1.3.0 (2026-08-12)

### Features

- **deploy**: Configure docker-compose to pull ksmaiotupnvj/nexo-bot:latest and expose port 8000
  ([`ddf61fb`](https://github.com/ksm-aiot-upnvj/nexo/commit/ddf61fb90476816c59790e62a7f52fc0251d21a6))


## v1.2.0 (2026-08-12)

### Features

- **gateway**: Implement team-centric notification routing and global release broadcast
  ([`18d139d`](https://github.com/ksm-aiot-upnvj/nexo/commit/18d139d5568998c5ea2e24dabb981216c8de8705))


## v1.1.4 (2026-08-12)

### Bug Fixes

- **templates**: Remove @everyone fallback when discord_role_id is null
  ([`3d65f51`](https://github.com/ksm-aiot-upnvj/nexo/commit/3d65f5191672284284a6ee4912f4f783ea0da79b))


## v1.1.3 (2026-08-11)

### Bug Fixes

- **ci**: Update tag regex in docker-prune workflow to support semver tags without v prefix
  ([`3300ddd`](https://github.com/ksm-aiot-upnvj/nexo/commit/3300ddd6bcc75cbf0f9cfcc3b310e1e883c73658))


## v1.1.2 (2026-08-11)

### Bug Fixes

- **ci**: Update docker hub secret name to DOCKER_RELEASE
  ([`558b3ce`](https://github.com/ksm-aiot-upnvj/nexo/commit/558b3ceebda75c1d610c55db13f90d8b53ccf838))


## v1.1.1 (2026-08-11)

### Bug Fixes

- **ci**: Allow docker build and push workflow for all release tag formats
  ([`6f47d7e`](https://github.com/ksm-aiot-upnvj/nexo/commit/6f47d7ec41957d20a315a10651174e741bfcd1bd))


## v1.0.0 (2026-08-11)

- Initial Release

## v1.1.0 (2026-08-11)

### Bug Fixes

- **ci**: Set semantic-release changelog template_dir to avoid conflict with bot templates
  ([`8fc98ae`](https://github.com/ksm-aiot-upnvj/nexo/commit/8fc98ae7289f87fad4a01a127172c27e6dd68608))

### Features

- Enhance voice channel commands, context reset, onboarding UI, and rate limit docs
  ([`b9d4097`](https://github.com/ksm-aiot-upnvj/nexo/commit/b9d4097f1f76cc623bbadf76554ce21bc118741a))

- Integrate FastAPI webhook gateway, dynamic CD notifications, and auto-deploy engine
  ([`c622c16`](https://github.com/ksm-aiot-upnvj/nexo/commit/c622c16cec7906c31a86cdaac5ae7cbbf74f5f2d))


## v1.0.1 (2026-08-04)

### Bug Fixes

- Migrate mcp client to SSE transport
  ([`12296e1`](https://github.com/ksm-aiot-upnvj/nexo/commit/12296e1fc93a0b9709bb38b5a6653e82b17e9934))


## v1.0.0 (2026-08-03)

- Initial Release
