import os
from PIL import Image
from app.inference.visual.face_detector import FaceDetection
from app.inference.visual.deepfake_classifier import classify_deepfakes
from app.inference.crossmodal.context_matcher import match_context
from app.inference.crossmodal.lipsync_checker import check_lipsync

def create_dummy_image(path):
    img = Image.new('RGB', (224, 224), color = 'red')
    img.save(path)

def test_deepfake_classifier():
    print("--- Testing Deepfake Classifier ---")
    dummy_crop = "dummy_face.jpg"
    create_dummy_image(dummy_crop)
    
    detection = FaceDetection(frame_idx=0, bbox=[0,0,100,100], crop_path=dummy_crop, confidence=0.99)
    result = classify_deepfakes([detection])
    print(f"Deepfake Result: {result.fake_probability:.4f} | Hint: {result.manipulation_type}")
    
    if os.path.exists(dummy_crop):
        os.remove(dummy_crop)

def test_context_matcher():
    print("--- Testing Context Matcher (CLIP) ---")
    dummy_img = "dummy_scene.jpg"
    create_dummy_image(dummy_img)
    
    result = match_context(dummy_img, "A random red square dummy image")
    print(f"CLIP Similarity: {result.clip_similarity:.4f} | Flags: {result.flags}")
    
    if os.path.exists(dummy_img):
        os.remove(dummy_img)

def test_lipsync():
    print("--- Testing Lipsync (Proxy) ---")
    # Will fail real lipsync because no real video, testing fallback logic
    result = check_lipsync("video", "dummy_video.mp4", faces_detected=True)
    print(f"Lipsync Confidence: {result.sync_confidence:.2f} | Offset: {result.offset_frames}")

if __name__ == "__main__":
    test_deepfake_classifier()
    test_context_matcher()
    test_lipsync()
    print("--- All tests finished ---")
