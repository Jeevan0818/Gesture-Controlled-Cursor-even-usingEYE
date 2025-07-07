
import cv2
import mediapipe as mp
import pyautogui
import webbrowser
import numpy as np
import time
import speech_recognition as sr
from datetime import datetime
from tkinter import Tk, Label

cam = cv2.VideoCapture(0)
hands = mp.solutions.hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.8)
face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
mp_draw = mp.solutions.drawing_utils
screen_w, screen_h = pyautogui.size()

smooth_x, smooth_y = 0, 0
eye_closed_start_time = None
voice_recognition_active = False

def activate_voice_recognition():
    global voice_recognition_active
    root = Tk()
    root.title("Voice Recognition")
    root.geometry("300x100") 
    label = Label(root, text="Voice Recognition Active!", font=("Arial", 14))
    label.pack(pady=20)
    root.update()

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print("Listening...")
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio).lower()
            print(f"You said: {command}")

            websites = {
                "youtube": "https://www.youtube.com",
                "google": "https://www.google.com",
                "facebook": "https://www.facebook.com",
                "telegram": "https://web.telegram.org",
                "whatsapp": "https://web.whatsapp.com",
                "snapchat": "https://www.snapchat.com",
                "x": "https://twitter.com",
                "instagram": "https://instagram.com",
                "coder": "https://leetcode.com",
                "chatgpt": "https://chatgpt.com",
                "netflix": "https://www.netflix.com",
                "w3schools": "https://w3schools.com"
            }

            if "time" in command:
                now = datetime.now()
                pyautogui.alert(f"The current time is {now.strftime('%H:%M:%S')}")
            elif "date" in command:
                today = datetime.today()
                pyautogui.alert(f"Today's date is {today.strftime('%Y-%m-%d')}")
            elif "joke" in command:
                pyautogui.alert("Why don't skeletons fight each other? They don't have the guts!")
            elif command in websites:
                webbrowser.open(websites[command])
            else:
                pyautogui.alert("Sorry, I didn't understand that command.")

        except sr.UnknownValueError:
            pyautogui.alert("Sorry, I couldn't understand what you said.")
        except sr.RequestError:
            pyautogui.alert("Voice recognition service is unavailable.")

    root.destroy()
    voice_recognition_active = False

def smooth_coordinates(new_x, new_y, alpha=0.5):
    global smooth_x, smooth_y
    smooth_x = alpha * new_x + (1 - alpha) * smooth_x
    smooth_y = alpha * new_y + (1 - alpha) * smooth_y
    return int(smooth_x), int(smooth_y)

def count_fingers(hand_landmarks, hand_type):
    finger_states = []
    fingertips = [8, 12, 16, 20]
    thumb_tip = 4

    if hand_landmarks:
        for tip in fingertips:
            finger_states.append(1 if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y else 0)
        if hand_type == "Right":
            finger_states.append(1 if hand_landmarks.landmark[thumb_tip].x > hand_landmarks.landmark[thumb_tip - 1].x else 0)
        else:
            finger_states.append(1 if hand_landmarks.landmark[thumb_tip].x < hand_landmarks.landmark[thumb_tip - 1].x else 0)
    return finger_states.count(1)

def track_eyes_and_control_cursor(frame, landmarks):
    global eye_closed_start_time
    frame_h, frame_w, _ = frame.shape
    for id, landmark in enumerate(landmarks[474:478]):
        x, y = int(landmark.x * frame_w), int(landmark.y * frame_h)
        cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
        if id == 1:
            screen_x, screen_y = smooth_coordinates(landmark.x * screen_w, landmark.y * screen_h)
            pyautogui.moveTo(screen_x, screen_y)

    left_eye = [landmarks[145], landmarks[159]]
    left_eye_closed = abs(int(left_eye[0].y * frame_h) - int(left_eye[1].y * frame_h)) < 10

    if left_eye_closed:
        if eye_closed_start_time is None:
            eye_closed_start_time = time.time()
        elif time.time() - eye_closed_start_time > 1:
            pyautogui.click()
            eye_closed_start_time = None
    else:
        eye_closed_start_time = None

def track_eyes_and_mouth(frame, landmarks):
    global voice_recognition_active
    frame_h, frame_w, _ = frame.shape
    mouth_opening = abs(int(landmarks[13].y * frame_h) - int(landmarks[14].y * frame_h))
    if mouth_opening > 20 and not voice_recognition_active:
        voice_recognition_active = True
        activate_voice_recognition()

while True:
    _, frame = cam.read()
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    hand_output = hands.process(rgb_frame)
    if hand_output.multi_hand_landmarks:
        for hand_landmarks, hand_type in zip(hand_output.multi_hand_landmarks, hand_output.multi_handedness):
            hand_label = hand_type.classification[0].label
            mp_draw.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
            finger_count = count_fingers(hand_landmarks, hand_label)
            
            if hand_label == "Right":
                if finger_count == 5:
                    pyautogui.press("volumeup")
                elif finger_count == 4:
                    pyautogui.scroll(30)
                elif finger_count == 3:
                    pyautogui.rightClick()
                elif finger_count == 2:
                    pyautogui.click()
            elif hand_label == "Left":
                if finger_count == 5:
                    pyautogui.press("volumedown")
                elif finger_count == 4:
                    pyautogui.scroll(-30)
                elif finger_count == 3:
                    pyautogui.leftClick()
                elif finger_count == 2:
                    pyautogui.doubleClick()
    
    face_output = face_mesh.process(rgb_frame)
    if face_output.multi_face_landmarks:
        landmarks = face_output.multi_face_landmarks[0].landmark
        track_eyes_and_mouth(frame, landmarks)
        track_eyes_and_control_cursor(frame, landmarks)
    
    cv2.imshow('Hand and Eye Gesture Control', frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cam.release()
cv2.destroyAllWindows()
