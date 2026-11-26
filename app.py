"""Web app pembelajaran Monte Carlo untuk transport cahaya pada kulit."""

import plotly.express as px
import pandas as pd
import streamlit as st

from simulation import beer_lambert_transmission, simulate_transport


st.set_page_config(
    page_title="Monte Carlo Cahaya pada Kulit",
    page_icon="🔴",
    layout="wide",
)

st.title("Monte Carlo: Cahaya LED pada Kulit")
st.write(
    "Simulasi sederhana ini mengikuti paket foton saat bergerak di dalam satu "
    "lapisan kulit. Atur parameter, jalankan simulasi, lalu amati fraksi foton "
    "yang terserap, kembali keluar, atau menembus lapisan."
)

st.info(
    "Model memakai satu panjang gelombang merah (660 nm), satu lapisan "
    "homogen, dan berkas datang tegak lurus. Ini model pembelajaran transport "
    "foton, bukan model lengkap sebuah masker atau prediksi manfaat klinis."
)

with st.sidebar.form("parameter_simulasi"):
    st.header("Parameter simulasi")
    num_photons = st.slider(
        "Jumlah paket foton",
        min_value=1000,
        max_value=30000,
        value=5000,
        step=1000,
    )
    thickness_mm = st.slider(
        "Ketebalan lapisan (mm)",
        min_value=0.2,
        max_value=3.0,
        value=1.0,
        step=0.1,
    )
    mu_a = st.number_input(
        "Koefisien absorpsi μₐ (mm⁻¹)",
        min_value=0.0,
        max_value=0.2,
        value=0.03316,
        step=0.001,
        format="%.5f",
        help="Nilai awal dari Girasol dkk. (2026) untuk kulit pada 660 nm.",
    )
    mu_s_reduced = st.number_input(
        "Koefisien hamburan tereduksi μₛ′ (mm⁻¹)",
        min_value=0.0,
        max_value=4.0,
        value=1.88212,
        step=0.05,
        format="%.5f",
        help="Nilai awal dari Girasol dkk. (2026) untuk kulit pada 660 nm.",
    )
    g = st.slider(
        "Parameter arah hamburan g",
        min_value=0.0,
        max_value=0.99,
        value=0.91,
        step=0.01,
        help="Nilai awal g = 0,91 dari Girasol dkk. (2026).",
    )
    seed = st.number_input(
        "Seed bilangan acak",
        min_value=0,
        max_value=999999,
        value=42,
        step=1,
        help="Seed yang sama menghasilkan urutan bilangan acak yang sama.",
    )
    run = st.form_submit_button("Jalankan simulasi", type="primary")

if run:
    st.session_state["hasil"] = simulate_transport(
        num_photons=int(num_photons),
        mu_a_per_mm=float(mu_a),
        mu_s_reduced_per_mm=float(mu_s_reduced),
        g=float(g),
        thickness_mm=float(thickness_mm),
        seed=int(seed),
    )
    st.session_state["parameter_hasil"] = {
        "num_photons": int(num_photons),
        "thickness_mm": float(thickness_mm),
        "mu_a": float(mu_a),
        "mu_s_reduced": float(mu_s_reduced),
        "g": float(g),
        "seed": int(seed),
    }

if "hasil" not in st.session_state:
    st.session_state["hasil"] = simulate_transport(
        num_photons=5000,
        mu_a_per_mm=0.03316,
        mu_s_reduced_per_mm=1.88212,
        g=0.91,
        thickness_mm=1.0,
        seed=42,
    )
    st.session_state["parameter_hasil"] = {
        "num_photons": 5000,
        "thickness_mm": 1.0,
        "mu_a": 0.03316,
        "mu_s_reduced": 1.88212,
        "g": 0.91,
        "seed": 42,
    }

hasil = st.session_state["hasil"]
parameter = st.session_state["parameter_hasil"]
mu_s = parameter["mu_s_reduced"] / (1.0 - parameter["g"])

st.subheader("Hasil transport foton")
col_a, col_r, col_t, col_sum = st.columns(4)
col_a.metric("Diserap A", f"{hasil.absorbed * 100:.2f}%")
col_r.metric("Keluar dari sisi atas R", f"{hasil.reflected * 100:.2f}%")
col_t.metric(
    "Diteruskan T",
    f"{hasil.transmitted * 100:.2f}%",
    help=(
        "Galat baku Monte Carlo: "
        f"± {hasil.transmission_standard_error * 100:.2f} poin persentase."
    ),
)
col_sum.metric(
    "Jumlah A + R + T + belum selesai",
    f"{(hasil.absorbed + hasil.reflected + hasil.transmitted + hasil.unfinished) * 100:.2f}%",
)

