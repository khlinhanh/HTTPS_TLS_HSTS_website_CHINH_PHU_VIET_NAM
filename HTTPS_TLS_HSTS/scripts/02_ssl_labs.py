import pandas as pd
import requests
import time
from pathlib import Path

# ============================================================
# CAU HINH
# ============================================================

INPUT = Path("results/URL_Input.xlsx")
OUTPUT = Path("results/SSL_Labs_Result.xlsx")

API_URL = "https://api.ssllabs.com/api/v4/analyze"

# Thoi gian toi da cho 1 domain
MAX_WAIT_SECONDS = 180

# Thoi gian nghi giua cac domain
SLEEP_BETWEEN_HOSTS = 5

# ============================================================
# NHAP EMAIL
# ============================================================

EMAIL = input(
    "Nhap email da dang ky SSL Labs API v4: "
).strip()

if not EMAIL:
    print("ERROR: Chua nhap email.")
    raise SystemExit(1)

HEADERS = {
    "email": EMAIL
}

# ============================================================
# DOC INPUT
# ============================================================

df = pd.read_excel(INPUT)

required_columns = [
    "ID",
    "Nhóm",
    "Cơ quan/Hệ thống",
    "URL",
    "Domain"
]

missing = [c for c in required_columns if c not in df.columns]

if missing:
    print("THIEU COT:", missing)
    raise SystemExit(1)


# ============================================================
# GOI API
# ============================================================

def call_ssl_labs(domain):

    print()
    print("=" * 70)
    print(f"DOMAIN: {domain}")
    print("=" * 70)

    start_time = time.time()

    params = {
        "host": domain,
        "all": "done",
        "ignoreMismatch": "on"
    }

    # --------------------------------------------------------
    # REQUEST DAU TIEN
    # --------------------------------------------------------

    try:

        response = requests.get(
            API_URL,
            headers=HEADERS,
            params=params,
            timeout=30
        )

    except Exception as e:

        return None, f"Loi ket noi API: {e}"

    if response.status_code != 200:

        return None, (
            f"HTTP {response.status_code}: "
            f"{response.text[:300]}"
        )

    try:

        data = response.json()

    except Exception:

        return None, "API khong tra ve JSON"

    # --------------------------------------------------------
    # API ERROR
    # --------------------------------------------------------

    if "errors" in data:

        return None, str(data["errors"])

    # --------------------------------------------------------
    # POLL DEN KHI READY
    # --------------------------------------------------------

    while True:

        # Luon kiem tra thoi gian ngay dau vong lap
        elapsed = int(
            time.time() - start_time
        )

        status = str(
            data.get(
                "status",
                ""
            )
        ).upper()

        print(
            f"SSL Labs status: {status} "
            f"(da cho {elapsed}s)"
        )

        # ----------------------------------------------------
        # READY
        # ----------------------------------------------------

        if status == "READY":

            print(
                "Assessment da hoan thanh."
            )

            return data, ""

        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        if status == "ERROR":

            return data, data.get(
                "statusMessage",
                "SSL Labs ERROR"
            )

        # ----------------------------------------------------
        # TIMEOUT
        # ----------------------------------------------------

        if elapsed >= MAX_WAIT_SECONDS:

            print(
                f"TIMEOUT: SSL Labs chua hoan thanh sau "
                f"{MAX_WAIT_SECONDS} giay."
            )

            return data, "Timeout SSL Labs"

        # ----------------------------------------------------
        # TINH THOI GIAN CON LAI
        # ----------------------------------------------------

        remaining = (
            MAX_WAIT_SECONDS - elapsed
        )

        # Khong sleep qua thoi gian con lai
        sleep_seconds = min(
            10,
            remaining
        )

        if sleep_seconds > 0:

            time.sleep(
                sleep_seconds
            )

        # ----------------------------------------------------
        # KIEM TRA TIMEOUT SAU KHI SLEEP
        # ----------------------------------------------------

        elapsed = int(
            time.time() - start_time
        )

        if elapsed >= MAX_WAIT_SECONDS:

            print(
                f"TIMEOUT: SSL Labs chua hoan thanh sau "
                f"{MAX_WAIT_SECONDS} giay."
            )

            return data, "Timeout SSL Labs"

        # ----------------------------------------------------
        # POLL LAI
        # ----------------------------------------------------

        try:

            remaining = (
                MAX_WAIT_SECONDS - elapsed
            )

            response = requests.get(
                API_URL,
                headers=HEADERS,
                params={
                    "host": domain,
                    "all": "done",
                    "ignoreMismatch": "on"
                },
                timeout=min(
                    30,
                    remaining
                )
            )

        except Exception as e:

            print(
                f"Loi khi poll API: {e}"
            )

            # Kiem tra timeout ngay sau loi ket noi
            elapsed = int(
                time.time() - start_time
            )

            if elapsed >= MAX_WAIT_SECONDS:

                print(
                    f"TIMEOUT: SSL Labs chua hoan thanh sau "
                    f"{MAX_WAIT_SECONDS} giay."
                )

                return data, "Timeout SSL Labs"

            # Chua timeout -> tiep tuc poll
            continue

        # ----------------------------------------------------
        # RATE LIMIT
        # ----------------------------------------------------

        if response.status_code == 429:

            print(
                "HTTP 429 - Rate limit. Thu lai..."
            )

            # Khong sleep 30 giay.
            # Vong lap tiep theo se kiem tra timeout.
            continue

        # ----------------------------------------------------
        # SERVER BUSY
        # ----------------------------------------------------

        if response.status_code == 529:

            print(
                "HTTP 529 - SSL Labs dang qua tai. "
                "Thu lai..."
            )

            # Khong sleep 60 giay.
            # Vong lap tiep theo se kiem tra timeout.
            continue

        # ----------------------------------------------------
        # HTTP KHAC
        # ----------------------------------------------------

        if response.status_code != 200:

            print(
                f"HTTP {response.status_code}. "
                "Thu lai..."
            )

            continue

        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        try:

            data = response.json()

        except Exception:

            print(
                "JSON khong hop le. Thu lai..."
            )

            continue


