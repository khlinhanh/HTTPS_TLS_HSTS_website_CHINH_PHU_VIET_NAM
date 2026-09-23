import pandas as pd
from pathlib import Path
from urllib.parse import urlparse

INPUT = Path("data/input_urls.xlsx")
OUTPUT = Path("results/URL_Input.xlsx")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(INPUT)

required_columns = ["ID", "Nhóm", "Cơ quan/Hệ thống", "URL"]

missing = [c for c in required_columns if c not in df.columns]

if missing:
    print("THIEU COT:", missing)
    raise SystemExit(1)


def get_domain(url):
    if pd.isna(url):
        return ""

    url = str(url).strip()

    if not url:
        return ""

    try:
        parsed = urlparse(url)

        if parsed.hostname:
            return parsed.hostname.lower()

    except Exception:
        pass

    return ""


result = df[required_columns].copy()

result["Domain"] = result["URL"].apply(get_domain)

result.to_excel(OUTPUT, index=False)

print("=" * 60)
print("DA CHUAN BI URL")
print("=" * 60)
print(f"Tong so URL: {len(result)}")
print(f"Domain hop le: {(result['Domain'] != '').sum()}")
print(f"Domain khong hop le: {(result['Domain'] == '').sum()}")
print(f"File: {OUTPUT}")
print("=" * 60)