import requests
from bs4 import BeautifulSoup
import pandas as pd

urls = [
    # "https://kel-mungkubaru.palangkaraya.go.id/data-real-time/",
    "https://kel-pahandutseberang.palangkaraya.go.id/data-real-time/",
    # "https://kel-pahandut.palangkaraya.go.id/data-real-time/",
    # "https://kel-panarung.palangkaraya.go.id/data-real-time/",
    # "https://kel-langkai.palangkaraya.go.id/data-real-time/",
    # "https://kel-sabaru.palangkaraya.go.id/data-real-time/"
]

#deb https://packages-cf.termux.org/apt/termux-main stable main

all_data = []

for url in urls:
    resp = requests.get(url)
    resp.raise_for_status()  # memastikan status 200 OK

    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table')  # asumsi data ada di table

    # Ambil header tabel
    headers = [header.get_text(strip=True) for header in table.find_all('th')]
    print(f"Headers for {url}: {headers}")  # Tampilkan header sesuai urutan index

    rows = table.find_all('tr')[1:]  # abaikan header
    opd_name = url.split('/')[2]  # ambil nama OPD dari URL
    for row in rows:
        cols = row.find_all('td')
        all_data.append({
            'opd': opd_name,
            'tanggal': cols[0].get_text(strip=True),
            'waktu': cols[1].get_text(strip=True),
            'judul': cols[2].get_text(strip=True),
            'satuan': cols[3].get_text(strip=True),
            'jumlah': int(cols[4].get_text(strip=True)),  # pastikan jumlah sebagai integer
        })

df = pd.DataFrame(all_data)

# Ubah kolom tanggal menjadi tipe datetime
df['tanggal'] = pd.to_datetime(df['tanggal'], format='%Y-%m-%d')

# Tambahkan kolom bulan
df['bulan'] = df['tanggal'].dt.to_period('M')

# Tambahkan kolom satuan
df['satuan'] = df['satuan'].str.strip()  # pastikan satuan tidak ada spasi berlebih

# Kelompokkan berdasarkan OPD, bulan, judul, dan satuan, lalu hitung jumlahnya
grouped_per_opd = df.groupby(['opd', 'bulan', 'judul', 'satuan'])['jumlah'].sum().reset_index()

print(grouped_per_opd)
