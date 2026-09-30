import json
import os
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import yt_dlp

# ---------------------------------------------------------------------------
# ค่าคงที่ / การตั้งค่า
# ---------------------------------------------------------------------------
DEFAULT_DOWNLOAD_DIR = r"D:\YouTube Downloads"
URL_PLACEHOLDER = "วางลิงก์ YouTube ที่นี่... (เช่น https://youtube.com/watch?v=...)"

# ไฟล์เก็บค่าโฟลเดอร์ที่ผู้ใช้เลือกไว้ล่าสุด (เก็บข้าง exe / script)
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "downloader_config.json"
)

COLORS = {
    "bg": "#181825",
    "surface": "#1e1e2e",
    "card": "#313244",
    "border": "#45475a",
    "accent": "#cba6f7",
    "accent2": "#89b4fa",
    "text": "#cdd6f4",
    "muted_text": "#6c7086",
    "muted": "#a6adc8",
    "success": "#a6e3a1",
    "warning": "#f9e2af",
    "error": "#f38ba8",
}


def looks_like_youtube_url(text: str) -> bool:
    """เช็คแบบคร่าวๆ ว่าข้อความหน้าตาเหมือนลิงก์ YouTube หรือไม่"""
    t = text.strip().lower()
    return t.startswith("http") and ("youtube.com" in t or "youtu.be" in t)


def drive_exists(path: str) -> bool:
    """เช็คว่าไดรฟ์ของ path ที่ให้มามีอยู่จริงในเครื่องหรือไม่ (เช่น D:\\ มีจริงไหม)"""
    drive = os.path.splitdrive(path)[0]  # เช่น "D:"
    if not drive:
        return True  # path สัมพัทธ์ ไม่ใช่ไดรฟ์ ให้ผ่านไปก่อน
    return os.path.exists(drive + os.sep)


def load_saved_folder():
    """โหลดโฟลเดอร์ที่ผู้ใช้เคยเลือกไว้จากไฟล์ config ถ้ามี"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            folder = data.get("download_dir")
            if folder and drive_exists(folder):
                return folder
    except Exception:
        pass
    return None


def save_folder(folder: str):
    """บันทึกโฟลเดอร์ที่ผู้ใช้เลือกไว้ลงไฟล์ config เพื่อจำไว้ใช้ครั้งถัดไป"""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"download_dir": folder}, f, ensure_ascii=False)
    except Exception:
        pass  # บันทึกไม่ได้ก็ไม่เป็นไร แค่ต้องเลือกใหม่รอบหน้า


def ensure_download_dir(path: str) -> bool:
    """สร้างโฟลเดอร์ดาวน์โหลดถ้ายังไม่มี คืนค่า True/False ว่าพร้อมใช้งานหรือไม่"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False


def has_ffmpeg():
    """เช็คว่ามี ffmpeg ใน PATH หรือไม่"""
    return shutil.which("ffmpeg") is not None


def friendly_error(exc: Exception) -> str:
    """แปลง exception จาก yt-dlp ให้เป็นข้อความที่ผู้ใช้ทั่วไปเข้าใจง่าย"""
    msg = str(exc)
    lower = msg.lower()

    if "ffmpeg" in lower or "ffprobe" in lower:
        return (
            "ไม่พบโปรแกรม ffmpeg ในเครื่อง\n"
            "โหมด 'วิดีโอ + เสียง' และการแปลงไฟล์เสียง (MP3) ต้องใช้ ffmpeg\n"
            "กรุณาติดตั้ง ffmpeg แล้วเพิ่มลงใน PATH ก่อนใช้งาน"
        )
    if "unsupported url" in lower or "is not a valid url" in lower:
        return "ลิงก์ที่กรอกไม่ถูกต้อง กรุณาตรวจสอบ URL อีกครั้ง"
    if "video unavailable" in lower:
        return "วิดีโอนี้ไม่พร้อมใช้งาน (อาจถูกลบหรือถูกจำกัดพื้นที่)"
    if "private video" in lower:
        return "วิดีโอนี้เป็นวิดีโอส่วนตัว ไม่สามารถดาวน์โหลดได้"
    if "sign in to confirm" in lower or "age" in lower and "restrict" in lower:
        return "วิดีโอนี้มีการจำกัดอายุ ต้องเข้าสู่ระบบจึงจะดาวน์โหลดได้"
    if "http error 429" in lower or "too many requests" in lower:
        return "ถูกจำกัดการเข้าถึงชั่วคราว (คำขอมากเกินไป) กรุณาลองใหม่ภายหลัง"
    if "network" in lower or "timed out" in lower or "connection" in lower or "urlopen" in lower:
        return "เกิดปัญหาการเชื่อมต่ออินเทอร์เน็ต กรุณาตรวจสอบเครือข่ายแล้วลองใหม่"
    if "no space left" in lower or "disk" in lower:
        return "พื้นที่จัดเก็บไม่เพียงพอ กรุณาตรวจสอบพื้นที่ว่างในโฟลเดอร์ปลายทาง"
    if "permission" in lower or "access is denied" in lower:
        return "ไม่มีสิทธิ์เขียนไฟล์ลงในโฟลเดอร์ปลายทาง กรุณาตรวจสอบสิทธิ์การเข้าถึง"

    short = msg.splitlines()[0]
    if len(short) > 160:
        short = short[:160] + "..."
    return f"เกิดข้อผิดพลาดที่ไม่คาดคิด:\n{short}"


