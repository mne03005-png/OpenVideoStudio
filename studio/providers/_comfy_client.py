"""Shared ComfyUI HTTP client. Both comfyui_sdxl.py and comfyui_ltx.py use
this — submit/poll/retrieve/free logic lives in exactly one place.

Talks to a locally-running ComfyUI server over its HTTP API: submit -> poll
/history -> check status_str -> pull output -> /free to release VRAM
between jobs.
"""
from __future__ import annotations

import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional

import requests


class ComfyError(RuntimeError):
    pass


class ComfyClient:
    def __init__(self, server: str = "http://127.0.0.1:8188", comfy_root: Optional[Path] = None):
        self.server = server.rstrip("/")
        # comfy_root is the ComfyUI/ dir itself (holding input/ and output/),
        # i.e. .../ComfyUI_windows_portable/ComfyUI. Every install lives
        # somewhere different, so there's no safe default to guess: pass it
        # explicitly or set the COMFYUI_ROOT environment variable.
        root = comfy_root or os.environ.get("COMFYUI_ROOT")
        # Users commonly copy Windows paths into .env files, where a path can
        # contain either separator. Normalising backslashes makes that setting
        # work consistently when tests or launch scripts run on another OS.
        self.comfy_root = Path(str(root).replace("\\", os.sep)) if root else None

    def _require_comfy_root(self) -> Path:
        if self.comfy_root is None:
            raise ComfyError(
                "comfy_root is not configured — pass ComfyClient(comfy_root=...) "
                "or set the COMFYUI_ROOT environment variable to your ComfyUI/ "
                "directory (the one containing input/ and output/)."
            )
        return self.comfy_root

    def is_available(self, timeout: float = 5.0) -> bool:
        try:
            r = requests.get(f"{self.server}/system_stats", timeout=timeout)
            return r.status_code == 200
        except requests.RequestException:
            return False

    def upload_input_image(self, local_path: Path, dest_name: Optional[str] = None) -> str:
        """LTXV's LoadImage node reads from ComfyUI's own input/ dir, so the
        keyframe has to be copied in before submitting."""
        dest_name = dest_name or f"{uuid.uuid4().hex}{Path(local_path).suffix}"
        dest_path = self._require_comfy_root() / "input" / dest_name
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(local_path, dest_path)
        return dest_name

    def submit(self, graph: dict, client_id_prefix: str = "openvideostudio") -> str:
        body = {"prompt": graph, "client_id": f"{client_id_prefix}-{uuid.uuid4().hex[:8]}"}
        r = requests.post(f"{self.server}/prompt", json=body, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get("node_errors"):
            raise ComfyError(f"ComfyUI rejected the graph: {data['node_errors']}")
        return data["prompt_id"]

    def wait_for_result(self, prompt_id: str, timeout_minutes: float = 6.0, poll_seconds: float = 2.0) -> dict:
        deadline = time.time() + timeout_minutes * 60
        while time.time() < deadline:
            r = requests.get(f"{self.server}/history/{prompt_id}", timeout=10)
            r.raise_for_status()
            history = r.json()
            entry = history.get(prompt_id)
            if entry:
                status = entry.get("status", {}).get("status_str")
                if status == "success":
                    return entry
                if status == "error":
                    raise ComfyError(f"ComfyUI job failed: {entry.get('status', {}).get('messages')}")
            time.sleep(poll_seconds)
        # Don't leave the job running/queued behind on timeout — a caller
        # retry would otherwise stack a second heavy job on top of it.
        self.cancel(prompt_id)
        raise ComfyError(f"ComfyUI job {prompt_id} timed out after {timeout_minutes} minutes")

    def cancel(self, prompt_id: str) -> None:
        """Best-effort: interrupt only if prompt_id is the job actually
        running, dequeue only if it's still pending. /interrupt has no
        target argument and stops whatever is currently running server-side,
        so calling it unconditionally could kill an unrelated job that
        happened to be running when our own prompt was still queued."""
        running_ids: set = set()
        pending_ids: set = set()
        try:
            r = requests.get(f"{self.server}/queue", timeout=10)
            r.raise_for_status()
            q = r.json()
            running_ids = {entry[1] for entry in q.get("queue_running", [])}
            pending_ids = {entry[1] for entry in q.get("queue_pending", [])}
        except (requests.RequestException, ValueError, IndexError, KeyError, TypeError):
            pass  # if we can't tell, don't touch anything else's job

        if prompt_id in pending_ids:
            try:
                requests.post(f"{self.server}/queue", json={"delete": [prompt_id]}, timeout=10)
            except requests.RequestException:
                pass
        if prompt_id in running_ids:
            try:
                requests.post(f"{self.server}/interrupt", timeout=10)
            except requests.RequestException:
                pass

    def output_path(self, entry: dict, node_id: str, media_key: str = "images") -> Path:
        """media_key is 'images' or 'videos' depending on the SaveImage/SaveVideo node."""
        items = entry.get("outputs", {}).get(node_id, {}).get(media_key)
        if not items:
            raise ComfyError(f"No '{media_key}' output found on node {node_id}")
        item = items[0]
        return self._require_comfy_root() / "output" / item.get("subfolder", "") / item["filename"]

    def free(self, unload_models: bool = True, free_memory: bool = True) -> bool:
        """Release VRAM between jobs/providers — the sequencing discipline
        this machine's 6GB card needs between SDXL and LTX stages. Returns
        whether the server actually confirmed the request, so callers can
        tell a real release from a silently-swallowed failure instead of
        just logging "called" regardless of outcome."""
        try:
            r = requests.post(
                f"{self.server}/free",
                json={"unload_models": unload_models, "free_memory": free_memory},
                timeout=15,
            )
            return r.status_code == 200
        except requests.RequestException:
            return False  # best-effort; caller decides how to react
