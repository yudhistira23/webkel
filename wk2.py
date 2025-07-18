import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
from collections import defaultdict

urls = [
    # "https://kel-pahandutseberang.palangkaraya.go.id/data-real-time/",
    "https://kel-mungkubaru.palangkaraya.go.id/data-real-time/",
]

data_grouped = defaultdict(int)

for url in urls:
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table')
    rows = table.find_all('tr')[1:]
    opd_name = url.split('/')[2]

    for row in rows:
        cols = row.find_all('td')
        tanggal_str = cols[0].get_text(strip=True)
        judul = cols[2].get_text(strip=True)
        satuan = cols[3].get_text(strip=True).strip()
        jumlah = int(cols[4].get_text(strip=True))

        # Ambil bulan dari tanggal
        tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d')
        bulan = tanggal.strftime('%Y-%m')  # e.g. '2025-07'

        key = (opd_name, bulan, judul, satuan)
        data_grouped[key] += jumlah

# Simpan ke CSV
with open('rekap_data_per_opd.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['opd', 'bulan', 'judul', 'satuan', 'jumlah'])

    for (opd, bulan, judul, satuan), jumlah in data_grouped.items():
        writer.writerow([opd, bulan, judul, satuan, jumlah])

print("Data berhasil disimpan ke 'rekap_data_per_opd.csv'")
