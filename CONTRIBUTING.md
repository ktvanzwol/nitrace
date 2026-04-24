# Contributing to nitrace

Contributions to [nitrace](https://github.com/ktvanzwol/nitrace) are welcome from all!

nitrace is managed via [Git](https://git-scm.com), with the canonical upstream repository hosted on [GitHub](https://github.com/ktvanzwol/nitrace).

nitrace follows a pull request model for development. If you wish to contribute, you will need to create a GitHub account, fork this project, push a branch with your changes to your project, and then submit a pull request.

See [GitHub's official documentation](https://help.github.com/articles/using-pull-requests/) for more details.

# Getting Started

## Prerequisites

- Windows
- [Python 3.10+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) (recommended package manager)
- [NI IO Trace](https://www.ni.com/docs/en-US/bundle/ni-io-trace/page/overview.html) installed (required for system tests)

## Environment Setup

Clone the repository and install dependencies using [uv](https://docs.astral.sh/uv/):

```
git clone https://github.com/ktvanzwol/nitrace.git
cd nitrace
uv sync
```

This will create a virtual environment and install all development dependencies.

## Code Formatting

nitrace uses [ruff](https://docs.astral.sh/ruff/) for formatting. To format the entire project, run:

```
uv run ruff format
```

## Linting

nitrace uses [ruff](https://docs.astral.sh/ruff/) for linting. To lint the entire project, run:

```
uv run ruff check
```

To automatically fix lint issues where possible:

```
uv run ruff check --fix
```

## Testing

nitrace uses [pytest](https://docs.pytest.org/) to run tests. To run the unit tests:

```
uv run pytest
```

To run tests with coverage:

```
uv run pytest --cov
```

### System Tests

Some tests require NI IO Trace to be installed on the machine. These are marked with the `system` marker and are skipped by default. To include system tests, pass the `--system` flag:

```
uv run pytest --system
```

## Building

To build the project:

```
uv build
```

If the build succeeds, artifacts will be placed in `dist/`.

# Developer Certificate of Origin (DCO)

   Developer's Certificate of Origin 1.1

   By making a contribution to this project, I certify that:

   (a) The contribution was created in whole or in part by me and I
       have the right to submit it under the open source license
       indicated in the file; or

   (b) The contribution is based upon previous work that, to the best
       of my knowledge, is covered under an appropriate open source
       license and I have the right under that license to submit that
       work with modifications, whether created in whole or in part
       by me, under the same open source license (unless I am
       permitted to submit under a different license), as indicated
       in the file; or

   (c) The contribution was provided directly to me by some other
       person who certified (a), (b) or (c) and I have not modified
       it.

   (d) I understand and agree that this project and the contribution
       are public and that a record of the contribution (including all
       personal information I submit with it, including my sign-off) is
       maintained indefinitely and may be redistributed consistent with
       this project or the open source license(s) involved.

(taken from [developercertificate.org](https://developercertificate.org/))

See [LICENSE](https://github.com/ktvanzwol/nitrace/blob/main/LICENSE) for details about how nitrace is licensed.
