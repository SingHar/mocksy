# Moto in mocksy

Many mocksy services keep their state in [Moto](https://github.com/getmoto/moto)
(see `MotoFallbackDispatcher` in `localstack-core/localstack/services/providers.py`).
mocksy runs with either package:

| Package | What it is | Status |
|---|---|---|
| `moto-ext` (default) | LocalStack's build of Moto, with its own fixes | Published by LocalStack for its own product; mocksy has no control over it |
| `moto` | The upstream Moto project | Released by the Moto maintainers |

Both install the Python package `moto`, so only one can be installed at a time.

## Use upstream moto

In a development environment:

```sh
make install-dev-upstream-moto                 # latest moto
make install-dev-upstream-moto MOTO_VERSION="==5.2.4"
```

To make upstream moto the default for everyone, change one line in
`pyproject.toml`:

```toml
"moto-ext[all]>=5.1.22",   # replace with: "moto[all]>=5.2.4"
```

## Differences that mocksy handles

`localstack-core/localstack/utils/moto_compat.py` holds the names that differ
between the packages. Import them from there, not from Moto:

| Name | moto-ext | upstream moto |
|---|---|---|
| `RESTError` | `moto.core.exceptions.RESTError` | `moto.core.exceptions._RESTError` |

`is_moto_ext()` tells which package is installed. Use it to skip tests that
depend on moto-ext internals.

## Checks

The workflow `.github/workflows/mocksy-moto-compat.yml` runs the unit tests and
the tests of the Moto-backed services with the pinned moto-ext, the latest
moto-ext and the latest upstream moto:

- on pull requests that change services, dependencies or the workflow
- every Monday; a failed weekly run opens an issue

## When you change a Moto-backed service

- Run its tests with both packages before you merge.
- Put Moto fixes in the service's `provider.py` (with `localstack.utils.patch`)
  and say in the module docstring what they fix. The same gaps are usually in
  upstream Moto too; consider sending the fix to the Moto project.
