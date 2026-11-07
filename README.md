# Tiểu Tô TTS — tool đọc text bằng giọng clone Tiểu Tô, chạy ngay trên máy của bạn

Tool dùng model **VieNeu-TTS v3 Turbo** (mã nguồn mở, Apache-2.0) chạy offline trên CPU.
Giọng **Tiểu Tô** đã được đăng ký sẵn từ file mẫu — mở tool lên là đọc được ngay,
không cần làm gì thêm. Mọi xử lý diễn ra trên máy của bạn, text không gửi đi đâu cả.

## Yêu cầu

- Windows 10/11 hoặc macOS (Apple Silicon M1/M2/M3 hoặc Intel đều được) — Linux cũng chạy với cách tương tự
- **Python 3.10 trở lên** (script cài đặt sẽ tự kiểm tra và hướng dẫn nếu chưa có)
- Lần cài đầu cần internet để tải thư viện + model (khoảng 600MB), các lần sau chạy offline
- Khoảng 2GB ổ trống

## Tải về (dễ nhất)

Vào trang [**Releases**](https://github.com/tobi1008/tieu-to-tts/releases/latest):

- **Windows**: tải `TieuToTTS-windows-x64.zip` — bản portable, **không cần cài Python**.
  Giải nén toàn bộ ra chỗ cố định (đường dẫn ngắn, ví dụ `D:\TieuToTTS`) → nhấp đúp **`Mo-Tieu-To-TTS.bat`**.
  Lần đầu tool tự tải model (~550MB), các lần sau chạy offline. Xem thêm `HUONG-DAN.txt` trong gói.
- **macOS**: tải `TieuToTTS-app.zip`, giải nén rồi làm theo phần "Cài đặt trên macOS" bên dưới.

## Cập nhật

Trong tool, mở mục **Cập nhật** ở cuối trang → **Kiểm tra cập nhật** (bản tải từ Releases còn tự kiểm tra
mỗi lần mở trang). Có bản mới thì bấm **Cài bản mới**: tool tải gói code mới, chép đè, tự khởi động lại —
đợi ~30 giây rồi F5. Model, audio đã tạo và thư viện đều giữ nguyên (thư viện chỉ cài thêm khi bản mới cần).

Mỗi lần push code lên nhánh `main`, GitHub Actions tự build bản Windows trên máy Windows thật, chạy thử
đọc 1 câu, rồi phát hành bản mới (phiên bản = ngày giờ, ví dụ `2026.11.07.1930`). Chạy tay:
tab **Actions → Release Windows → Run workflow**.

## Cài đặt trên Windows bằng Python có sẵn (chỉ làm 1 lần)

1. Giải nén thư mục này ra chỗ cố định (ví dụ Desktop hoặc `D:\TieuToTTS`), đừng chạy trong thư mục Downloads tạm.
2. Nhấp đúp **`cai-dat-windows.bat`**.
   - Nếu chưa có Python: script sẽ tự mở trang tải Python. Khi cài Python, **nhớ tích ô "Add python.exe to PATH"** ở màn hình đầu tiên, cài xong chạy lại file `.bat` này.
   - Nếu Windows hiện cảnh báo SmartScreen: bấm **More info → Run anyway** (đây là file script thường, không phải file lạ).
   - Script sẽ tự: tạo môi trường riêng → cài VieNeu → tải model → đăng ký giọng Tiểu Tô → đọc thử 1 câu và **in ra tốc độ thật trên máy của bạn**.
3. Nghe thử câu mẫu ở `outputs\mau-thu.wav`.
4. Từ lần sau: nhấp đúp **`mo-tool-windows.bat`** để mở tool (trình duyệt mở `http://127.0.0.1:7860`).
   Đọc file kịch bản dài: mở CMD/PowerShell trong thư mục này, chạy `.venv\Scripts\python.exe doc_file.py kich-ban.txt`

## Cài đặt trên macOS (chỉ làm 1 lần)

1. Giải nén thư mục này ra chỗ nào cố định (ví dụ Desktop hoặc Documents), đừng chạy trong thư mục Downloads tạm.
2. Nhấp đúp **`cai-dat.command`**.
   - Nếu macOS chặn vì "không rõ nhà phát triển": chuột phải vào file → **Open** → **Open**.
   - Script sẽ tự: tạo môi trường riêng → cài VieNeu → tải model → đăng ký giọng Tiểu Tô → đọc thử 1 câu và **in ra tốc độ thật trên máy của bạn** (máy bạn tạo 30 phút audio mất khoảng bao lâu).
3. Nghe thử câu mẫu ở `outputs/mau-thu.wav`.

## Dùng hằng ngày

### Cách 1: giao diện web (đọc đoạn ngắn/trung bình)

Nhấp đúp **`mo-tool.command`** → trình duyệt tự mở `http://127.0.0.1:7860` →
dán text → bấm **Đọc** → nghe và tải file wav về (file cũng lưu trong `outputs/`).
Giữ cửa sổ Terminal mở khi dùng; đóng cửa sổ là tắt tool.

### Cách 2: đọc file kịch bản dài 30–60 phút (Terminal)

```bash
cd đường-dẫn-tới-thư-mục-này
source .venv/bin/activate
python doc_file.py kich-ban.txt
```

- File kịch bản là file `.txt` thuần (UTF-8), ngắt đoạn văn bằng dòng trống.
- Tool tự cắt nhỏ, đọc từng đoạn và **lưu từng đoạn ngay** vào thư mục `<tên-file>_doan/`.
  Bị tắt máy/ngắt giữa chừng thì chạy lại đúng lệnh cũ — nó đọc tiếp từ đoạn dở, không đọc lại từ đầu.
- Xong sẽ có 1 file `.wav` ghép hoàn chỉnh (và `.mp3` nếu máy có sẵn ffmpeg —
  cài bằng `brew install ffmpeg` nếu muốn có mp3).
- Muốn đổi giọng có sẵn của VieNeu: thêm `--voice "Tên Giọng"` (xem danh sách giọng trong giao diện web).

## Tốc độ tham khảo

- Trên máy chủ yếu (4 nhân CPU, không GPU): hệ số RTF khoảng **1,5** ở chế độ chuẩn —
  tức 30 phút audio cần ~45 phút tạo. CPU Apple Silicon thường mạnh hơn ở tác vụ này,
  con số thật trên máy bạn sẽ hiện ngay ở bước cài đặt (dòng "Máy của bạn tạo 30 phút audio...").
- Muốn nhanh hơn nữa thì giới hạn nằm ở CPU — bản trên máy chủ dùng GPU sẽ nhanh hơn rất nhiều,
  nhưng bản local này được cái chủ động: mở lên là đọc, không phụ thuộc ai.

## Cấu trúc thư mục

- `app.py` — giao diện web · `doc_file.py` — đọc file dài · `core.py` — nạp model + giọng Tiểu Tô · `capnhat.py` — kiểm tra/cài bản mới
- `pack/` + `.github/workflows/release.yml` — đóng gói bản Windows portable và phát hành
- `assets/` — file mẫu giọng Tiểu Tô (đừng xoá, tool cần nó để đăng ký giọng mỗi lần mở)
- `models/` — model đã tải về dạng file thật (tool tự tạo lúc cài; xoá đi thì lần mở sau sẽ tải lại)
- `outputs/` — các file audio tạo ra từ giao diện web

## Lỗi thường gặp

- **"không tìm thấy Python 3.10+"**: cài Python 3.12 từ python.org rồi chạy lại `cai-dat.command`.
- **Tool mở lên nhưng báo lỗi model/ONNX**: xoá thư mục `models/` rồi chạy lại `cai-dat.command` để tải lại sạch.
- **Cổng 7860 bận**: đang có bản tool khác chạy — đóng cửa sổ Terminal của bản đó trước.
