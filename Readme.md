curl -X POST \
  -F "camera_id=cam_1" \
  -F "image=@/Users/strangerd/Desktop/random.png" \
  https://traffic-events-engine-production.up.railway.app/ingest/frame

  curl https://traffic-events-engine-production.up.railway.app/debug/pipeline

