# arel - Example

This example Starlette web application renders pages dynamically from local Markdown files.

For performance, files are not read from disk on each request. Instead, all pages are rendered into memory on application startup.

During development, if we make edits to the content we'd like the browser to automatically reload the page without having to restart the entire server.

## Installation

- Clone the [`arel`](https://github.com/florimondmanca/arel) repository.
- Make sure you are in the repository root directory.
- Install dependencies: `$ make install`.

## Usage

- Start the server: `$ make serve`.
- Open your browser at http://localhost:8000.
- Add, edit or delete one of the Markdown files in `pages/`.
- A message should appear in the console, and the page should refresh automatically.
