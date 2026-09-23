# Đánh giá HTTPS, TLS và HSTS trên các website chính phủ Việt Nam

## 1. Giới thiệu
Repository này chứa mã nguồn và dữ liệu phục vụ phần đánh giá HTTPS, TLS và HSTS trong nghiên cứu về mức độ sẵn sàng và an toàn của các website thuộc hệ thống chính phủ Việt Nam.
Nghiên cứu thực hiện phép đo từ bên ngoài đối với 85 website/domain thuộc các nhóm cơ quan và hệ thống chính phủ được lựa chọn trong mẫu nghiên cứu.
Các phép đo tập trung vào:
* Khả năng thiết lập kết nối HTTPS.
* Phiên bản TLS 1.0, TLS 1.1, TLS 1.2 và TLS 1.3.
* Cipher được thương lượng trong các phiên TLS thành công.
* Thông tin chứng thư số TLS/SSL.
* HTTP Strict Transport Security (HSTS).
* Giá trị max-age.
* Directive includeSubDomains.
* Directive preload.

Phương pháp đo chỉ sử dụng các kết nối từ bên ngoài và không yêu cầu quyền truy cập nội bộ vào hệ thống được khảo sát.

## 2. Mục tiêu
Repository được xây dựng nhằm:
* Chuẩn hóa danh sách website/domain cần khảo sát.
* Tự động hóa việc kiểm tra HTTPS, TLS và HSTS.
* Thu thập dữ liệu nhất quán trên toàn bộ mẫu 85 website.
* Lưu kết quả dưới dạng Excel để phục vụ phân tích thống kê.
* Hỗ trợ khả năng tái lập phép đo.
* Giảm việc kiểm tra thủ công từng website.
* Cung cấp dữ liệu đầu vào cho các bảng kết quả và phần thảo luận của nghiên cứu.

## 3. Phạm vi nghiên cứu
### Đối tượng
Mẫu nghiên cứu gồm 85 URL/domain thuộc các website chính phủ và hệ thống dịch vụ công được lựa chọn trong nghiên cứu.

### Phạm vi kỹ thuật
Các phép đo tập trung vào những thông tin có thể quan sát từ bên ngoài:

| Nhóm | Nội dung |
| :--- | :--- |
| **HTTPS** | Khả năng thiết lập kết nối HTTP |
| **TLS** | TLS 1.0, TLS 1.1, TLS 1.2, TLS 1.3 |
| **Cipher** | Cipher được thương lượng trong phiên TLS |
| **Certificate** | Subject, Issuer, thời hạn, Serial Number và trạng thái xác thực |
| **HSTS** | Sự tồn tại của Strict-Transport-Security |
| **HSTS max-age** | Giá trị thời gian được khai báo |
| **HSTS includeSubDomains** | Directive áp dụng cho subdomain |
| **HSTS preload** | Directive preload được khai báo trong header |

### Ngoài phạm vi
Repository này không thực hiện:
* Đăng nhập vào hệ thống.
* Kiểm tra tài khoản người dùng.
* Khai thác lỗ hổng.
* Brute force.
* SQL injection.
* XSS exploitation.
* DoS/DDoS.
* Tấn công hoặc thay đổi dữ liệu trên hệ thống mục tiêu.
* Truy cập vào các thành phần nội bộ không công khai.

Các phép đo được thực hiện theo hướng non-intrusive/external measurement.

## 4. Cấu trúc thư mục
Cấu trúc project:

```text
HTTPS_TLS_HSTS/
│
├── data/
│   └── input_urls.xlsx
│
├── scripts/
│   ├── 01_prepare_input.py
│   ├── 02_ssl_labs.py
│   └── 03_python_tls_hsts.py
│
├── results/
│   ├── URL_Input.xlsx
│   └── Python_TLS_HSTS_Result.xlsx
│
└── README.md
```

## 5. Kết quả đầu ra

File `Python_TLS_HSTS_Result.xlsx` gồm 3 sheet:

| Sheet | Nội dung chính |
|-------|----------------|
| **TLS_Result** | Kết quả hỗ trợ TLS 1.0 / 1.1 / 1.2 / 1.3, cipher được thương lượng, lỗi kết nối |
| **HSTS_Result** | Trạng thái HTTPS, HSTS, max-age, includeSubDomains, preload |
| **Certificate_Result** | Thông tin chứng chỉ (Subject, Issuer, Valid From/To, Serial Number…) |

### Tóm tắt số liệu chính (85 website)

