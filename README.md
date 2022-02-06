# dvci

**dvci** is a Python utility to easily deploy multiple versions of your
[Docums](http://khanhduy1407.github.io/docums)-powered docs to a Git branch, suitable for
deploying to Github via `gh-pages`.

## Installation

Like most Python projects, dvci uses [setuptools][setuptools], so installation
is what you might expect:

```sh
pip install dvci
```

Once you've installed dvci, you might also want to set up shell-completion for
it. If you have [shtab][shtab] installed, you can do this with
`dvci generate-completion`, which will print the shell-completion code for your
shell. For more details on how to set this up, consult shtab's
[documentation][shtab-setup].

## Usage

### Initialization

Before using dvci for the first time, you may want to add the dvci plugin
to your `docums.yml` file. This plugin is added by default when building your
documentation with dvci, but by adding it explicitly, you can configure how it
works. The plugin adds a version selector to supported themes as well as
updating the `site_url` (if you set it) to point to the version of the docs that
are being built:

```yaml
plugins:
  - dvci:
      # these fields are all optional; the defaults are as below...
      version_selector: true   # set to false to leave out the version selector
      css_dir: css             # the directory to put the version selector's CSS
      javascript_dir: js       # the directory to put the version selector's JS
      canonical_version: null  # the version for <link rel="canonical">; `null`
                               # uses the version specified via `dvci deploy`
```

Note: If you have existing documentation on your `gh-pages` branch, you may also
want to delete the old documentation before building your new versioned docs via
[`dvci delete --all`](#deleting-docs).)

### Building Your Docs

dvci is designed to produce one version of your docs at a time. That way, you
can easily deploy a new version without touching any older versions of your
docs; this can be especially important if your old docs are no longer buildable
with the newest version of Docums (or if they weren't built with Docums at
all!). To deploy the current version of your docs, simply run:

```sh
dvci deploy [version]
```

Where `[version]` is the current version of your project, represented however
you like (I recommend using `[major].[minor]` and excluding the patch
number). You can also pass aliases to the `deploy` command to host a
particularly-relevant version of your docs somewhere special (e.g. `latest`):

```sh
dvci deploy [version] [alias]...
```

If `[version]` already exists, this command will *also* update all of the
pre-existing aliases for it. Normally, if an alias specified on the command line
is already associated with another version, this will return an error. If you
*do* want to move an alias from another version to this version (e.g. when
releasing a new version and updating the `latest` alias to point to this new
version), you can pass `-u`/`--update-aliases` to allow this.

By default, aliases create a simple HTML redirect to the real version of the
docs; to create a copy of the docs for each alias, you can pass `--no-redirect`.
If you're using redirects, you can customize the redirect template with
`-T`/`--template`; this takes a path to a [Jinja][jinja] template that accepts
an `{{href}}` variable.

If you'd like to specify a title for this version that doesn't match the version
string, you can pass `-t TITLE`/`--title=TITLE` as well.

In addition, you can specify where to deploy your docs via `-b`/`--branch`,
`-r`/`--remote`, and `--prefix`, specifying the branch, remote, and directory
prefix within the branch, respectively. Finally, to push your docs to a remote
branch, simply add `-p`/`--push` to your command.

### Viewing Your Docs

To test that your docs have been built as expected, you can serve them locally
from a dev server:

```sh
dvci serve
```

By default, this serves the docs on `http://localhost:8000`, but you can
change this with `-a`/`--dev-addr`. Remember though, *this is for testing only*.
To host your docs for real, you should use a real web server.

### Deleting Docs

Sometimes you need to delete an old version of your docs, either because you
made a mistake or you're pruning unsupported versions. You can do this via the
`delete` subcommand:

```sh
dvci delete [version-or-alias]...
```

If `version-or-alias` is a version, this will delete the version and all its
aliases from the branch; if it's an alias, it will only delete that alias.

If you'd like to *completely* wipe the contents of your docs branch, just run
`dvci delete --all`. Like `deploy` above, you can specify `--branch`, `--push`,
etc to control how the commit is handled.

### Listing Docs

If you ever need to see the list of all currently-deployed doc versions, you can
run:

```sh
dvci list
```

To list the info for a particular version, you can just pass the version or
alias:

```sh
dvci list [version-or-alias]
```

Sometimes, you need this information to be consumed by another tool. In that
case, pass `-j`/`--json` to return the list of doc versions as JSON.

### Setting the Default Version

With all the versions of docs you have, you may want to set a *default* version
so that people going to the root of your site are redirected to the latest
version of the docs:

```sh
dvci set-default [version-or-alias]
```

If you want to use a different template from the default, you can pass
`-T`/`--template`; this takes a path to a [Jinja][jinja] template that accepts
an `{{href}}` variable.

Like `deploy` and `delete` above, you can specify `--branch`, `--push`,
etc to control how the commit is handled.

### Changing a Version's Title

As you update your docs, you may want to change the title of a particular
version. For example, your `1.0` docs might have the title `1.0.0`, and when you
release a new patch, you want to update the title to `1.0.1`. You can do this
with the `retitle` command:

```sh
dvci retitle [version-or-alias] [title]
```

As with other commands that change your docs, you can specify `--branch`,
`--push`, etc to control how the commit is handled.

### Adding a New Version Alias

Sometimes, you might need to add a new alias for a version without rebuilding
your documentation. You can use the `alias` command for this:

```sh
dvci alias [version-or-alias] [alias]...
```

As with `deploy`, you can pass `-u`/`--update-aliases` to change where an
existing alias points to.

Once again, you can specify `--branch`, `--push`, etc to control how the commit
is handled.

### More Details

For more details on the available options, consult the `--help` command for
dvci.

## Staying in Sync

dvci will do its best to stay in-sync with your remote repository and will
automatically update your local branch to match the remote's if possible (note
that dvci *won't* automatically `git fetch` anything). If your local branch has
diverged from your remote, dvci will leave it as-is and ask you what to do. To
ignore the remote's state, just pass `--ignore`; to update to the remote's
state, pass `--rebase`.

## `CNAME` (and Other Special Files)

Some special files that you'd like to deploy along with your documentation (such
as `CNAME`) aren't related to a particular version of the docs, and instead need
to go in the root directory of your site. There's no special handling for this
in dvci, but since your built docs live on a Git branch, it's still easy to
manage: check out your `gh-pages` branch (or wherever your built docs
live), and commit the necessary files to the root directory.

## Deploying via CI

Since dvci just generates commits to an ordinary Git branch, it should work
smoothly with your favorite CI system. However, you should keep in mind that
some CI systems make shallow clones of your repository, meaning that the CI job
won't have a local instance of your documentation branch to commit to. This will
naturally cause issues when trying to push the commit. This is easy to resolve
though; just manually fetch your `gh-pages` branch (or whichever you deploy to)
before running dvci:

```sh
git fetch origin gh-pages --depth=1
```

You may also need to [configure a Git user][gh-action-commit] so that dvci can
make commits:

```sh
git config user.name ci-bot
git config user.email ci-bot@example.com
```

## For Theme Authors

If you'd like to provide support for dvci in your theme, you just need to
fetch `versions.json` and build a version selector. `versions.json` looks like
this:

```js
[
  {"version": "1.0", "title": "1.0.1", "aliases": ["latest"]},
  {"version": "0.9", "title": "0.9", "aliases": []}
]
```

If you're creating a third-party extension to an existing theme, you add a
setuptools entry point for `dvci.themes` pointing to a Python submodule that
contains `css/` and `js/` subdirectories containing the extra code to be
installed into the user's documentation. This will then automatically be
included via the `dvci` plugin in the user's `docums.yml` file.

To see some examples of how to work with this, check the
[`dvci/themes/docums`](dvci/themes/docums) directory.

## License

This project is licensed under the [BSD 3-clause license](LICENSE).

[setuptools]: https://pythonhosted.org/setuptools/
[shtab]: https://github.com/iterative/shtab
[shtab-setup]: https://github.com/iterative/shtab#cli-usage
[jinja]: https://jinja.palletsprojects.com/
[gh-action-commit]: https://github.com/actions/checkout#push-a-commit-using-the-built-in-token