if hasil.unfinished > 0:
    st.warning(
        f"Sebanyak {hasil.unfinished * 100:.3f}% paket belum keluar atau terserap "
        "dalam batas langkah komputasi. Nilai tersebut dilaporkan terpisah dan "
        "tidak dimasukkan ke A, R, atau T."
    )

left, right = st.columns(2)
with left:
    st.markdown("#### Ke mana paket foton berakhir?")
    outcome = pd.DataFrame(
        {
            "Hasil": ["Diserap A", "Keluar atas R", "Diteruskan T"],
            "Persentase": [
                hasil.absorbed * 100,
                hasil.reflected * 100,
                hasil.transmitted * 100,
            ],
        }
    )
    fig_outcome = px.bar(
        outcome,
        x="Hasil",
        y="Persentase",
        range_y=[0, 100],
        labels={"Persentase": "Paket foton (%)"},
        color="Hasil",
        color_discrete_sequence=["#555555", "#888888", "#BBBBBB"],
    )
    fig_outcome.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig_outcome, use_container_width=True)

with right:
    st.markdown("#### Foton yang terserap menurut kedalaman")
    edges = hasil.depth_edges_mm
    depth = 0.5 * (edges[:-1] + edges[1:])
    absorption = pd.DataFrame(
        {
            "Kedalaman (mm)": depth,
            "Foton awal yang terserap (%)": hasil.absorbed_by_depth * 100,
        }
    )
    fig_depth = px.bar(
        absorption,
        x="Kedalaman (mm)",
        y="Foton awal yang terserap (%)",
        labels={"Foton awal yang terserap (%)": "Foton awal (%)"},
        color_discrete_sequence=["#555555"],
    )
    fig_depth.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig_depth, use_container_width=True)
    st.caption(
        "Tiap batang menunjukkan bagian dari seluruh paket awal yang terserap "
        "di interval kedalaman tersebut. Ini bukan peta fluens."
    )

st.subheader("Pemeriksaan Beer–Lambert")
st.write(
    "Pemeriksaan ini menjalankan simulasi terpisah tanpa hamburan (μₛ = 0). "
    "Untuk berkas tegak lurus dan tanpa pantulan permukaan, transmisinya "
    "dibandingkan dengan T = exp(−μₐd)."
)
validasi = simulate_transport(
    num_photons=parameter["num_photons"],
    mu_a_per_mm=parameter["mu_a"],
    mu_s_reduced_per_mm=0.0,
    g=0.0,
    thickness_mm=parameter["thickness_mm"],
    seed=parameter["seed"] + 1,
)
t_teori = beer_lambert_transmission(
    parameter["mu_a"], parameter["thickness_mm"]
)
v1, v2, v3 = st.columns(3)
v1.metric("Transmisi MC tanpa hamburan", f"{validasi.transmitted * 100:.2f}%")
v2.metric("Beer–Lambert", f"{t_teori * 100:.2f}%")
v3.metric(
    "Selisih absolut",
    f"{abs(validasi.transmitted - t_teori) * 100:.2f} poin persentase",
)

with st.expander("Asumsi dan batas model"):
    st.markdown(
        """
        - Kulit dianggap satu lapisan homogen dan bidangnya tidak berhingga.
        - Semua foton mulai tegak lurus terhadap permukaan.
        - Setiap paket foton memiliki bobot sama; pada tumbukan paket diserap atau dihamburkan.
        - Pantulan Fresnel, pembiasan, lapisan kulit lain, dan sebaran sudut LED belum dimodelkan.
        - R menghitung foton yang kembali keluar melalui sisi atas setelah hamburan, bukan pantulan Fresnel.
        - Data optik adalah nilai rata-rata sampel kulit dari literatur, bukan nilai universal semua orang.
        - Hasil menjelaskan transport cahaya dalam model, bukan SPF, keamanan, atau manfaat klinis masker.
        """
    )

with st.expander("Rumus yang digunakan"):
    st.markdown(
        """
        **Koefisien total:** μₜ = μₐ + μₛ  
        **Jarak ke tumbukan:** s = −ln(ξ)/μₜ  
        **Peluang absorpsi pada tumbukan:** μₐ/μₜ  
        **Hamburan tereduksi:** μₛ′ = μₛ(1 − g), sehingga μₛ = μₛ′/(1 − g)  
        **Transmisi Beer–Lambert tanpa hamburan:** T = exp(−μₐd)
        """
    )
    st.write(
        f"Untuk parameter saat ini, μₛ yang dipakai program = "
        f"{mu_s:.3f} mm⁻¹."
    )

st.caption(
    "Nilai awal optik pada 660 nm: Girasol dkk. (2026), "
    "Lasers in Medical Science 41, 109. DOI: 10.1007/s10103-026-04911-7. "
    "Kode mengubah μₛ′ menjadi μₛ menggunakan relasi standar sebelum mengambil langkah foton."
)
