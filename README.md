# Gitspatch

<p align="center">
    <em>Connect any webhook to GitHub Actions</em>
</p>

Plug webhooks into powerful workflows backed by GitHub Actions — zero infrastructure needed.

<p align="center">
<a href="https://www.gitspatch.dev/app/webhooks/create"><img src="https://md-buttons.francoisvoron.com/button.svg?text=Start%20automating&bg=4f46e5&w=200&h=40&py=10&px=10&fs=18" alt="Start automating" /></a>
</p>

---

**Documentation**: <a href="https://docs.gitspatch.dev" target="_blank">https://docs.gitspatch.dev</a>

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
