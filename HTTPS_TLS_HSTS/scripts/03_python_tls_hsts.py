import pandas as pd
import requests
import socket
import ssl
import time
from pathlib import Path
from urllib.parse import urlparse

# ============================================================
# CAU HINH
# ============================================================

INPUT = Path("../results/URL_Input.xlsx")
OUTPUT = Path("../results/Python_TLS_HSTS_Result.xlsx")

CONNECT_TIMEOUT = 15
HTTP_TIMEOUT = 20
SLEEP_BETWEEN_HOSTS = 1

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

missing = [
    c for c in required_columns
    if c not in df.columns
]

if missing:
    print("THIEU COT:", missing)
    raise SystemExit(1)

# ============================================================
# HAM CHUAN HOA DOMAIN
# ============================================================

def clean_domain(domain):
    if pd.isna(domain):
        return ""

    domain = str(domain).strip().lower()

    if not domain:
        return ""

    return domain


# ============================================================
# HAM TAO SSL CONTEXT
# ============================================================

def create_context(tls_version):

    context = ssl.SSLContext(
        ssl.PROTOCOL_TLS_CLIENT
    )

    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    # --------------------------------------------------------
    # TLS 1.0 / 1.1 tren OpenSSL moi co the bi vo hieu hoa
    # --------------------------------------------------------

    if tls_version in [
        ssl.TLSVersion.TLSv1,
        ssl.TLSVersion.TLSv1_1
    ]:

        try:
            context.set_ciphers(
                "DEFAULT:@SECLEVEL=0"
            )
        except Exception:
            pass

    context.minimum_version = tls_version
    context.maximum_version = tls_version

    return context


# ============================================================
# KIEM TRA MOT PHIEN BAN TLS
# ============================================================

def test_tls_version(domain, tls_version, label):

    result = {
        "TLS": label,
        "Ket qua": "Không xác định",
        "TLS negotiated": "",
        "Cipher": "",
        "Error": ""
    }

    try:

        # ----------------------------------------------------
        # DNS
        # ----------------------------------------------------

        infos = socket.getaddrinfo(
            domain,
            443,
            type=socket.SOCK_STREAM
        )

        if not infos:

            result["Error"] = "DNS khong tra ve IP"

            return result

        last_error = ""

        # ----------------------------------------------------
        # THU CAC IP
        # ----------------------------------------------------

        for info in infos:

            family = info[0]
            socktype = info[1]
            proto = info[2]
            sockaddr = info[4]

            sock = None
            ssock = None

            try:

                sock = socket.socket(
                    family,
                    socktype,
                    proto
                )

                sock.settimeout(
                    CONNECT_TIMEOUT
                )

                sock.connect(
                    sockaddr
                )

                context = create_context(
                    tls_version
                )

                ssock = context.wrap_socket(
                    sock,
                    server_hostname=domain
                )

                # ------------------------------------------------
                # BAT TAY TLS THANH CONG
                # ------------------------------------------------

                negotiated = ssock.version()

                cipher = ssock.cipher()

                result["Ket qua"] = "Có"
                result["TLS negotiated"] = (
                    negotiated or ""
                )

                if cipher:
                    result["Cipher"] = cipher[0]

                result["Error"] = ""

                return result

            except Exception as e:

                last_error = str(e)

            finally:

                try:
                    if ssock:
                        ssock.close()
                    elif sock:
                        sock.close()
                except Exception:
                    pass

        # ----------------------------------------------------
        # TAT CA IP DEU KHONG BAT TAY DUOC
        # ----------------------------------------------------

        result["Ket qua"] = "Không"
        result["Error"] = last_error[:300]

        return result

    except Exception as e:

        result["Ket qua"] = "Không xác định"
        result["Error"] = str(e)[:300]

        return result


# ============================================================
# KIEM TRA 4 PHIEN BAN TLS
# ============================================================

def test_all_tls(domain):

    versions = [
        (
            ssl.TLSVersion.TLSv1,
            "TLS 1.0"
        ),
        (
            ssl.TLSVersion.TLSv1_1,
            "TLS 1.1"
        ),
        (
            ssl.TLSVersion.TLSv1_2,
            "TLS 1.2"
        ),
        (
            ssl.TLSVersion.TLSv1_3,
            "TLS 1.3"
        )
    ]

    results = []

    for version, label in versions:

        result = test_tls_version(
            domain,
            version,
            label
        )

        results.append(result)

    return results


