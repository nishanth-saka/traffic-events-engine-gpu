curl -X POST "https://traffic-events-engine-production.up.railway.app/ingest/frame" \
  -F "camera_id=test_cam_1" \
  -F "image=@/Users/strangerd/Desktop/SAMPLE.png"


  curl -X POST "https://traffic-events-engine-production.up.railway.app/ingest/frame" \
  -F "camera_id=test_cam_2" \
  -F "image=@/Users/strangerd/Desktop/random.png"

  curl -X POST https://traffic-events-engine-production.up.railway.app/ingest/frame \
  -F "camera_id=det_test" \
  -F "image=@/Users/strangerd/Desktop/random.png"

