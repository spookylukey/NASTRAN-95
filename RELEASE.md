# Release process

To do a new release:

- cd python
- Use `uv version` to set the desired version.
- Commit and push
- Go to https://github.com/spookylukey/NASTRAN-95/actions/workflows/release.yml and trigger the build, including "Publish to PyPI"
- If it succeeds, do:

  ```
  git tag v$(uv version --short | tr -d '\n')
  git push
  ```

