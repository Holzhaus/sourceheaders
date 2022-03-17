# sourceheaders

Adds or replaces header comments (usually containing licensing information) in
source files.

## Configuration

You can configure *sourceheaders* by placing a `.sourceheaders.toml` file into
your project root.

```toml
[general]
license = "MPL-2.0"
copyright_holder = "John Doe <john.doe@example.com>"
prefer_inline = true
width = 70

[language.rust]
width = 99
```

## Usage

### Command line

You can run *sourceheaders* manually on the command line and pass one or more
file paths.

```shell-session
$ sourceheaders /path/to/file.py /path/to/other/file.rs
Added header to /path/to/file.py
Replaced header in /path/to/other/file.rs
```

### Pre-commit

*sourceheaders* can be used with [pre-commit](https://pre-commit.com).
Add the following lines to your `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/Holzhaus/sourceheaders
    rev: ""
    hooks:
    -   id: sourceheaders
```

Either specify a specific hook version in the `rev` field directly, or run the
this command to automatically fill in the latest version:

```shell-session
$ pre-commit autoupdate --repo "https://github.com/Holzhaus/sourceheaders"
Updating https://github.com/Holzhaus/sourceheaders ... updating  -> <latest-version>.
```