# ============================================================
# TIM ENDPOINT READY
# ============================================================

def get_ready_endpoints(data):

    if not data:
        return []

    endpoints = data.get(
        "endpoints",
        []
    )

    ready = []

    for ep in endpoints:

        status_message = str(
            ep.get(
                "statusMessage",
                ""
            )
        ).strip().lower()

        details = ep.get(
            "details"
        )

        # ----------------------------------------------------
        # CHI LAY ENDPOINT THAT SU THAT READY
        # ----------------------------------------------------

        if (
            status_message == "ready"
            and isinstance(
                details,
                dict
            )
        ):

            ready.append(ep)

    return ready


# ============================================================
# TLS
# ============================================================

def extract_tls(endpoints):

    result = {
        "TLS 1.0": "Không xác định",
        "TLS 1.1": "Không xác định",
        "TLS 1.2": "Không xác định",
        "TLS 1.3": "Không xác định"
    }

    if not endpoints:
        return result

    # --------------------------------------------------------
    # Mapping Protocol ID cua SSL Labs
    # --------------------------------------------------------

    protocol_mapping = {
        769: "TLS 1.0",
        770: "TLS 1.1",
        771: "TLS 1.2",
        772: "TLS 1.3"
    }

    found_protocols = set()

    has_protocol_data = False

    # --------------------------------------------------------
    # DOC details.protocols
    # --------------------------------------------------------

    for ep in endpoints:

        details = ep.get(
            "details",
            {}
        )

        protocols = details.get(
            "protocols",
            []
        )

        if isinstance(
            protocols,
            list
        ):

            for protocol in protocols:

                if not isinstance(
                    protocol,
                    dict
                ):
                    continue

                protocol_id = protocol.get(
                    "id"
                )

                # ID co the la int hoac string
                try:

                    protocol_id = int(
                        protocol_id
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                if protocol_id in protocol_mapping:

                    has_protocol_data = True

                    found_protocols.add(
                        protocol_mapping[
                            protocol_id
                        ]
                    )

    # --------------------------------------------------------
    # FALLBACK:
    # Neu protocols[] khong co, doc tu suites[]
    # --------------------------------------------------------

    if not has_protocol_data:

        for ep in endpoints:

            details = ep.get(
                "details",
                {}
            )

            suites = details.get(
                "suites",
                []
            )

            if not isinstance(
                suites,
                list
            ):
                continue

            for suite_group in suites:

                if not isinstance(
                    suite_group,
                    dict
                ):
                    continue

                protocol_id = suite_group.get(
                    "protocol"
                )

                try:

                    protocol_id = int(
                        protocol_id
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                if protocol_id in protocol_mapping:

                    has_protocol_data = True

                    found_protocols.add(
                        protocol_mapping[
                            protocol_id
                        ]
                    )

    # --------------------------------------------------------
    # KHONG CO DU LIEU
    # --------------------------------------------------------

    if not has_protocol_data:

        return result

    # --------------------------------------------------------
    # CO DU LIEU -> CO / KHONG
    # --------------------------------------------------------

    for version in result:

        if version in found_protocols:

            result[version] = "Có"

        else:

            result[version] = "Không"

    return result


# ============================================================
# CIPHER
# ============================================================

def extract_ciphers(endpoints):

    rows = []

    for ep in endpoints:

        ip = ep.get(
            "ipAddress",
            ""
        )

        details = ep.get(
            "details",
            {}
        )

        suites = details.get(
            "suites",
            []
        )

        if not isinstance(
            suites,
            list
        ):
            continue

        for suite_group in suites:

            if not isinstance(
                suite_group,
                dict
            ):
                continue

            protocol = suite_group.get(
                "protocol",
                ""
            )

            list_suites = suite_group.get(
                "list",
                []
            )

            if not isinstance(
                list_suites,
                list
            ):
                continue

            for cipher in list_suites:

                if not isinstance(
                    cipher,
                    dict
                ):
                    continue

                rows.append({
                    "IP": ip,
                    "Protocol": protocol,
                    "Cipher": cipher.get(
                        "name",
                        ""
                    ),
                    "Strength": cipher.get(
                        "strength",
                        cipher.get(
                            "cipherStrength",
                            ""
                        )
                    )
                })

    return rows


# ============================================================
# CERTIFICATE
# ============================================================

def extract_certificates(data, endpoints):

    rows = []

    if not data:
        return rows

    # --------------------------------------------------------
    # SSL Labs API v4:
    # certs[] nam o cap HOST
    # khong nam trong details
    # --------------------------------------------------------

    certs = data.get(
        "certs",
        []
    )

    if not isinstance(
        certs,
        list
    ):
        return rows

    endpoint_ips = []

    for ep in endpoints:

        ip = ep.get(
            "ipAddress",
            ""
        )

        if ip:

            endpoint_ips.append(
                ip
            )

    # --------------------------------------------------------
    # DOC CERTIFICATE
    # --------------------------------------------------------

    for cert in certs:

        if not isinstance(
            cert,
            dict
        ):
            continue

        rows.append({
            "IP": ", ".join(
                endpoint_ips
            ),
            "Subject": cert.get(
                "subject",
                ""
            ),
            "Issuer": cert.get(
                "issuerLabel",
                cert.get(
                    "issuer",
                    ""
                )
            ),
            "Valid From": cert.get(
                "notBefore",
                ""
            ),
            "Valid To": cert.get(
                "notAfter",
                ""
            ),
            "Key Size": cert.get(
                "keySize",
                ""
            ),
            "SHA256": cert.get(
                "sha256Hash",
                cert.get(
                    "sha256",
                    ""
                )
            )
        })

    return rows


# ============================================================
# HSTS
# ============================================================

def extract_hsts(endpoints):

    rows = []

    for ep in endpoints:

        ip = ep.get(
            "ipAddress",
            ""
        )

        details = ep.get(
            "details",
            {}
        )

        hsts = details.get(
            "hstsPolicy"
        )

        # ----------------------------------------------------
        # HSTS CO THONG TIN
        # ----------------------------------------------------

        if isinstance(
            hsts,
            dict
        ):

            status = str(
                hsts.get(
                    "status",
                    ""
                )
            ).lower()

            # present = header ton tai
            # invalid/disabled/absent = khong nen ghi don gian la Co
            if status == "present":

                hsts_value = "Có"

            elif status == "absent":

                hsts_value = "Không"

            else:

                hsts_value = "Không xác định"

            rows.append({
                "IP": ip,
                "HSTS": hsts_value,
                "maxAge": hsts.get(
                    "maxAge",
                    ""
                ),
                "includeSubDomains": hsts.get(
                    "includeSubDomains",
                    ""
                ),
                "preload": hsts.get(
                    "preload",
                    ""
                ),
                "Status": hsts.get(
                    "status",
                    ""
                ),
                "Header": hsts.get(
                    "header",
                    ""
                )
            })

        # ----------------------------------------------------
        # KHONG CO HSTS POLICY
        # ----------------------------------------------------

        else:

            rows.append({
                "IP": ip,
                "HSTS": "Không xác định",
                "maxAge": "",
                "includeSubDomains": "",
                "preload": "",
                "Status": "",
                "Header": ""
            })

    return rows


# ============================================================
# HSTS PRELOAD
# ============================================================

def extract_hsts_preloads(endpoints):

    rows = []

    for ep in endpoints:

        ip = ep.get(
            "ipAddress",
            ""
        )

        details = ep.get(
            "details",
            {}
        )

        preloads = details.get(
            "hstsPreloads",
            []
        )

        if not isinstance(
            preloads,
            list
        ):
            continue

        for preload in preloads:

            if not isinstance(
                preload,
                dict
            ):
                continue

            rows.append({
                "IP": ip,
                "Preload Data": str(
                    preload
                )
            })

    return rows


# ============================================================
# BIEN LUU KET QUA
# ============================================================

summary_rows = []
tls_rows = []
cipher_rows = []
cert_rows = []
hsts_rows = []
preload_rows = []


# ============================================================
# CHAY CAC DOMAIN
# ============================================================

for index, row in df.iterrows():

    number = index + 1

    domain = str(
        row["Domain"]
    ).strip()

    print()
    print(
        f"[{number}/{len(df)}] {domain}"
    )

    # --------------------------------------------------------
    # DOMAIN RONG
    # --------------------------------------------------------

    if not domain:

        summary_rows.append({
            "ID": row["ID"],
            "Domain": domain,
            "SSL Labs Status": "Không xác định",
            "Endpoint": "Không xác định",
            "TLS Data": "Không xác định",
            "Certificate": "Không xác định",
            "HSTS": "Không xác định",
            "Error": "Domain rong"
        })

        tls_rows.append({
            "ID": row["ID"],
            "Domain": domain,
            "TLS 1.0": "Không xác định",
            "TLS 1.1": "Không xác định",
            "TLS 1.2": "Không xác định",
            "TLS 1.3": "Không xác định"
        })

        continue

    # --------------------------------------------------------
    # SSL LABS
    # --------------------------------------------------------

    data, error = call_ssl_labs(
        domain
    )

    # --------------------------------------------------------
    # ENDPOINT
    # --------------------------------------------------------

    endpoints = get_ready_endpoints(
        data
    )

    # --------------------------------------------------------
    # TLS
    # --------------------------------------------------------

    tls = extract_tls(
        endpoints
    )

    tls_rows.append({
        "ID": row["ID"],
        "Domain": domain,
        "TLS 1.0": tls["TLS 1.0"],
        "TLS 1.1": tls["TLS 1.1"],
        "TLS 1.2": tls["TLS 1.2"],
        "TLS 1.3": tls["TLS 1.3"]
    })

    # --------------------------------------------------------
    # CIPHER
    # --------------------------------------------------------

    ciphers = extract_ciphers(
        endpoints
    )

    for c in ciphers:

        cipher_rows.append({
            "ID": row["ID"],
            "Domain": domain,
            **c
        })

    # --------------------------------------------------------
    # CERTIFICATE
    # --------------------------------------------------------

    certs = extract_certificates(
        data,
        endpoints
    )

    for c in certs:

        cert_rows.append({
            "ID": row["ID"],
            "Domain": domain,
            **c
        })

    # --------------------------------------------------------
    # HSTS
    # --------------------------------------------------------

    hsts = extract_hsts(
        endpoints
    )

    for h in hsts:

        hsts_rows.append({
            "ID": row["ID"],
            "Domain": domain,
            **h
        })

    # --------------------------------------------------------
    # HSTS PRELOAD
    # --------------------------------------------------------

    preloads = extract_hsts_preloads(
        endpoints
    )

    for p in preloads:

        preload_rows.append({
            "ID": row["ID"],
            "Domain": domain,
            **p
        })

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    ssl_status = (
        data.get(
            "status",
            "Không xác định"
        )
        if data
        else "Không xác định"
    )

    # --------------------------------------------------------
    # ENDPOINT STATUS
    # --------------------------------------------------------

    if endpoints:

        endpoint_status = (
            "Có endpoint kết nối được"
        )

    else:

        endpoint_status = (
            "Không có endpoint kết nối được"
        )

    # --------------------------------------------------------
    # TLS STATUS
    # --------------------------------------------------------

    if endpoints:

        tls_status = (
            "Có dữ liệu TLS"
        )

    else:

        tls_status = (
            "Không có endpoint có dữ liệu TLS"
        )

    # --------------------------------------------------------
    # CERTIFICATE STATUS
    # --------------------------------------------------------

    if certs:

        cert_status = (
            "Có dữ liệu Certificate"
        )

    else:

        cert_status = (
            "Không có dữ liệu Certificate"
        )

    # --------------------------------------------------------
    # HSTS STATUS
    # --------------------------------------------------------

    if hsts:

        hsts_status = (
            "Có dữ liệu HSTS"
        )

    else:

        hsts_status = (
            "Không có endpoint có dữ liệu HSTS"
        )

    # --------------------------------------------------------
    # ERROR
    # --------------------------------------------------------

    # Neu READY thi khong ghi Timeout
    if ssl_status == "READY":

        final_error = ""

    else:

        final_error = error

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    summary_rows.append({
        "ID": row["ID"],
        "Domain": domain,
        "SSL Labs Status": ssl_status,
        "Endpoint": endpoint_status,
        "TLS Data": tls_status,
        "Certificate": cert_status,
        "HSTS": hsts_status,
        "Error": final_error
    })

    # ========================================================
    # LUU EXCEL SAU MOI DOMAIN
    # ========================================================

    with pd.ExcelWriter(
        OUTPUT,
        engine="openpyxl"
    ) as writer:

        pd.DataFrame(
            tls_rows
        ).to_excel(
            writer,
            sheet_name="TLS_Result",
            index=False
        )

        pd.DataFrame(
            cipher_rows
        ).to_excel(
            writer,
            sheet_name="Cipher_Result",
            index=False
        )

        pd.DataFrame(
            cert_rows
        ).to_excel(
            writer,
            sheet_name="Certificate_Result",
            index=False
        )

        pd.DataFrame(
            hsts_rows
        ).to_excel(
            writer,
            sheet_name="HSTS_Result",
            index=False
        )

        pd.DataFrame(
            preload_rows
        ).to_excel(
            writer,
            sheet_name="HSTS_Preload",
            index=False
        )

        pd.DataFrame(
            summary_rows
        ).to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

    print(
        "Da luu ket qua vao Excel."
    )

    # --------------------------------------------------------
    # NGHI GIUA CAC DOMAIN
    # --------------------------------------------------------

    if number < len(df):

        print(
            f"Cho {SLEEP_BETWEEN_HOSTS} giay "
            "truoc domain tiep theo..."
        )

        time.sleep(
            SLEEP_BETWEEN_HOSTS
        )


# ============================================================
# HOAN THANH
# ============================================================

print()
print("=" * 70)
print("HOAN THANH")
print("=" * 70)

print(
    f"Tong so URL: {len(df)}"
)

print(
    f"TLS records: {len(tls_rows)}"
)

print(
    f"Cipher records: {len(cipher_rows)}"
)

print(
    f"Certificate records: {len(cert_rows)}"
)

print(
    f"HSTS records: {len(hsts_rows)}"
)

print(
    f"HSTS Preload records: {len(preload_rows)}"
)

print(
    f"File ket qua: {OUTPUT}"
)

print("=" * 70)