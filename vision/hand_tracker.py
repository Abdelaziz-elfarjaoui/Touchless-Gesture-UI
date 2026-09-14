import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandTracker:
    def __init__(self, model_path, width=640, height=480, smoothing=.5):
        self.width,self.height,self.smoothing=width,height,smoothing
        self.x=self.y=None; self.last_seen=0; self.confidence=0.0
        opts=vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,num_hands=1,
            min_hand_detection_confidence=.30,
            min_hand_presence_confidence=.30,
            min_tracking_confidence=.30)
        self.landmarker=vision.HandLandmarker.create_from_options(opts)
        self.timestamp=0
    def detect(self, frame):
        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        img=mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb)
        self.timestamp += 33
        result=self.landmarker.detect_for_video(img,self.timestamp)
        if result.hand_landmarks:
            hand=result.hand_landmarks[0]; tip=hand[8]
            rawx=max(0,min(self.width-1,int(tip.x*self.width)))
            rawy=max(0,min(self.height-1,int(tip.y*self.height)))
            if self.x is None: self.x,self.y=rawx,rawy
            else:
                self.x=self.smoothing*rawx+(1-self.smoothing)*self.x
                self.y=self.smoothing*rawy+(1-self.smoothing)*self.y
            self.last_seen=time.time()
            try: self.confidence=float(result.handedness[0][0].score)
            except Exception: self.confidence=1.0
            return (int(self.x),int(self.y)),True,self.confidence
        self.confidence=0.0
        if self.x is not None and time.time()-self.last_seen < .20:
            return (int(self.x),int(self.y)),False,0.0
        return None,False,0.0
    def close(self): self.landmarker.close()
