// Spectra desktop shell — Tauri Rust entrypoint.
//
// Phase 0 scope: launch the window and load the Vite/React frontend.
// No Tauri commands, no native system integration, no file-system or
// process-spawning bridges are implemented yet. Those arrive in later
// phases (e.g. Phase 6 file intelligence, Phase 7 tool execution) and
// must each declare a permission level per docs/ENGINEERING_RULES.md.

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running the Spectra desktop shell");
}
