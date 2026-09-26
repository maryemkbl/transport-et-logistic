import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import hashlib

st.set_page_config(page_title='COPAG | Logistique & Transport', page_icon='🚚', layout='wide')

# ============================================================
# AUTHENTICATION
# Demo credentials requested for this project.
# For production, move credentials to Streamlit Secrets.
# ============================================================
USERNAME = 'admin'
PASSWORD = 'aero2026'


def check_login(username, password):
    return username == USERNAME and password == PASSWORD


if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('''
    <style>
    .stApp {background: linear-gradient(135deg,#eef5f7 0%,#f8fafb 100%);}
    .login-card {max-width:520px;margin:90px auto 0;background:white;padding:42px;border-radius:20px;box-shadow:0 10px 35px rgba(0,0,0,.10);border:1px solid #e5e7eb;}
    .login-title {font-size:34px;font-weight:800;color:#164e63;margin-bottom:4px;}
    .login-sub {color:#64748b;font-size:16px;margin-bottom:22px;}
    </style>
    <div class="login-card">
      <div class="login-title">🚚 COPAG Logistics</div>
      <div class="login-sub">Logistique & Transport Management</div>
    </div>
    ''', unsafe_allow_html=True)

    with st.form('login_form'):
        st.markdown('### 🔐 Connexion')
        username = st.text_input('Identifiant')
        password = st.text_input('Mot de passe', type='password')
        submitted = st.form_submit_button('Se connecter', use_container_width=True)
        if submitted:
            if check_login(username, password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error('Identifiant ou mot de passe incorrect.')
    st.stop()

# ============================================================
# STYLE
# ============================================================
st.markdown('''
<style>
.stApp {background:#f6f8fa;}
.block-container {padding-top:1.4rem; padding-bottom:2rem;}
.hero {background:linear-gradient(135deg,#0f4c5c,#176b7a);color:white;padding:28px 32px;border-radius:18px;margin-bottom:22px;}
.hero h1 {margin:0;font-size:34px;color:white;}
.hero p {margin:8px 0 0;color:#d8f3f5;font-size:15px;}
[data-testid="stMetric"] {background:white;border:1px solid #e5e7eb;border-radius:14px;padding:16px;box-shadow:0 3px 12px rgba(15,23,42,.05);}
.section {font-size:22px;font-weight:750;color:#164e63;margin:12px 0;}
.note {background:#fff8e8;border-left:4px solid #f59e0b;padding:12px 16px;border-radius:8px;color:#5b4a1b;font-size:13px;}
</style>
''', unsafe_allow_html=True)

# ============================================================
# DATA
# ============================================================
@st.cache_data
def load_data():
    df = pd.read_csv('copag_logistics.csv')
    df.columns = df.columns.str.strip()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    numeric = [
        'distance_km','planned_duration_min','actual_duration_min','delay_min',
        'on_time','temperature_breach','capacity_utilization','fuel_liters',
        'co2_kg','cost_mad','quantity_tons','lat','lon','o_lat','o_lon','d_lat','d_lon'
    ]
    for c in numeric:
        df[c] = pd.to_numeric(df[c], errors='coerce')
        df[c] = df[c].fillna(df[c].median())
    df = df.dropna(subset=['date'])
    df['route'] = df['origin_hub'].astype(str) + ' → ' + df['destination_city'].astype(str)
    return df.sort_values('date')

df = load_data()

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title('⚙️ Filtres')
min_date, max_date = df['date'].min().date(), df['date'].max().date()
date_range = st.sidebar.date_input('Période', (min_date, max_date), min_value=min_date, max_value=max_date)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_date, end_date = pd.Timestamp(min_date), pd.Timestamp(max_date)

modes = ['Tous'] + sorted(df['mode'].dropna().unique().tolist())
mode = st.sidebar.selectbox('Mode de transport', modes)
products = ['Tous'] + sorted(df['product_category'].dropna().unique().tolist())
product = st.sidebar.selectbox('Catégorie produit', products)

filtered = df[df['date'].between(start_date, end_date)].copy()
if mode != 'Tous':
    filtered = filtered[filtered['mode'] == mode]
if product != 'Tous':
    filtered = filtered[filtered['product_category'] == product]

if st.sidebar.button('🚪 Se déconnecter', use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

# ============================================================
# HEADER
# ============================================================
st.markdown('''
<div class="hero">
<h1>🚚 COPAG — Logistique & Transport</h1>
<p>Tableau de bord de suivi des flux, du transport, des stocks théoriques et de la performance logistique.</p>
</div>
''', unsafe_allow_html=True)

st.caption(f"Période des données : {filtered['date'].min().date()} → {filtered['date'].max().date()} | {len(filtered):,} expéditions sélectionnées")

# ============================================================
# KPIs
# ============================================================
shipments = len(filtered)
tons = filtered['quantity_tons'].sum()
on_time_rate = filtered['on_time'].mean() * 100 if shipments else 0
delay_avg = filtered['delay_min'].mean() if shipments else 0
cost = filtered['cost_mad'].sum()
breaches = int(filtered['temperature_breach'].sum())

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric('🚛 Expéditions', f'{shipments:,}')
c2.metric('📦 Volume transporté', f'{tons:,.1f} t')
c3.metric('⏱️ À l’heure', f'{on_time_rate:.1f}%')
c4.metric('🕐 Retard moyen', f'{delay_avg:.1f} min')
c5.metric('💰 Coût transport', f'{cost:,.0f} MAD')

st.divider()

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(['📊 Dashboard', '↔️ Entrées / Sorties', '📦 Stock', '🚚 Transport'])

with tab1:
    st.markdown('<div class="section">📈 Vue générale</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    daily = filtered.groupby('date', as_index=False).agg(quantity_tons=('quantity_tons','sum'), shipments=('shipment_id','count'))
    fig = px.line(daily, x='date', y='quantity_tons', markers=True, title='Volume transporté par jour')
    fig.update_layout(template='plotly_white', xaxis_title='Date', yaxis_title='Tonnes')
    col1.plotly_chart(fig, use_container_width=True)

    mode_df = filtered.groupby('mode', as_index=False)['quantity_tons'].sum()
    fig2 = px.pie(mode_df, names='mode', values='quantity_tons', hole=.55, title='Répartition du volume par mode')
    fig2.update_layout(template='plotly_white')
    col2.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    route_df = filtered.groupby('route', as_index=False).agg(Expeditions=('shipment_id','count'), Tonnes=('quantity_tons','sum')).sort_values('Tonnes', ascending=False).head(10)
    fig3 = px.bar(route_df.sort_values('Tonnes'), x='Tonnes', y='route', orientation='h', title='Top 10 routes par volume')
    fig3.update_layout(template='plotly_white', xaxis_title='Tonnes', yaxis_title='Route')
    col3.plotly_chart(fig3, use_container_width=True)

    product_df = filtered.groupby('product_category', as_index=False)['quantity_tons'].sum().sort_values('quantity_tons', ascending=False)
    fig4 = px.bar(product_df, x='product_category', y='quantity_tons', title='Volume par catégorie de produit')
    fig4.update_layout(template='plotly_white', xaxis_title='', yaxis_title='Tonnes')
    col4.plotly_chart(fig4, use_container_width=True)

    st.markdown('<div class="section">📌 Indicateurs qualité transport</div>', unsafe_allow_html=True)
    q1,q2,q3 = st.columns(3)
    q1.metric('🌡️ Ruptures température', f'{breaches}')
    q2.metric('⛽ Carburant', f"{filtered['fuel_liters'].sum():,.0f} L")
    q3.metric('🌍 CO₂', f"{filtered['co2_kg'].sum():,.0f} kg")

with tab2:
    st.markdown('<div class="section">↔️ Suivi des entrées et sorties</div>', unsafe_allow_html=True)
    st.markdown('<div class="note">Dans le fichier fourni, il n’existe pas de colonne dédiée « entrée » / « sortie ». Les entrées sont donc représentées par les marchandises arrivant aux villes de destination, et les sorties par les marchandises quittant les hubs d’origine.</div>', unsafe_allow_html=True)
    st.write('')

    entries = filtered.groupby('destination_city', as_index=False).agg(Entrees_t=('quantity_tons','sum'), Nb_entrees=('shipment_id','count')).sort_values('Entrees_t', ascending=False)
    exits = filtered.groupby('origin_hub', as_index=False).agg(Sorties_t=('quantity_tons','sum'), Nb_sorties=('shipment_id','count')).sort_values('Sorties_t', ascending=False)

    a,b = st.columns(2)
    fig_in = px.bar(entries.head(12).sort_values('Entrees_t'), x='Entrees_t', y='destination_city', orientation='h', title='Entrées par destination')
    fig_in.update_layout(template='plotly_white', xaxis_title='Tonnes', yaxis_title='Destination')
    a.plotly_chart(fig_in, use_container_width=True)

    fig_out = px.bar(exits.sort_values('Sorties_t'), x='Sorties_t', y='origin_hub', orientation='h', title='Sorties par hub d’origine')
    fig_out.update_layout(template='plotly_white', xaxis_title='Tonnes', yaxis_title='Hub')
    b.plotly_chart(fig_out, use_container_width=True)

    st.subheader('Détail des flux')
    st.dataframe(entries.rename(columns={'destination_city':'Destination'}), use_container_width=True, hide_index=True)

with tab3:
    st.markdown('<div class="section">📦 Suivi du stock théorique</div>', unsafe_allow_html=True)
    st.markdown('<div class="note">Le CSV ne contient pas de stock initial ni de mouvements de stock explicites. Cette vue calcule donc un « stock théorique » à partir des flux : Stock = Stock initial + Entrées − Sorties. Saisissez le stock initial si vous disposez de cette donnée.</div>', unsafe_allow_html=True)
    st.write('')

    initial_stock = st.number_input('Stock initial (tonnes)', min_value=0.0, value=0.0, step=1.0)

    # Node-level theoretical stock: destinations are inbound; origins are outbound.
    nodes = sorted(set(filtered['origin_hub'].dropna().astype(str)) | set(filtered['destination_city'].dropna().astype(str)))
    selected_node = st.selectbox('Site / ville à suivre', ['Tous les sites'] + nodes)

    if selected_node == 'Tous les sites':
        stock_daily = filtered.groupby('date').agg(Entrees=('quantity_tons','sum')).reset_index()
        stock_daily['Sorties'] = filtered.groupby('date')['quantity_tons'].sum().values
        stock_daily['Stock_Theorique'] = initial_stock
        st.info('Pour une lecture globale, les entrées et sorties globales se compensent. Sélectionnez un site pour suivre un stock théorique local.')
    else:
        ent = filtered[filtered['destination_city'].astype(str) == selected_node].groupby('date')['quantity_tons'].sum()
        sor = filtered[filtered['origin_hub'].astype(str) == selected_node].groupby('date')['quantity_tons'].sum()
        dates = pd.date_range(filtered['date'].min(), filtered['date'].max(), freq='D')
        stock_daily = pd.DataFrame(index=dates)
        stock_daily['Entrees'] = ent.reindex(dates, fill_value=0)
        stock_daily['Sorties'] = sor.reindex(dates, fill_value=0)
        stock_daily['Stock_Theorique'] = initial_stock + (stock_daily['Entrees'] - stock_daily['Sorties']).cumsum()
        stock_daily = stock_daily.reset_index().rename(columns={'index':'date'})

        fig_stock = px.line(stock_daily, x='date', y='Stock_Theorique', title=f'Stock théorique — {selected_node}', markers=False)
        fig_stock.update_layout(template='plotly_white', xaxis_title='Date', yaxis_title='Tonnes')
        st.plotly_chart(fig_stock, use_container_width=True)

        k1,k2,k3 = st.columns(3)
        k1.metric('Entrées', f"{stock_daily['Entrees'].sum():,.1f} t")
        k2.metric('Sorties', f"{stock_daily['Sorties'].sum():,.1f} t")
        k3.metric('Stock théorique final', f"{stock_daily['Stock_Theorique'].iloc[-1]:,.1f} t")

        st.dataframe(stock_daily.tail(30), use_container_width=True, hide_index=True)

with tab4:
    st.markdown('<div class="section">🚚 Performance transport</div>', unsafe_allow_html=True)

    mode_perf = filtered.groupby('mode', as_index=False).agg(
        Expeditions=('shipment_id','count'),
        Tonnes=('quantity_tons','sum'),
        Retard_moyen=('delay_min','mean'),
        Taux_a_l_heure=('on_time','mean'),
        Cout=('cost_mad','sum'),
        CO2=('co2_kg','sum')
    )
    mode_perf['Taux_a_l_heure'] *= 100

    st.dataframe(mode_perf.round(2), use_container_width=True, hide_index=True)

    a,b = st.columns(2)
    fig_delay = px.box(filtered, x='mode', y='delay_min', title='Distribution des retards par mode')
    fig_delay.update_layout(template='plotly_white', yaxis_title='Retard (min)', xaxis_title='Mode')
    a.plotly_chart(fig_delay, use_container_width=True)

    fig_capacity = px.scatter(filtered, x='capacity_utilization', y='cost_mad', size='quantity_tons', color='mode', hover_data=['route','product_category'], title='Utilisation capacité vs coût')
    fig_capacity.update_layout(template='plotly_white', xaxis_title='Utilisation capacité (%)', yaxis_title='Coût (MAD)')
    b.plotly_chart(fig_capacity, use_container_width=True)

    st.subheader('Dernières expéditions')
    st.dataframe(filtered.sort_values('date', ascending=False).head(50), use_container_width=True, hide_index=True)

st.divider()
st.caption('COPAG Logistics & Transport • Dashboard de démonstration • Données fournies dans copag_logistics.csv')
