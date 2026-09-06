# 🎬 YouTube Downloader Studio

โปรแกรมดาวน์โหลดวิดีโอ/เสียงจาก YouTube แบบ GUI ใช้งานง่าย ธีมมืด สร้างด้วย Python (`tkinter` + [`yt-dlp`](https://github.com/yt-dlp/yt-dlp))

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ ฟีเจอร์

- 🎥 ดาวน์โหลดวิดีโอ + เสียง (ไฟล์สมบูรณ์)
- 🎬 ดาวน์โหลดวิดีโออย่างเดียว (ไม่มีเสียง)
- 🎵 ดาวน์โหลดเสียงอย่างเดียว แปลงเป็น MP3 อัตโนมัติ
- 📋 วางลิงก์จากคลิปบอร์ดได้ในคลิกเดียว
- ✅ ตรวจสอบลิงก์แบบเรียลไทม์ พร้อมเตือนถ้าไม่ใช่ลิงก์ YouTube
- 📊 แสดง progress bar และความเร็วดาวน์โหลดจริงระหว่างโหลด
- 📂 บันทึกไฟล์ลงโฟลเดอร์เฉพาะอัตโนมัติ พร้อมปุ่มเปิดโฟลเดอร์ปลายทาง
- ⚠️ ตรวจสอบ ffmpeg ในเครื่องก่อนดาวน์โหลด และแจ้งเตือนหากไม่พบ
- 💬 ข้อความแจ้งข้อผิดพลาดเป็นภาษาไทย เข้าใจง่าย ไม่ใช่ raw error

## 📸 หน้าตาโปรแกรม

โปรแกรมมาพร้อมธีมมืดสไตล์ Catppuccin ใช้งานง่าย เลือกประเภทไฟล์ด้วย radio button และดูสถานะการดาวน์โหลดแบบเรียลไทม์

## 🔧 ความต้องการของระบบ

| รายการ | รายละเอียด |
|---|---|
| ระบบปฏิบัติการ | Windows 10/11 |
| Python | 3.8 ขึ้นไป (สำหรับรันจาก source) |
| ffmpeg | จำเป็นสำหรับโหมด "วิดีโอ+เสียง" และ "แปลงเป็น MP3" |

## 🚀 การติดตั้งและใช้งาน

### วิธีที่ 1: ใช้ไฟล์ .exe (ง่ายที่สุด)

1. ไปที่แท็บ [Releases](../../releases) ของ repo นี้
2. ดาวน์โหลด `YouTubeDownloader.exe` เวอร์ชันล่าสุด
3. ดับเบิลคลิกเพื่อเปิดใช้งานได้ทันที (ไม่ต้องติดตั้ง Python)

> ⚠️ Windows Defender หรือแอนตี้ไวรัสบางตัวอาจแจ้งเตือนเนื่องจากเป็น false positive ที่พบได้บ่อยกับโปรแกรมที่ build ด้วย PyInstaller หากกังวลสามารถตรวจสอบซอร์สโค้ดในไฟล์ `main.py` ได้โดยตรง

### วิธีที่ 2: รันจาก Source Code

```bash
# โคลนโปรเจกต์
git clone https://github.com/bosscoolkid/youtube-downloader.git
cd youtube-downloader

# ติดตั้งไลบรารีที่จำเป็น
pip install yt-dlp

# รันโปรแกรม
python main.py
```

### 🎞️ ติดตั้ง ffmpeg (จำเป็นสำหรับบางโหมด)

1. ดาวน์โหลด ffmpeg build สำหรับ Windows จาก [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) หรือ [ffmpeg.org](https://ffmpeg.org/download.html)
2. แตกไฟล์ไว้ เช่น `C:\ffmpeg`
3. เพิ่มโฟลเดอร์ `C:\ffmpeg\bin` เข้า System PATH
4. เปิด terminal ใหม่แล้วพิมพ์ `ffmpeg -version` เพื่อยืนยันว่าติดตั้งสำเร็จ

## 📁 ตำแหน่งไฟล์ที่ดาวน์โหลด

ไฟล์ทั้งหมดจะถูกบันทึกไว้ที่:

```
D:\YouTube Downloads
```

โปรแกรมจะสร้างโฟลเดอร์นี้ให้อัตโนมัติหากยังไม่มี

## 🛠️ Build เป็น .exe เอง

```bash
pip install pyinstaller
python -m PyInstaller --onefile --noconsole --name "YouTubeDownloader" --icon=icon.ico main.py
```

ไฟล์ผลลัพธ์จะอยู่ที่ `dist\YouTubeDownloader.exe`

## ⚠️ ข้อจำกัดและคำเตือน

- โปรแกรมนี้ใช้สำหรับดาวน์โหลดวิดีโอเพื่อการใช้งานส่วนตัวเท่านั้น
- ผู้ใช้ต้องรับผิดชอบต่อการปฏิบัติตามข้อกำหนดการใช้งานของ YouTube และกฎหมายลิขสิทธิ์ในประเทศของตนเอง
- โปรแกรมนี้ไม่มีความเกี่ยวข้องหรือได้รับการรับรองจาก YouTube หรือ Google

## 📄 License

โปรเจกต์นี้เผยแพร่ภายใต้ [MIT License](LICENSE)

## 🙏 เครดิต

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — เอนจินหลักสำหรับดาวน์โหลดวิดีโอ
- [PyInstaller](https://pyinstaller.org/) — ใช้แปลงโปรแกรม Python เป็นไฟล์ .exe