# ============================================================
# HTTP / HTTPS / REDIRECT / HSTS
# ============================================================

def check_https_hsts(domain):

    result = {
        "HTTP Status": "",
        "URL cuoi": "",
        "HTTPS": "Không xác định",
        "So redirect": "",
        "HSTS": "Không xác định",
        "HSTS max-age": "",
        "includeSubDomains": "",
        "preload": "",
        "HSTS Header": "",
        "Error": ""
    }

    url = "https://" + domain

    try:

        response = requests.get(
            url,
            timeout=HTTP_TIMEOUT,
            allow_redirects=True,
            verify=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "TLS-HSTS-Academic-Measurement"
                )
            }
        )

        result["HTTP Status"] = response.status_code
        result["URL cuoi"] = response.url

        # ----------------------------------------------------
        # DEM REDIRECT
        # ----------------------------------------------------

        result["So redirect"] = len(
            response.history
        )

        # ----------------------------------------------------
        # KIEM TRA HTTPS CUOI
        # ----------------------------------------------------

        final_scheme = urlparse(
            response.url
        ).scheme.lower()

        if final_scheme == "https":

            result["HTTPS"] = "Có"

        else:

            result["HTTPS"] = "Không"

        # ----------------------------------------------------
        # HSTS
        # ----------------------------------------------------

        hsts_header = response.headers.get(
            "Strict-Transport-Security",
            ""
        )

        result["HSTS Header"] = hsts_header

        if hsts_header:

            result["HSTS"] = "Có"

            # ------------------------------------------------
            # Tach cac directive
            # ------------------------------------------------

            directives = [
                x.strip()
                for x in hsts_header.split(";")
            ]

            for directive in directives:

                lower = directive.lower()

                # max-age
                if lower.startswith(
                    "max-age="
                ):

                    result["HSTS max-age"] = (
                        directive.split(
                            "=",
                            1
                        )[1].strip()
                    )

                # includeSubDomains
                elif lower == "includesubdomains":

                    result[
                        "includeSubDomains"
                    ] = "Có"

                # preload
                elif lower == "preload":

                    result[
                        "preload"
                    ] = "Có"

            if result["includeSubDomains"] == "":

                result[
                    "includeSubDomains"
                ] = "Không"

            if result["preload"] == "":

                result[
                    "preload"
                ] = "Không"

        else:

            result["HSTS"] = "Không"
            result["includeSubDomains"] = "Không"
            result["preload"] = "Không"

        return result

    except requests.exceptions.SSLError as e:

        result["Error"] = (
            "SSL/TLS error: "
            + str(e)[:300]
        )

        return result

    except requests.exceptions.Timeout:

        result["Error"] = (
            "HTTP timeout"
        )

        return result

    except requests.exceptions.RequestException as e:

        result["Error"] = str(e)[:300]

        return result

    except Exception as e:

        result["Error"] = str(e)[:300]

        return result


# ============================================================
# CERTIFICATE
# ============================================================

def get_certificate(domain):

    result = {
        "Certificate": "Không xác định",
        "Subject": "",
        "Issuer": "",
        "Valid From": "",
        "Valid To": "",
        "Serial Number": "",
        "SHA256": "",
        "Error": ""
    }

    try:

        context = ssl.create_default_context()

        # ----------------------------------------------------
        # Ket noi HTTPS
        # ----------------------------------------------------

        with socket.create_connection(
            (
                domain,
                443
            ),
            timeout=CONNECT_TIMEOUT
        ) as sock:

            with context.wrap_socket(
                sock,
                server_hostname=domain
            ) as ssock:

                cert = ssock.getpeercert()

                if not cert:

                    result["Certificate"] = (
                        "Không xác định"
                    )

                    result["Error"] = (
                        "Khong lay duoc certificate"
                    )

                    return result

                # ------------------------------------------------
                # SUBJECT
                # ------------------------------------------------

                subject_parts = []

                for item in cert.get(
                    "subject",
                    []
                ):

                    for key, value in item:

                        subject_parts.append(
                            f"{key}={value}"
                        )

                result["Subject"] = ", ".join(
                    subject_parts
                )

                # ------------------------------------------------
                # ISSUER
                # ------------------------------------------------

                issuer_parts = []

                for item in cert.get(
                    "issuer",
                    []
                ):

                    for key, value in item:

                        issuer_parts.append(
                            f"{key}={value}"
                        )

                result["Issuer"] = ", ".join(
                    issuer_parts
                )

                result["Valid From"] = cert.get(
                    "notBefore",
                    ""
                )

                result["Valid To"] = cert.get(
                    "notAfter",
                    ""
                )

                result["Serial Number"] = cert.get(
                    "serialNumber",
                    ""
                )

                result["Certificate"] = "Có"

                return result

    except ssl.SSLCertVerificationError as e:

        result["Certificate"] = (
            "Không xác thực được"
        )

        result["Error"] = str(e)[:300]

        return result

    except Exception as e:

        result["Error"] = str(e)[:300]

        return result


