import sys
import os
import json
import base64


def _add_onnx_dll_dirs():
    """Setup DLL directories for onnxruntime in frozen PyInstaller environments."""
    base_path = getattr(sys, "_MEIPASS", None)
    if not base_path:
        return

    from pathlib import Path
    candidates = [
        Path(base_path) / "onnxruntime" / "capi",
        Path(base_path) / "_internal" / "onnxruntime" / "capi",
    ]

    for capi_dir in candidates:
        if capi_dir.exists() and capi_dir.is_dir():
            current_path = os.environ.get("PATH", "")
            os.environ["PATH"] = str(capi_dir) + os.pathsep + base_path + os.pathsep + current_path

            if hasattr(os, 'add_dll_directory'):
                for d in [capi_dir, Path(base_path)]:
                    try:
                        os.add_dll_directory(str(d))
                    except OSError:
                        pass
            break


def _create_session(model_path: str):
    """Create an ONNX InferenceSession with GPU priority, falling back to CPU."""
    # Pre-import numpy so onnxruntime_pybind11_state.pyd finds it in sys.modules
    import numpy as np  # noqa: F401
    import onnxruntime as ort

    # [OPT-1] Session Options: graph optimization + DirectML compatibility
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    opts.enable_mem_pattern = False       # Required for DirectML
    opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

    providers = ['CUDAExecutionProvider', 'DmlExecutionProvider', 'CPUExecutionProvider']
    try:
        sess = ort.InferenceSession(model_path, sess_options=opts, providers=providers)
        return sess, sess.get_providers()
    except Exception as e:
        sess = ort.InferenceSession(model_path, sess_options=opts, providers=["CPUExecutionProvider"])
        return sess, ["CPUExecutionProvider (Fallback)", str(e)]


LABELS = [
    "FEMALE_GENITALIA_COVERED", "FACE_FEMALE", "BUTTOCKS_EXPOSED",
    "FEMALE_BREAST_EXPOSED", "FEMALE_GENITALIA_EXPOSED", "MALE_BREAST_EXPOSED",
    "ANUS_EXPOSED", "FEET_EXPOSED", "BELLY_COVERED", "FEET_COVERED",
    "ARMPITS_COVERED", "ARMPITS_EXPOSED", "FACE_MALE", "BELLY_EXPOSED",
    "MALE_GENITALIA_EXPOSED", "ANUS_COVERED", "FEMALE_BREAST_COVERED",
    "BUTTOCKS_COVERED"
]


def run_worker():
    _add_onnx_dll_dirs()

    import numpy as np
    import cv2

    session = None
    input_name = None
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))  # [OPT-3] CLAHE instance

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
            cmd = req.get("cmd")

            if cmd == "load":
                model_path = req["model_path"]
                try:
                    session, providers = _create_session(model_path)
                    input_name = session.get_inputs()[0].name
                    print(json.dumps({"ok": True, "providers": providers}), flush=True)
                except Exception as e:
                    import traceback
                    print(json.dumps({"ok": False, "error": repr(e), "trace": traceback.format_exc()}), flush=True)

            elif cmd == "infer":
                if session is None:
                    print(json.dumps({"ok": False, "error": "model_not_loaded"}), flush=True)
                    continue

                img_data = base64.b64decode(req["image_b64"])
                np_arr = np.frombuffer(img_data, np.uint8)
                img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                if img_bgr is None:
                    print(json.dumps({"ok": False, "error": "failed_to_decode_image"}), flush=True)
                    continue

                # [OPT-2] Resolution: accept from command, default 640
                resolution = req.get("resolution", 640)

                # [OPT-3] CLAHE: improve contrast for dark scenes
                lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
                lab[:, :, 0] = clahe.apply(lab[:, :, 0])
                img_enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

                # Preprocess
                h, w = img_enhanced.shape[:2]
                img_rgb = cv2.cvtColor(img_enhanced, cv2.COLOR_BGR2RGB)
                max_size = max(h, w)
                x_pad = max_size - w
                y_pad = max_size - h

                if x_pad > 0 or y_pad > 0:
                    mat_pad = cv2.copyMakeBorder(img_rgb, 0, y_pad, 0, x_pad, cv2.BORDER_CONSTANT)
                else:
                    mat_pad = img_rgb

                blob = cv2.dnn.blobFromImage(
                    mat_pad, 1 / 255.0, (resolution, resolution),
                    (0, 0, 0), swapRB=False, crop=False
                )

                # Inference
                out = session.run(None, {input_name: blob})
                data = np.transpose(np.squeeze(out[0]))

                # Postprocess
                boxes, scores, class_ids = [], [], []

                for i in range(data.shape[0]):
                    class_scores = data[i][4:]
                    max_score = np.amax(class_scores)

                    if max_score >= 0.15:  # [OPT-4] Lowered from 0.20 for better recall
                        class_id = np.argmax(class_scores)
                        cx, cy, bw, bh = data[i][0:4]

                        x = (cx - bw / 2) * (w + x_pad) / resolution
                        y = (cy - bh / 2) * (h + y_pad) / resolution
                        bw = bw * (w + x_pad) / resolution
                        bh = bh * (h + y_pad) / resolution

                        boxes.append([int(x), int(y), int(bw), int(bh)])
                        scores.append(float(max_score))
                        class_ids.append(int(class_id))

                result_dets = []
                if boxes:
                    indices = cv2.dnn.NMSBoxes(boxes, scores, 0.25, 0.45)
                    if len(indices) > 0:
                        flat_indices = indices.flatten() if hasattr(indices, 'flatten') else indices
                        for idx in flat_indices:
                            i = idx[0] if isinstance(idx, (list, tuple, np.ndarray)) else idx
                            result_dets.append({'class': LABELS[class_ids[i]], 'score': scores[i]})

                print(json.dumps({"ok": True, "detections": result_dets}), flush=True)

            elif cmd == "ping":
                print(json.dumps({"ok": True}), flush=True)

            else:
                print(json.dumps({"ok": False, "error": f"unknown_cmd:{cmd}"}), flush=True)

        except Exception as e:
            import traceback
            print(json.dumps({"ok": False, "error": repr(e), "trace": traceback.format_exc()}), flush=True)


if __name__ == "__main__":
    run_worker()