class PremiumYoutubeDownloader:

    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader Studio")
        self.root.geometry("560x540")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(False, False)

        self.is_downloading = False
        self.ffmpeg_available = has_ffmpeg()
        self.showing_placeholder = True

        # --- กำหนดโฟลเดอร์ดาวน์โหลดเริ่มต้น ---
        self.download_dir = self.resolve_initial_download_dir()

        self.setup_ui()
        self.refresh_ffmpeg_notice()

    # ------------------------------------------------------------------
    # จัดการโฟลเดอร์ดาวน์โหลด
    # ------------------------------------------------------------------
    def resolve_initial_download_dir(self) -> str:
        """
        ตัดสินใจว่าจะใช้โฟลเดอร์ไหนตอนเปิดโปรแกรม:
        1. ถ้าเคยเลือกไว้และไดรฟ์นั้นยังมีอยู่ -> ใช้ค่าที่เคยเลือก
        2. ถ้าไดรฟ์ D มีอยู่ -> ใช้ D:\\YouTube Downloads ตามค่า default
        3. ถ้าไม่มีทั้งคู่ -> เปิดหน้าต่างให้ผู้ใช้เลือกโฟลเดอร์เอง
        """
        saved = load_saved_folder()
        if saved:
            return saved

        if drive_exists(DEFAULT_DOWNLOAD_DIR) and ensure_download_dir(DEFAULT_DOWNLOAD_DIR):
            return DEFAULT_DOWNLOAD_DIR

        # ไม่มีไดรฟ์ D หรือสร้างโฟลเดอร์ไม่ได้ -> ให้ผู้ใช้เลือกเอง
        messagebox.showwarning(
            "ไม่พบไดรฟ์ D",
            "ไม่พบไดรฟ์ D ในเครื่องนี้ หรือไม่สามารถสร้างโฟลเดอร์ดาวน์โหลดได้\n"
            "กรุณาเลือกโฟลเดอร์สำหรับบันทึกไฟล์ในขั้นตอนถัดไป",
        )
        chosen = self.ask_folder_dialog(initial=os.path.expanduser("~"))
        if chosen:
            save_folder(chosen)
            return chosen

        # ผู้ใช้กด Cancel -> fallback ไปที่โฟลเดอร์เอกสารของผู้ใช้
        fallback = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube Downloads")
        ensure_download_dir(fallback)
        return fallback

    def ask_folder_dialog(self, initial: str = None) -> str:
        """เปิดหน้าต่างเลือกโฟลเดอร์ คืนค่า path ที่เลือก หรือ '' ถ้ายกเลิก"""
        folder = filedialog.askdirectory(
            title="เลือกโฟลเดอร์สำหรับบันทึกไฟล์ที่ดาวน์โหลด",
            initialdir=initial or "/",
            mustexist=True,
        )
        return folder

    def change_download_folder(self):
        """ให้ผู้ใช้เปลี่ยนโฟลเดอร์ปลายทางเองได้ทุกเมื่อผ่านปุ่มใน UI"""
        chosen = self.ask_folder_dialog(initial=self.download_dir)
        if not chosen:
            return
        if not ensure_download_dir(chosen):
            messagebox.showerror(
                "ผิดพลาด",
                f"ไม่สามารถใช้โฟลเดอร์นี้ได้:\n{chosen}\nกรุณาเลือกโฟลเดอร์อื่น",
            )
            return
        self.download_dir = chosen
        save_folder(chosen)
        self.folder_label.config(text=self.download_dir)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def setup_ui(self):
        tk.Label(
            self.root,
            text="🎬 YOUTUBE DOWNLOADER",
            font=("Segoe UI", 17, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["accent"],
        ).pack(pady=(22, 2))

        tk.Label(
            self.root,
            text="เลือกรูปแบบสื่อและวางลิงก์เพื่อเริ่มดาวน์โหลด",
            font=("Segoe UI", 9),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
        ).pack(pady=(0, 14))

        # --- Input ---
        input_frame = tk.Frame(self.root, bg=COLORS["bg"])
        input_frame.pack(pady=5, padx=25, fill="x")

        self.url_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 10),
            bg=COLORS["card"],
            fg=COLORS["muted_text"],
            insertbackground="white",
            relief="flat",
            bd=7,
        )
        self.url_entry.insert(0, URL_PLACEHOLDER)
        self.url_entry.bind("<FocusIn>", self.on_url_focus_in)
        self.url_entry.bind("<FocusOut>", self.on_url_focus_out)
        self.url_entry.bind("<KeyRelease>", self.on_url_changed)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.paste_btn = tk.Button(
            input_frame,
            text="📋 วาง",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["border"],
            fg=COLORS["text"],
            activebackground="#585b70",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.paste_url,
            padx=12,
        )
        self.paste_btn.pack(side="right")

        # --- Format options ---
        option_frame = tk.LabelFrame(
            self.root,
            text=" เลือกประเภทการดาวน์โหลด ",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["accent2"],
            bd=1,
            relief="solid",
        )
        option_frame.pack(pady=14, padx=25, fill="x")

        self.download_type = tk.StringVar(value="both")

        rb_style = {
            "font": ("Segoe UI", 9, "bold"),
            "bg": COLORS["bg"],
            "fg": COLORS["text"],
            "activebackground": COLORS["bg"],
            "activeforeground": COLORS["accent2"],
            "selectcolor": COLORS["bg"],
            "cursor": "hand2",
        }

        tk.Radiobutton(option_frame, text=" วิดีโอ + เสียง (สมบูรณ์)  แนะนำ",
                        value="both", variable=self.download_type, **rb_style
                        ).pack(anchor="w", padx=15, pady=4)
        tk.Radiobutton(option_frame, text=" วิดีโออย่างเดียว (ไม่มีเสียง)",
                        value="video_only", variable=self.download_type, **rb_style
                        ).pack(anchor="w", padx=15, pady=4)
        tk.Radiobutton(option_frame, text=" เสียงอย่างเดียว (Audio/MP3)",
                        value="audio_only", variable=self.download_type, **rb_style
                        ).pack(anchor="w", padx=15, pady=4)

        # แจ้งเตือนเรื่อง ffmpeg (ซ่อน/แสดงตามสถานะ)
        self.ffmpeg_notice = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["bg"],
            fg=COLORS["warning"],
            wraplength=480,
            justify="center",
        )
        self.ffmpeg_notice.pack(pady=(0, 4))

        # --- Output folder (secondary info, lighter weight than the option box) ---
        folder_row = tk.Frame(self.root, bg=COLORS["surface"])
        folder_row.pack(pady=(6, 10), padx=25, fill="x")

        inner = tk.Frame(folder_row, bg=COLORS["surface"])
        inner.pack(fill="x", padx=12, pady=8)

        text_col = tk.Frame(inner, bg=COLORS["surface"])
        text_col.pack(side="left", fill="x", expand=True)

        tk.Label(
            text_col,
            text="บันทึกไฟล์ไปที่",
            font=("Segoe UI", 8),
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            anchor="w",
        ).pack(anchor="w")

        self.folder_label = tk.Label(
            text_col,
            text=self.download_dir,
            font=("Consolas", 9),
            bg=COLORS["surface"],
            fg=COLORS["text"],
            anchor="w",
        )
        self.folder_label.pack(anchor="w")

        btn_col = tk.Frame(inner, bg=COLORS["surface"])
        btn_col.pack(side="right")

        self.change_folder_btn = tk.Button(
            btn_col,
            text="✏ เปลี่ยน",
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            activebackground=COLORS["card"],
            activeforeground=COLORS["text"],
            relief="solid",
            bd=1,
            highlightbackground=COLORS["border"],
            cursor="hand2",
            command=self.change_download_folder,
            padx=8,
        )
        self.change_folder_btn.pack(side="right", padx=(0, 6))

        self.open_folder_btn = tk.Button(
            btn_col,
            text="📂 เปิดโฟลเดอร์",
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["surface"],
            fg=COLORS["accent2"],
            activebackground=COLORS["card"],
            activeforeground=COLORS["accent2"],
            relief="solid",
            bd=1,
            highlightbackground=COLORS["accent2"],
            cursor="hand2",
            command=self.open_download_folder,
            padx=8,
        )
        self.open_folder_btn.pack(side="right")

        # --- Progress ---
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=COLORS["card"],
            background=COLORS["accent"],
            thickness=8,
        )

        # กรอบตายตัวสำหรับ progress bar กันไม่ให้ layout กระโดดเวลาโผล่/หาย
        self.progress_slot = tk.Frame(self.root, bg=COLORS["bg"], height=22)
        self.progress_slot.pack(pady=(5, 0), padx=25, fill="x")
        self.progress_slot.pack_propagate(False)

        self.progress = ttk.Progressbar(
            self.progress_slot,
            style="Custom.Horizontal.TProgressbar",
            mode="determinate",
            maximum=100,
            length=470,
        )

        self.status_label = tk.Label(
            self.root,
            text="พร้อมสำหรับการดาวน์โหลด",
            font=("Segoe UI", 9, "italic"),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            wraplength=480,
            justify="center",
        )
        self.status_label.pack(pady=(10, 5))

        self.download_btn = tk.Button(
            self.root,
            text="⚡ สั่งดาวน์โหลด",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["accent2"],
            fg="#11111b",
            activebackground="#b4befe",
            activeforeground="#11111b",
            relief="flat",
            cursor="hand2",
            command=self.start_download_thread,
            pady=8,
            padx=25,
        )
        self.download_btn.pack(pady=10)

    def refresh_ffmpeg_notice(self):
        if not self.ffmpeg_available:
            self.ffmpeg_notice.config(
                text="⚠ ไม่พบ ffmpeg ในเครื่อง — โหมด 'วิดีโอ+เสียง' และการแปลงเป็น MP3 อาจใช้งานไม่ได้"
            )
        else:
            self.ffmpeg_notice.config(text="")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def on_url_focus_in(self, _event=None):
        if self.showing_placeholder:
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(fg=COLORS["text"])
            self.showing_placeholder = False

    def on_url_focus_out(self, _event=None):
        if not self.url_entry.get().strip():
            self.showing_placeholder = True
            self.url_entry.config(fg=COLORS["muted_text"])
            self.url_entry.insert(0, URL_PLACEHOLDER)

    def on_url_changed(self, _event=None):
        if self.showing_placeholder:
            return
        text = self.url_entry.get().strip()
        if not text:
            self.url_entry.config(bg=COLORS["card"])
        elif looks_like_youtube_url(text):
            self.url_entry.config(bg=COLORS["card"])
        else:
            self.url_entry.config(bg="#3b2f3a")  # เตือนเบาๆ ว่าอาจไม่ใช่ลิงก์ YouTube

    def get_url_value(self) -> str:
        return "" if self.showing_placeholder else self.url_entry.get().strip()

    def paste_url(self):
        try:
            clipboard_text = self.root.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(fg=COLORS["text"])
            self.showing_placeholder = False
            self.url_entry.insert(0, clipboard_text)
            self.on_url_changed()
        except Exception:
            pass

    def open_download_folder(self):
        if not ensure_download_dir(self.download_dir):
            messagebox.showerror(
                "ผิดพลาด",
                f"ไม่สามารถสร้าง/เข้าถึงโฟลเดอร์ได้:\n{self.download_dir}\n"
                "กรุณาเลือกโฟลเดอร์อื่นด้วยปุ่ม 'เปลี่ยน'",
            )
            return
        try:
            os.startfile(self.download_dir)  # Windows only
        except Exception:
            try:
                subprocess.Popen(["explorer", self.download_dir])
            except Exception as e:
                messagebox.showerror("ผิดพลาด", f"ไม่สามารถเปิดโฟลเดอร์ได้:\n{e}")

    def start_download_thread(self):
        url = self.get_url_value()
        if not url:
            messagebox.showwarning("แจ้งเตือน", "กรุณากรอกหรือวาง URL ก่อนกดดาวน์โหลดครับ")
            return
        if not looks_like_youtube_url(url):
            proceed = messagebox.askyesno(
                "ตรวจสอบลิงก์",
                "ลิงก์นี้ดูไม่เหมือนลิงก์ YouTube ทั่วไป\nต้องการดาวน์โหลดต่อหรือไม่?",
            )
            if not proceed:
                return

        mode = self.download_type.get()

        # ตรวจสอบโฟลเดอร์ปลายทางก่อนเริ่ม (ไดรฟ์อาจถูกถอดออกระหว่างใช้งาน)
        if not drive_exists(self.download_dir) or not ensure_download_dir(self.download_dir):
            messagebox.showwarning(
                "ไม่พบโฟลเดอร์ปลายทาง",
                f"ไม่พบหรือไม่สามารถเข้าถึงโฟลเดอร์:\n{self.download_dir}\n"
                "กรุณาเลือกโฟลเดอร์ใหม่ในขั้นตอนถัดไป",
            )
            chosen = self.ask_folder_dialog(initial=os.path.expanduser("~"))
            if not chosen or not ensure_download_dir(chosen):
                return
            self.download_dir = chosen
            save_folder(chosen)
            self.folder_label.config(text=self.download_dir)

        # ตรวจสอบ ffmpeg สำหรับโหมดที่ต้องใช้
        if mode in ("both", "audio_only") and not has_ffmpeg():
            proceed = messagebox.askyesno(
                "ไม่พบ ffmpeg",
                "ไม่พบโปรแกรม ffmpeg ในเครื่อง\n"
                "โหมดนี้อาจดาวน์โหลดไม่สำเร็จ หรือได้ไฟล์ที่ไม่สมบูรณ์\n\n"
                "ต้องการดำเนินการต่อหรือไม่?",
            )
            if not proceed:
                return

        self.is_downloading = True
        self.download_btn.config(state=tk.DISABLED, bg=COLORS["border"], fg="#6c7086")
        self.paste_btn.config(state=tk.DISABLED)
        self.open_folder_btn.config(state=tk.DISABLED)
        self.change_folder_btn.config(state=tk.DISABLED)

        self.progress["value"] = 0
        self.progress.pack(fill="x", expand=True)
        self.status_label.config(text="⏳ กำลังเริ่มดาวน์โหลด...", fg=COLORS["warning"])

        threading.Thread(
            target=self.download_video,
            args=(url, mode, self.download_dir),
            daemon=True,
        ).start()

    # ------------------------------------------------------------------
    # Download logic
    # ------------------------------------------------------------------
    def progress_hook(self, d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            if total:
                pct = downloaded / total * 100
                speed = d.get("speed")
                speed_txt = f" • {speed / 1024 / 1024:.1f} MB/s" if speed else ""
                self.root.after(0, self.update_progress, pct,
                                 f"⏳ กำลังดาวน์โหลด... {pct:.0f}%{speed_txt}")
            else:
                self.root.after(0, self.update_progress, None, "⏳ กำลังดาวน์โหลด...")
        elif d.get("status") == "finished":
            self.root.after(0, self.update_progress, 100, "🔧 กำลังประมวลผลไฟล์ (แปลง/รวมไฟล์)...")

    def update_progress(self, pct, text):
        if pct is not None:
            self.progress["value"] = pct
        self.status_label.config(text=text, fg=COLORS["warning"])

    def download_video(self, url, mode, target_dir):
        try:
            if mode == "video_only":
                fmt = "bestvideo/best"
            elif mode == "audio_only":
                fmt = "bestaudio/best"
            else:  # both
                fmt = "bestvideo+bestaudio/best"

            outtmpl = os.path.join(target_dir, "%(title)s.%(ext)s")

            ydl_opts = {
                "format": fmt,
                "outtmpl": outtmpl,
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [self.progress_hook],
                "noplaylist": True,
            }

            if mode == "audio_only":
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
            elif mode == "both":
                ydl_opts["merge_output_format"] = "mp4"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.root.after(0, self.on_success, target_dir)
        except Exception as e:
            self.root.after(0, self.on_error, e)

    def on_success(self, target_dir):
        self.finish_download()
        self.status_label.config(text="✨ ดาวน์โหลดสำเร็จเรียบร้อย!", fg=COLORS["success"])
        self.progress["value"] = 100
        messagebox.showinfo("สำเร็จ!", f"ไฟล์ของคุณถูกบันทึกไว้ที่:\n{target_dir}")
        self.url_entry.delete(0, tk.END)
        self.showing_placeholder = True
        self.url_entry.config(fg=COLORS["muted_text"], bg=COLORS["card"])
        self.url_entry.insert(0, URL_PLACEHOLDER)

    def on_error(self, exc: Exception):
        self.finish_download()
        self.status_label.config(text="❌ เกิดข้อผิดพลาด!", fg=COLORS["error"])
        messagebox.showerror("ไม่สามารถดาวน์โหลดได้", friendly_error(exc))

    def finish_download(self):
        self.is_downloading = False
        self.progress.pack_forget()
        self.download_btn.config(state=tk.NORMAL, bg=COLORS["accent2"], fg="#11111b")
        self.paste_btn.config(state=tk.NORMAL)
        self.open_folder_btn.config(state=tk.NORMAL)
        self.change_folder_btn.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = PremiumYoutubeDownloader(root)
    root.mainloop()