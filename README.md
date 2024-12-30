# Gitspatch

<p align="center">
    <em>Connect any webhook to GitHub Actions</em>
</p>

[![build](https://github.com/gitspatch/gitspatch/workflows/Build/badge.svg)](https://github.com/gitspatch/gitspatch/actions)
[![codecov](https://codecov.io/gh/gitspatch/gitspatch/branch/master/graph/badge.svg)](https://codecov.io/gh/gitspatch/gitspatch)

---

**Documentation**: <a href="https://gitspatch.github.io/gitspatch/" target="_blank">https://gitspatch.github.io/gitspatch/</a>

**Source Code**: <a href="https://github.com/gitspatch/gitspatch" target="_blank">https://github.com/gitspatch/gitspatch</a>

---

## Development

### Setup environment

We use [Hatch](https://hatch.pypa.io/latest/install/) to manage the development environment and production build. Ensure it's installed on your system.

### Run unit tests

You can run all the tests with:

```bash
hatch run test
```

### Format the code

Execute the following command to apply linting and check typing:

```bash
hatch run lint
```

### Publish a new version

You can bump the version, create a commit and associated tag with one command:

```bash
hatch version patch
```

```bash
hatch version minor
```

```bash
hatch version major
```

Your default Git text editor will open so you can add information about the release.

When you push the tag on GitHub, the workflow will automatically publish it on PyPi and a GitHub release will be created as draft.

## Serve the documentation

You can serve the Mkdocs documentation with:

```bash
hatch run docs-serve
```

It'll automatically watch for changes in your code.

## License

This project is licensed under the terms of the [Elastic License 2.0 (ELv2)](./LICENSE.md).
