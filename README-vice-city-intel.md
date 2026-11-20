# Vice City Intel Shorts
Independent short-video workflow. No changes to JonkersGym or MijnWagen.

## Run from iPhone
Open **Actions → Build Vice City Intel Short → Run workflow**. Optionally enter a topic and English narration. After completion, open the run's **Artifacts** section and download `vice-city-intel-short` (ZIP containing MP4 and YouTube text).

Uses free FFmpeg, Pillow and Edge TTS on GitHub-hosted Actions. Edge TTS relies on an unofficial online speech endpoint and may be unavailable or rate-limited. It is not a guaranteed unlimited commercial voice service.

To add new original images, place portrait PNG/JPG files under `assets/`. Without images, the script uses locally drawn neon graphic slides; it does **not** generate AI images by itself. Captions are timed approximately by sentence length; check alignment before publishing. The example script is general PS5 troubleshooting, not a verified GTA 6-specific fix.

**Cost:** public repository Actions using standard runners are generally free; private repository usage may count against plan limits.
