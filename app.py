import streamlit as st
import numpy as np
from PIL import Image
import movement_detector
import cv2
import tempfile

st.title("Camera Movement Detection Demo")
st.write(
    "Bir dizi resim(jpg,jpeg,png) veya bir video (.mp4,.avi,.webm) yükleyin. Uygulama, belirgin kamera hareketi olan kareleri tespit edecektir."
)
st.info("Duyarlılığı artırmak için eşik değerlerini düşürebilirsiniz. ORB için 'hareket eşiği' ve 'minimum eşleşme', Mean için 'fark eşiği' ne kadar düşükse küçük hareketler de tespit edilir.")

input_type = st.radio("Veri tipi seçin:", ["Resim Dizisi(jpg,jpeg,png)", "Video (mp4,avi,webm)"])

frames = []
fps = None
frame_real_indices = None

if input_type == "Resim Dizisi":
    uploaded_files = st.file_uploader(
        "Resim dosyalarını seçin", type=["jpg", "jpeg", "png"], accept_multiple_files=True
    )
    if uploaded_files:
        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file)
            frame = np.array(image)
            if frame.shape[-1] == 4:  # RGBA to RGB
                frame = frame[:, :, :3]
            frames.append(frame)
        st.write(f"{len(frames)} kare yüklendi.")
else:
    uploaded_video = st.file_uploader("Bir mp4 video seçin", type=["mp4","avi","webm"])
    if uploaded_video is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4,.avi,.webm')
        tfile.write(uploaded_video.read())
        cap = cv2.VideoCapture(tfile.name)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        max_frames = st.slider("Analiz edilecek maksimum kare sayısı", 10, 200, 50)
        frame_real_indices = []
        if total_frames > 0:
            indices = np.linspace(0, total_frames - 1, max_frames, dtype=int)
            frames = []
            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if not ret:
                    continue
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame)
                frame_real_indices.append(idx)
            st.write(f"Videodan {len(frames)} kare çıkarıldı (eşit aralıklı). FPS: {fps if fps else 'Bilinmiyor'}")
        else:
            frame_count = 0
            while cap.isOpened() and frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame)
                frame_real_indices.append(frame_count)
                frame_count += 1
            st.write(f"Videodan {len(frames)} kare çıkarıldı. FPS: {fps if fps else 'Bilinmiyor'}")
        cap.release()

if frames:
    detection_method = st.selectbox(
        "Hareket tespit yöntemi seçin:",
        ["ORB (anahtar nokta tabanlı)", "Mean (klasik piksel farkı)"]
    )

    if detection_method.startswith("ORB"):
        min_matches = st.slider("Minimum eşleşme (min_matches)", 3, 20, 5)
        movement_thresh = st.slider("Hareket eşiği (movement_thresh)", 0.005, 0.2, 0.03, step=0.001, format="%.3f")
        method = "orb"
        kwargs = {"min_matches": min_matches, "movement_thresh": movement_thresh}
    else:
        threshold = st.slider("Fark eşiği (threshold)", 5, 50, 15)
        method = "mean"
        kwargs = {"threshold": threshold}

    movement_indices = movement_detector.detect_significant_movement(frames, method=method, **kwargs)
    if fps and input_type == "Video (mp4,avi,webm)" and frame_real_indices is not None:
        frame_saniye_list = [f"{frame_real_indices[idx]} ({frame_real_indices[idx] / fps:.2f} sn)" for idx in movement_indices]
        st.write("Significant movement detected at frames (gerçek frame (saniye)):", frame_saniye_list)
    else:
        st.write("Significant movement detected at frames:", movement_indices)

    for idx in movement_indices:
        if fps and input_type == "Video (mp4,avi,webm)" and frame_real_indices is not None:
            real_idx = frame_real_indices[idx]
            saniye = real_idx / fps if fps else None
            st.image(frames[idx], caption=f"Movement at frame {real_idx} (yaklaşık {saniye:.2f} sn)", use_column_width=True)
        else:
            st.image(frames[idx], caption=f"Movement at frame {idx}", use_column_width=True)
