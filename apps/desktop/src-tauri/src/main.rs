// Entrypoint binary — delegates to the library so the app logic is
// testable and reusable across desktop/mobile targets if ever needed.
fn main() {
    spectra_desktop_lib::run()
}
