import cv2
import numpy as np
from typing import List, Literal
import tempfile
import streamlit as st


def detect_significant_movement_mean(frames: List[np.ndarray], threshold: float = 50.0) -> List[int]:

    movement_indices = []
    prev_gray = None
    for idx, frame in enumerate(frames):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            score = np.mean(diff)
            if score > threshold:
                movement_indices.append(idx)
        prev_gray = gray
    return movement_indices


def detect_significant_movement_orb(
    frames: List[np.ndarray],
    min_matches: int = 10,
    movement_thresh: float = 0.15,
) -> List[int]:
    movement_indices = []
    orb = cv2.ORB_create()
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    prev_kp, prev_des = None, None
    prev_gray = None
    for idx, frame in enumerate(frames):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        kp, des = orb.detectAndCompute(gray, None)
        if prev_des is not None and des is not None and len(kp) > 0 and len(prev_kp) > 0:
            matches = bf.match(prev_des, des)
            matches = sorted(matches, key=lambda x: x.distance)
            if len(matches) > min_matches:
                src_pts = np.float32([prev_kp[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
                H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                if H is not None:
                    dx = H[0, 2]
                    dy = H[1, 2]
                    da = np.arctan2(H[1, 0], H[0, 0])
                    norm_shift = np.sqrt(dx ** 2 + dy ** 2) / max(gray.shape)
                    norm_angle = np.abs(da) / np.pi
                    if norm_shift > movement_thresh or norm_angle > movement_thresh:
                        movement_indices.append(idx)
        prev_kp, prev_des = kp, des
        prev_gray = gray
    return movement_indices

def detect_significant_movement(
    frames: List[np.ndarray],
    method: Literal["mean", "orb"] = "orb",
    **kwargs
) -> List[int]:
    if method == "mean":
        return detect_significant_movement_mean(frames, **kwargs)
    else:
        return detect_significant_movement_orb(frames, **kwargs)
