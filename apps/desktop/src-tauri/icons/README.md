# Icons

No binary icon files are committed to this repository on purpose (see the
root README's "Do not include large binary files" constraint).

`apps/desktop/src-tauri/tauri.conf.json` references icon paths in this
folder for **bundling/packaging only** (`tauri build`). They are not
required to run the app in development (`npm run tauri dev`).

When you're ready to produce an installer, generate real icons from a
source PNG (1024x1024 recommended):

```bash
npm run tauri icon path/to/source-icon.png
```

This will populate this folder with the platform-specific icon set
(`32x32.png`, `128x128.png`, `128x128@2x.png`, `icon.icns`, `icon.ico`).
