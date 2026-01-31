curl -X POST \
  -F "camera_id=cam_1" \
  -F "image=@/Users/strangerd/Desktop/random.png" \
  https://traffic-events-engine-production.up.railway.app/ingest/frame

  curl -X POST \
  -F "camera_id=cam_1" \
  -F "image=@/Users/strangerd/Desktop/SAMPLE.png" \
  https://traffic-events-engine-production.up.railway.app/ingest/frame

  curl https://traffic-events-engine-production.up.railway.app/debug/pipeline

  ffmpeg -rtsp_transport tcp \
  -i "rtsp://admin:Admin%40123@103.88.236.191:10554/cam/realmonitor?channel=1&subtype=0" \
  -f null -


https://traffic-events-engine-production.up.railway.app/preview/stream/cam_1