| Chỉ số | Có | Không | Không xác định | Tỷ lệ Có |
|--------|----|-------|----------------|----------|
| HTTPS | 75 | 0 | 10 | 88,24% |
| TLS 1.0 | 20 | 65 | 0 | 23,53% |
| TLS 1.1 | 23 | 62 | 0 | 27,06% |
| TLS 1.2 | 79 | 6 | 0 | 92,94% |
| TLS 1.3 | 51 | 34 | 0 | 60,00% |
| HSTS | 46 | 29 | 10 | 54,12% |
| includeSubDomains (trong 46) | 33 | – | – | 71,74% |
| preload (trong 46) | 25 | – | – | 54,35% |
| Certificate xác thực thành công | 67 | 14 | 4 | 78,82% |

---

## 6. Yêu cầu môi trường

### Hệ điều hành

Project có thể chạy trên **Windows** với Python 3.  
Môi trường phát triển được sử dụng: **Python 3.12.2**.

### Thư viện Python

- `pandas`
- `requests`
- `openpyxl`

Các module thuộc **Python Standard Library** (không cần cài đặt):  
`socket`, `ssl`, `time`, `pathlib`, `urllib.parse`.

---

## 7. Cài đặt môi trường

Kiểm tra phiên bản Python:

```bash
py --version
```

Kiểm tra các thư viện:

```bash
py -c "import pandas, requests, openpyxl, ssl; print('OK')"
```

Nếu hiển thị `OK` thì môi trường đã sẵn sàng.  
Nếu thiếu thư viện, cài đặt bằng:

```bash
py -m pip install pandas requests openpyxl
```

Hoặc sử dụng file `requirements.txt`:

```bash
py -m pip install -r requirements.txt
```

---

## 8. Chuẩn bị dữ liệu đầu vào

File đầu vào: `data/input_urls.xlsx`

Các trường thông tin chính:

| Cột | Mô tả |
|-----|-------|
| ID | Mã định danh website |
| Nhóm | Nhóm website trong mẫu |
| Cơ quan/Hệ thống | Cơ quan hoặc hệ thống tương ứng |
| URL | URL đầu vào |
| Domain | Domain được trích xuất để đo |

> **Lưu ý:** Không nên sửa trực tiếp file kết quả để thay đổi dữ liệu đo.

---

## 9. Quy trình thực hiện

```text
input_urls.xlsx
       │
       ▼
01_prepare_input.py
       │
       ▼
URL_Input.xlsx
       │
       ├──────────────► 02_ssl_labs.py   (tùy chọn)
       │
       ▼
03_python_tls_hsts.py
       │
       ▼
Python_TLS_HSTS_Result.xlsx
```

### Các bước chạy

1. Chuẩn hóa dữ liệu đầu vào:

```bash
py scripts/01_prepare_input.py
```

2. (Tùy chọn) Chạy đo bổ sung qua SSL Labs:

```bash
py scripts/02_ssl_labs.py
```

3. Thực hiện đo TLS + HSTS + Certificate:

```bash
py scripts/03_python_tls_hsts.py
```

Kết quả sẽ được lưu tại `results/Python_TLS_HSTS_Result.xlsx`.

---

## 10. Giải thích kết quả

- **Có**: Kết nối / header / phiên bản TLS được thiết lập hoặc quan sát thành công.
- **Không**: Kết nối thất bại hoặc không quan sát được header/phiên bản tương ứng trong phép đo.
- **Không xác định**: Không thu thập được dữ liệu do timeout, lỗi DNS, lỗi xác thực chứng chỉ hoặc máy chủ đóng kết nối.

> Kết quả “Không” **không đồng nghĩa** với việc máy chủ tuyệt đối không hỗ trợ phiên bản TLS đó trong mọi điều kiện.

---

## 11. Lưu ý quan trọng

- Phép đo chỉ ghi nhận **cipher được thương lượng**, không phải toàn bộ danh sách cipher suite mà máy chủ hỗ trợ.
- Directive `preload` trong header HSTS **không** đồng nghĩa với việc website đã có trong danh sách HSTS Preload chính thức.
- Một số website có thể trả về nhiều giá trị `max-age` trong cùng header (cấu hình không nhất quán).
- Kết quả phụ thuộc vào thời điểm đo và môi trường mạng.

---

## 12. Tác giả & mục đích sử dụng

Project được thực hiện phục vụ báo cáo nghiên cứu về hiện trạng triển khai HTTPS, TLS và HSTS trên các website cơ quan nhà nước Việt Nam.

Chỉ sử dụng cho mục đích nghiên cứu và đánh giá cấu hình bảo mật từ phía bên ngoài.
