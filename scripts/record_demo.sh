#!/usr/bin/env bash
# Record ONLY Gazebo and our webcam window, never the rest of the desktop.
set -eo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/env.bash"
for dependency in xdotool ffmpeg; do
 command -v "${dependency}" >/dev/null || { echo "Missing ${dependency}; install xdotool and ffmpeg as described in README."; exit 1; }
done
gazebo_id="$({ xdotool search --onlyvisible --name '^Gazebo$' || true; } | tail -1)"
camera_id="$({ xdotool search --onlyvisible --name 'Lab 06 - REAL WEBCAM' || true; } | tail -1)"
if [[ -z "${gazebo_id}" || -z "${camera_id}" ]]; then
 echo 'Start simulation and control first; both Gazebo and webcam windows must be visible.'; exit 1
fi
mkdir -p "${TB4_WORKSPACE}/submission"
output="${1:-${TB4_WORKSPACE}/submission/demo_lab06_23020732.mp4}"
if [[ -e "${output}" ]]; then output="${TB4_WORKSPACE}/submission/demo_lab06_23020732_$(date +%Y%m%d_%H%M%S).mp4"; fi
echo "Recording two application windows. Press q in THIS terminal when finished and wait for FFmpeg to exit (or press Ctrl+C once). Output: ${output}"
exec ffmpeg -hide_banner -loglevel warning \
 -thread_queue_size 64 -f x11grab -framerate 10 -window_id "${gazebo_id}" -i "${DISPLAY:-:0}" \
 -thread_queue_size 64 -f x11grab -framerate 10 -window_id "${camera_id}" -i "${DISPLAY:-:0}" \
 -filter_complex '[0:v]scale=960:720:force_original_aspect_ratio=decrease,pad=960:720:(ow-iw)/2:(oh-ih)/2,setsar=1[a];[1:v]scale=640:720:force_original_aspect_ratio=decrease,pad=640:720:(ow-iw)/2:(oh-ih)/2,setsar=1[b];[a][b]hstack=inputs=2[v]' \
 -map '[v]' -an -c:v libx264 -threads 2 -preset ultrafast -crf 23 \
 -profile:v baseline -pix_fmt yuv420p -r 10 -movflags +faststart "${output}"