# ============================================================
# BIEN LUU KET QUA
# ============================================================

tls_rows = []
connection_rows = []
certificate_rows = []


# ============================================================
# CHAY 85 DOMAIN
# ============================================================

for index, row in df.iterrows():

    number = index + 1

    domain = clean_domain(
        row["Domain"]
    )

    print()
    print("=" * 70)
    print(
        f"[{number}/{len(df)}] {domain}"
    )
    print("=" * 70)

    if not domain:

        print(
            "Domain rong -> bo qua."
        )

        continue

    # ========================================================
    # TLS
    # ========================================================

    print()
    print("Dang kiem tra TLS...")

    tls_results = test_all_tls(
        domain
    )

    tls_row = {
        "ID": row["ID"],
        "Nhóm": row["Nhóm"],
        "Cơ quan/Hệ thống": row["Cơ quan/Hệ thống"],
        "Domain": domain
    }

    for tls_result in tls_results:

        label = tls_result["TLS"]

        tls_row[label] = tls_result[
            "Ket qua"
        ]

        tls_row[
            label + " - Negotiated"
        ] = tls_result[
            "TLS negotiated"
        ]

        tls_row[
            label + " - Cipher"
        ] = tls_result[
            "Cipher"
        ]

        tls_row[
            label + " - Error"
        ] = tls_result[
            "Error"
        ]

        print(
            f"  {label}: "
            f"{tls_result['Ket qua']}"
        )

    tls_rows.append(
        tls_row
    )

    # ========================================================
    # HTTPS + HSTS
    # ========================================================

    print()
    print(
        "Dang kiem tra HTTPS / HSTS..."
    )

    connection = check_https_hsts(
        domain
    )

    connection_rows.append({
        "ID": row["ID"],
        "Nhóm": row["Nhóm"],
        "Cơ quan/Hệ thống": row["Cơ quan/Hệ thống"],
        "Domain": domain,
        **connection
    })

    print(
        "  HTTPS:",
        connection["HTTPS"]
    )

    print(
        "  HSTS:",
        connection["HSTS"]
    )

    # ========================================================
    # CERTIFICATE
    # ========================================================

    print()
    print(
        "Dang lay Certificate..."
    )

    certificate = get_certificate(
        domain
    )

    certificate_rows.append({
        "ID": row["ID"],
        "Nhóm": row["Nhóm"],
        "Cơ quan/Hệ thống": row["Cơ quan/Hệ thống"],
        "Domain": domain,
        **certificate
    })

    print(
        "  Certificate:",
        certificate["Certificate"]
    )

    # ========================================================
    # LUU TAM SAU MOI DOMAIN
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
            connection_rows
        ).to_excel(
            writer,
            sheet_name="HSTS_Result",
            index=False
        )

        pd.DataFrame(
            certificate_rows
        ).to_excel(
            writer,
            sheet_name="Certificate_Result",
            index=False
        )

    print()
    print(
        "Da luu ket qua tam vao Excel."
    )

    # ========================================================
    # NGHI GIUA CAC DOMAIN
    # ========================================================

    if number < len(df):

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
    f"HTTPS/HSTS records: "
    f"{len(connection_rows)}"
)

print(
    f"Certificate records: "
    f"{len(certificate_rows)}"
)

print(
    f"File ket qua: {OUTPUT}"
)

print("=" * 70)