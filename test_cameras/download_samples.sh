#!/bin/bash
# ============================================================
#  Download sample test videos for CCTV Anomaly Detection
#  Covers: crowd, knife/weapon, traffic, fighting/running
# ============================================================

set -e
DEST="$(dirname "$0")/../static/videos/samples"
mkdir -p "$DEST"

echo ""
echo "=============================================="
echo "  Downloading test videos..."
echo "  Destination: $DEST"
echo "=============================================="
echo ""

# --- CROWD GATHERING ---
echo "[1/5] Crowd gathering — Shibuya Crossing (many people)"
curl -L -o "$DEST/crowd_shibuya_crossing.mp4" \
  "https://videos.pexels.com/video-files/25947490/25947490-uhd_2560_1440_25fps.mp4" \
  --progress-bar 2>/dev/null || echo "  (failed, trying alt...)" && \
curl -L -o "$DEST/crowd_shibuya_crossing.mp4" \
  "https://videos.pexels.com/video-files/25947490/25947490-hd_1920_1080_25fps.mp4" \
  --progress-bar 2>/dev/null || echo "  SKIP — download this manually from pexels.com/video/25947490"

echo "[2/5] Crowd gathering — St Peter's Square"
curl -L -o "$DEST/crowd_st_peters.mp4" \
  "https://videos.pexels.com/video-files/37834012/37834012-uhd_2560_1440_25fps.mp4" \
  --progress-bar 2>/dev/null || echo "  SKIP — download from pexels.com/video/37834012"

# --- KNIFE / WEAPON ---
echo "[3/5] Knife — man with knife (COCO class: knife)"
curl -L -o "$DEST/knife_man_with_knife.mp4" \
  "https://videos.pexels.com/video-files/18196283/18196283-uhd_2560_1440_25fps.mp4" \
  --progress-bar 2>/dev/null || echo "  (failed, trying alt...)" && \
curl -L -o "$DEST/knife_man_with_knife.mp4" \
  "https://videos.pexels.com/video-files/18196283/18196283-hd_1920_1080_25fps.mp4" \
  --progress-bar 2>/dev/null || echo "  SKIP — download from pexels.com/video/18196283"

echo "[4/5] Knife — tactical soldiers (weapons visible)"
curl -L -o "$DEST/weapon_tactical_soldiers.mp4" \
  "https://videos.pexels.com/video-files/29684323/29684323-uhd_2560_1440_25fps.mp4" \
  --progress-bar 2>/dev/null || echo "  (failed, trying alt...)" && \
curl -L -o "$DEST/weapon_tactical_soldiers.mp4" \
  "https://videos.pexels.com/video-files/29684323/29684323-hd_1920_1080_25fps.mp4" \
  --progress-bar 2>/dev/null || echo "  SKIP — download from pexels.com/video/29684323"

# --- FIGHTING / RUNNING ---
echo "[5/5] Fighting — sparring combat sport"
curl -L -o "$DEST/fighting_sparring.mp4" \
  "https://videos.pexels.com/video-files/6296163/6296163-uhd_2560_1440_25fps.mp4" \
  --progress-bar 2>/dev/null || echo "  (failed, trying alt...)" && \
curl -L -o "$DEST/fighting_sparring.mp4" \
  "https://videos.pexels.com/video-files/6296163/6296163-hd_1920_1080_25fps.mp4" \
  --progress-bar 2>/dev/null || echo "  SKIP — download from pexels.com/video/6296163"

echo ""
echo "=============================================="
echo "  Checking what downloaded..."
echo "=============================================="
echo ""
for f in "$DEST"/*.mp4; do
  if [ -f "$f" ]; then
    SIZE=$(du -h "$f" | cut -f1)
    DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null | cut -d. -f1)
    echo "  ✓ $(basename "$f")  (${SIZE}, ${DURATION:-?}s)"
  fi
done

echo ""
echo "=============================================="
echo "  MANUAL DOWNLOADS (if above failed):"
echo "=============================================="
echo ""
echo "  CROWD:"
echo "    https://www.pexels.com/video/a-crowded-city-street-with-many-people-walking-25947490/"
echo "    https://www.pexels.com/video/crowd-gathering-at-iconic-st-peters-square-37834012/"
echo "    https://www.pexels.com/video/bustling-city-square-with-diverse-crowd-36208367/"
echo ""
echo "  KNIFE / WEAPON:"
echo "    https://www.pexels.com/video/a-man-dressed-as-a-devil-holding-a-knife-18196283/"
echo "    https://www.pexels.com/video/tactical-soldiers-in-action-in-abandoned-warehouse-29684323/"
echo "    https://mixkit.co/free-stock-video/knife/"
echo ""
echo "  FIGHTING / RUNNING:"
echo "    https://www.pexels.com/video/two-men-sparring-in-a-combat-sport-6296163/"
echo "    https://www.pexels.com/video/fencing-battle-6832365/"
echo ""
echo "  TRAFFIC / VEHICLES:"
echo "    https://www.pexels.com/video/heavy-traffic-jam-on-urban-highway-during-daytime-32909774/"
echo "    https://www.pexels.com/video/vehicles-on-the-road-1393766/"
echo "    https://www.pexels.com/video/traffic-flow-in-the-highway-2103099/"
echo ""
echo "  Upload all .mp4 files to static/videos/ and use the"
echo "  'Upload Video' tab to analyze each one."
echo ""
