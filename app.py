import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# Configurazione della pagina
st.set_page_config(
    page_title="Apistica Serafina",
    page_icon="🐝",
    layout="wide"
)

# --- SUPABASE CONFIGURATION ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- CUSTOM CSS: TEMA DELICATO & NATURALE (APICOLTURA) + FONT ACCATTIVANTE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;1,400&display=swap');

    .stApp {
        background-color: #fbf9f5;
    }
    .stMetric {
        background-color: #ffffff;
        border: 1px solid #ebe5dc;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(44, 44, 44, 0.03);
    }
    .stButton>button {
        border-radius: 6px;
        font-weight: 500;
        border: 1px solid #d49b2b;
        background-color: #d49b2b;
        color: white;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #bd8722;
        border-color: #bd8722;
    }
    [data-testid="stSidebar"] {
        background-color: #f4efe6;
        border-right: 1px solid #e6e1da;
    }
    h1, h2, h3 {
        font-family: 'Playfair Display', Georgia, serif;
        color: #2c2c2c;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO SUPABASE ---
def fetch_table(table_name, order_by_date=False):
    try:
        response = supabase.table(table_name).select("*").execute()
        data = response.data
        if data:
            df = pd.DataFrame(data)
            if order_by_date and 'data' in df.columns:
                df['data_dt_sort'] = pd.to_datetime(df['data'], errors='coerce')
                df = df.sort_values(by='data_dt_sort', ascending=False).drop(columns=['data_dt_sort'])
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Errore di caricamento dalla tabella {table_name}: {e}")
        return pd.DataFrame()

# --- MENU LATERALE ---
st.sidebar.markdown("# 🐝 Apistica Serafina")
st.sidebar.markdown("---")
scelta = st.sidebar.radio(
    "Navigazione", 
    [
        "Dashboard", 
        "Report & Analisi",
        "Vendite", 
        "Carico Merci (Smielatura)", 
        "Prima Nota (Cassa)", 
        "Magazzino & Prodotti", 
        "Contatti (Clienti/Fornitori)"
    ]
)
st.sidebar.markdown("---")
st.sidebar.caption("Gestionale cloud v3.2 (Supabase)")

# ==========================================
# 1. DASHBOARD
# ==========================================
if scelta == "Dashboard":
    st.title("Apistica Serafina")
    st.markdown("Panoramica generale sull'andamento dell'attività (Cloud in tempo reale).")
    
    df_pn = fetch_table("prima_nota", order_by_date=True)
    df_prod = fetch_table("prodotti")
    df_vendite = fetch_table("vendite", order_by_date=True)
    
    incassi = df_pn[df_pn['tipo'] == 'Incasso']['importo'].sum() if not df_pn.empty and 'importo' in df_pn.columns else 0.0
    spese = df_pn[df_pn['tipo'] == 'Spesa']['importo'].sum() if not df_pn.empty and 'importo' in df_pn.columns else 0.0
    utile = incassi - spese
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Totale Incassi", f"€ {incassi:,.2f}")
    c2.metric("📉 Totale Spese", f"€ {spese:,.2f}")
    c3.metric("📈 Utile Corrente", f"€ {utile:,.2f}")
    
    valore_mag = (df_prod['prezzo_acquisto'] * df_prod['giacenza']).sum() if not df_prod.empty and 'prezzo_acquisto' in df_prod.columns else 0.0
    c4.metric("📦 Valore Magazzino", f"€ {valore_mag:,.2f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📦 Stock a magazzino", "🛒 Report Vendite", "💶 Report Cassa"])
    
    with tab1:
        st.subheader("Stock a magazzino")
        if not df_prod.empty:
            df_disp = df_prod.drop(columns=[col for col in ['id'] if col in df_prod.columns]).copy()
            df_disp['prezzo_acquisto'] = df_disp['prezzo_acquisto'].apply(lambda x: f"€ {x:,.2f}" if pd.notnull(x) else "€ 0,00")
            df_disp['prezzo_vendita'] = df_disp['prezzo_vendita'].apply(lambda x: f"€ {x:,.2f}" if pd.notnull(x) else "€ 0,00")
            df_disp['Valore Vendita Totale'] = (df_prod['prezzo_vendita'] * df_prod['giacenza']).apply(lambda x: f"€ {x:,.2f}" if pd.notnull(x) else "€ 0,00")
            st.dataframe(df_disp, use_container_width=True)
        else:
            st.info("Nessun prodotto disponibile.")
            
    with tab2:
        st.subheader("Elenco Vendite (dal più recente)")
        if not df_vendite.empty:
            df_disp = df_vendite.drop(columns=[col for col in ['id'] if col in df_vendite.columns]).copy() if 'id' in df_vendite.columns else df_vendite.copy()
            df_disp['totale'] = df_disp['totale'].apply(lambda x: f"€ {x:,.2f}" if pd.notnull(x) else "€ 0,00")
            st.dataframe(df_disp, use_container_width=True)
        else:
            st.info("Nessuna vendita registrata.")
            
    with tab3:
        st.subheader("Movimenti Prima Nota (dal più recente)")
        if not df_pn.empty:
            df_disp = df_pn.drop(columns=[col for col in ['id', 'vendita_id'] if col in df_pn.columns]).copy() if 'id' in df_pn.columns else df_pn.copy()
            df_disp['importo'] = df_disp['importo'].apply(lambda x: f"€ {x:,.2f}" if pd.notnull(x) else "€ 0,00")
            st.dataframe(df_disp, use_container_width=True)
        else:
            st.info("Nessun movimento registrato.")

# ==========================================
# 2. REPORT & ANALISI
# ==========================================
elif scelta == "Report & Analisi":
    st.title("Report & Analisi Statistiche")
    st.markdown("Filtra per intervallo di date, visualizza i totali specifici della selezione.")
    
    tab_rep_vendite, tab_rep_cassa, tab_rep_mag = st.tabs(["🍯 Vendite per Prodotto & Cliente", "💶 Analisi Cassa & Spese", "📦 Valore Potenziale Magazzino"])
    
    with tab_rep_vendite:
        st.subheader("Riepilogo Quantità e Fatturato per Articolo")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            data_inizio_v = st.date_input("Data Inizio (Vendite)", datetime(datetime.today().year, 1, 1), key="rep_v_1")
        with col_f2:
            data_fine_v = st.date_input("Data Fine (Vendite)", datetime.today(), key="rep_v_2")
            
        df_v_all = fetch_table("vendite", order_by_date=True)
        if not df_v_all.empty and 'data' in df_v_all.columns:
            df_v_all['data_dt'] = pd.to_datetime(df_v_all['data']).dt.date
            df_v = df_v_all[
                (df_v_all['stato'] != 'Annullata') & 
                (df_v_all['articolo'].notnull()) & 
                (df_v_all['data_dt'] >= data_inizio_v) & 
                (df_v_all['data_dt'] <= data_fine_v)
            ]
        else:
            df_v = pd.DataFrame()
            
        if not df_v.empty:
            df_agg = df_v.groupby('articolo').agg({'quantita': 'sum', 'totale': 'sum'}).reset_index()
            df_agg.columns = ['articolo', 'qta_totale', 'fatturato_totale']
            df_agg = df_agg.sort_values(by='fatturato_totale', ascending=False)
            
            tot_fatturato_sel = df_agg['fatturato_totale'].sum()
            tot_qta_sel = df_agg['qta_totale'].sum()
            
            mk1, mk2 = st.columns(2)
            mk1.metric("💰 Fatturato Selezionato", f"€ {tot_fatturato_sel:,.2f}")
            mk2.metric("📦 Quantità Totale Venduta", f"{int(tot_qta_sel)} pz")
            st.markdown("<br>", unsafe_allow_html=True)

            # --- SEZIONE: DETTAGLIO VENDITE PER SINGOLO PRODOTTO (CON TOTALI) ---
            st.markdown("### 🔍 Dettaglio Vendite per Singolo Prodotto")
            lista_articoli_rep = df_agg['articolo'].tolist()
            prodotto_selezionato_rep = st.selectbox("Seleziona un prodotto per vedere l'elenco di tutte le vendite", options=lista_articoli_rep, key="sel_prod_rep_dettaglio")
            
            if prodotto_selezionato_rep:
                df_storico_prod = df_v[df_v['articolo'] == prodotto_selezionato_rep].copy()
                if not df_storico_prod.empty:
                    tot_qta_prod = df_storico_prod['quantita'].sum()
                    tot_imp_prod = df_storico_prod['totale'].sum()
                    
                    riga_tot_prod = pd.DataFrame({
                        'cliente': ['--- TOTALE ---'],
                        'articolo': [''],
                        'quantita': [int(tot_qta_prod)],
                        'totale': [tot_imp_prod],
                        'stato': [''],
                        'tipo': ['']
                    }, index=[0])
                    
                    df_storico_prod_full = pd.concat([df_storico_prod, riga_tot_prod], ignore_index=True)
                    df_storico_prod_show = df_storico_prod_full.drop(columns=[col for col in ['id', 'vendita_id', 'data_dt'] if col in df_storico_prod_full.columns])
                    df_storico_prod_show['totale'] = df_storico_prod_show['totale'].apply(lambda x: f"€ {x:,.2f}" if pd.notnull(x) else "€ 0,00")
                    st.dataframe(df_storico_prod_show, use_container_width=True)
                else:
                    st.info("Nessuna vendita registrata per questo prodotto nel periodo.")

            st.markdown("<br>", unsafe_allow_html=True)

            # --- SEZIONE: DETTAGLIO ACQUISTI PER SINGOLO CLIENTE (CON TOTALI) ---
            st.markdown("### 👥 Dettaglio Acquisti per Singolo Cliente")
            df_clienti_attivi = df_v[df_v['cliente'].notnull()]['cliente'].unique().tolist()
            if df_clienti_attivi:
                cliente_selezionato_rep = st.selectbox("Seleziona un cliente per vedere tutto ciò che ha acquistato", options=df_clienti_attivi, key="sel_cli_rep_dettaglio")
                if cliente_selezionato_rep:
                    df_storico_cli = df_v[df_v['cliente'] == cliente_selezionato_rep].copy()
                    if not df_storico_cli.empty:
                        tot_qta_cli = df_storico_cli['quantita'].sum()
                        tot_imp_cli = df_storico_cli['totale'].sum()
                        
                        st.info(f"💡 Spesa complessiva di **{cliente_selezionato_rep}** nel periodo: **€ {tot_imp_cli:,.2f}** ({int(tot_qta_cli)} pz)")
                        
                        riga_tot_cli_dett = pd.DataFrame({
                            'cliente': ['--- TOTALE ---'],
                            'articolo': [''],
                            'quantita': [int(tot_qta_cli)],
                            'totale': [tot_imp_cli],
                            'stato': [''],
                            'tipo': ['']
                        }, index=[0])
                        
                        df_storico_cli_full = pd.concat([df_storico_cli, riga_tot_cli_dett], ignore_index=True)
                        df_storico_cli_show = df_storico_cli_full.drop(columns=[col for col in ['id', 'vendita_id', 'data_dt'] if col in df_storico_cli_full.columns])
                        df_storico_cli_show['totale'] = df_storico_cli_show['totale'].apply(lambda x: f"€ {x:,.2f}" if pd.notnull(x) else "€ 0,00")
                        st.dataframe(df_storico_cli_show, use_container_width=True)
                    else:
                        st.info("Nessun acquisto registrato per questo cliente nel periodo.")
            else:
                st.info("Nessun cliente registrato nelle vendite del periodo.")

            st.markdown("<br>", unsafe_allow_html=True)

            # --- SEZIONE: REPORT CLIENTE - FATTURATO COMPLESSIVO (CON TOTALI) ---
            st.markdown("### 👥 Report: Cliente – Fatturato")
            df_cli_agg = df_v.groupby('cliente').agg({'totale': 'sum', 'quantita': 'sum'}).reset_index()
            df_cli_agg.columns = ['cliente', 'fatturato_cliente', 'qta_totale_cliente']
            df_cli_agg = df_cli_agg.sort_values(by='fatturato_cliente', ascending=False)
            
            if not df_cli_agg.empty:
                tot_fatt_cli = df_cli_agg['fatturato_cliente'].sum()
                tot_qta_cli_tot = df_cli_agg['qta_totale_cliente'].sum()
                
                riga_tot_cli = pd.DataFrame({
                    'cliente': ['--- TOTALE COMPLESSIVO ---'],
                    'fatturato_cliente': [tot_fatt_cli],
                    'qta_totale_cliente': [int(tot_qta_cli_tot)]
                })
                df_cli_rep_full = pd.concat([df_cli_agg, riga_tot_cli], ignore_index=True)
                df_cli_rep_full['fatturato_cliente_fmt'] = df_cli_rep_full['fatturato_cliente'].apply(lambda x: f"€ {x:,.2f}")
                
                df_cli_show = df_cli_rep_full[['cliente', 'qta_totale_cliente', 'fatturato_cliente_fmt']].copy()
                df_cli_show.columns = ['Cliente', 'Pezzi Acquistati Totali', 'Fatturato']
                st.dataframe(df_cli_show, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📋 Tabella Riepilogativa per Articolo")
            
            df_agg['prezzo_medio'] = df_agg['fatturato_totale'] / df_agg['qta_totale']
            media_ponderata_totale = tot_fatturato_sel / tot_qta_sel if tot_qta_sel > 0 else 0.0
            
            riga_totale = pd.DataFrame({
                'articolo': ['--- TOTALE / MEDIA ---'],
                'qta_totale': [int(tot_qta_sel)],
                'fatturato_totale': [tot_fatturato_sel],
                'prezzo_medio': [media_ponderata_totale]
            })
            df_v_display_full = pd.concat([df_agg, riga_totale], ignore_index=True)
            df_v_display_full['fatturato_totale_fmt'] = df_v_display_full['fatturato_totale'].apply(lambda x: f"€ {x:,.2f}")
            df_v_display_full['prezzo_medio_fmt'] = df_v_display_full['prezzo_medio'].apply(lambda x: f"€ {x:,.2f}")
            
            df_table_show = df_v_display_full[['articolo', 'qta_totale', 'prezzo_medio_fmt', 'fatturato_totale_fmt']].copy()
            df_table_show.columns = ['Articolo', 'Quantità Totale', 'Prezzo Medio di Vendita', 'Fatturato Totale']
            st.dataframe(df_table_show, use_container_width=True)

            st.markdown("---")
            st.markdown("### 📊 Grafico Fatturato per Articolo")
            df_grafico = df_agg.set_index('articolo')['fatturato_totale']
            st.bar_chart(df_grafico)
        else:
            st.info("Nessun dato di vendita disponibile nel periodo selezionato.")
            
    with tab_rep_cassa:
        st.subheader("Riepilogo Cassa per Categoria")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            data_inizio_pn = st.date_input("Data Inizio (Cassa)", datetime(datetime.today().year, 1, 1), key="rep_c_1")
        with col_c2:
            data_fine_pn = st.date_input("Data Fine (Cassa)", datetime.today(), key="rep_c_2")
            
        df_pn_all = fetch_table("prima_nota", order_by_date=True)
        if not df_pn_all.empty and 'data' in df_pn_all.columns:
            df_pn_all['data_dt'] = pd.to_datetime(df_pn_all['data']).dt.date
            df_pn_f = df_pn_all[(df_pn_all['data_dt'] >= data_inizio_pn) & (df_pn_all['data_dt'] <= data_fine_pn)]
        else:
            df_pn_f = pd.DataFrame()
            
        if not df_pn_f.empty:
            inc_periodo = df_pn_f[df_pn_f['tipo'] == 'Incasso']['importo'].sum()
            spe_periodo = df_pn_f[df_pn_f['tipo'] == 'Spesa']['importo'].sum()
            uti_periodo = inc_periodo - spe_periodo
            
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("💰 Incassi nel periodo", f"€ {inc_periodo:,.2f}")
            mc2.metric("📉 Spese nel periodo", f"€ {spe_periodo:,.2f}")
            mc3.metric("📈 Saldo del periodo", f"€ {uti_periodo:,.2f}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            df_pn_rep = df_pn_f.groupby(['tipo', 'categoria'])['importo'].sum().reset_index()
            df_pn_rep.columns = ['tipo', 'categoria', 'totale_importo']
            
            # Riga totale per la cassa
            tot_imp_cassa = df_pn_rep['totale_importo'].sum()
            riga_tot_cassa = pd.DataFrame({
                'tipo': ['--- TOTALE ---'],
                'categoria': ['---'],
                'totale_importo': [tot_imp_cassa]
            })
            df_pn_rep_full = pd.concat([df_pn_rep, riga_tot_cassa], ignore_index=True)
            df_pn_rep_display = df_pn_rep_full.copy()
            df_pn_rep_display['totale_importo'] = df_pn_rep_display['totale_importo'].apply(lambda x: f"€ {x:,.2f}")
            st.dataframe(df_pn_rep_display, use_container_width=True)
        else:
            st.info("Nessun movimento registrato in prima nota nel periodo selezionato.")
            
    with tab_rep_mag:
        st.subheader("Analisi Valore Magazzino a Prezzo di Vendita")
        df_pm = fetch_table("prodotti")
        if not df_pm.empty:
            df_pm['Valore d\'Acquisto Totale'] = df_pm['prezzo_acquisto'] * df_pm['giacenza']
            df_pm['Valore di Vendita Potenziale'] = df_pm['prezzo_vendita'] * df_pm['giacenza']
            
            tot_acq = df_pm['Valore d\'Acquisto Totale'].sum()
            tot_vend = df_pm['Valore di Vendita Potenziale'].sum()
            tot_giacenza_mag = df_pm['giacenza'].sum()
            
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("📦 Valore Totale Acquisto/Produzione", f"€ {tot_acq:,.2f}")
            col_m2.metric("💰 Valore Potenziale di Vendita", f"€ {tot_vend:,.2f}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Riga totale magazzino
            riga_tot_mag = pd.DataFrame({
                'id': [0],
                'codice': ['--- TOTALE ---'],
                'descrizione': ['---'],
                'prezzo_acquisto': [0.0],
                'prezzo_vendita': [0.0],
                'giacenza': [int(tot_giacenza_mag)],
                'Valore d\'Acquisto Totale': [tot_acq],
                'Valore di Vendita Potenziale': [tot_vend]
            })
            df_pm_full = pd.concat([df_pm, riga_tot_mag], ignore_index=True)
            
            df_pm_disp = df_pm_full.copy()
            df_pm_disp['prezzo_acquisto'] = df_pm_disp['prezzo_acquisto'].apply(lambda x: f"€ {x:,.2f}" if x > 0 else "-")
            df_pm_disp['prezzo_vendita'] = df_pm_disp['prezzo_vendita'].apply(lambda x: f"€ {x:,.2f}" if x > 0 else "-")
            df_pm_disp['Valore d\'Acquisto Totale'] = df_pm_disp['Valore d\'Acquisto Totale'].apply(lambda x: f"€ {x:,.2f}")
            df_pm_disp['Valore di Vendita Potenziale'] = df_pm_disp['Valore di Vendita Potenziale'].apply(lambda x: f"€ {x:,.2f}")
            
            cols_show_mag = [c for c in ['codice', 'descrizione', 'prezzo_acquisto', 'prezzo_vendita', 'giacenza', 'Valore d\'Acquisto Totale', 'Valore di Vendita Potenziale'] if c in df_pm_disp.columns]
            st.dataframe(df_pm_disp[cols_show_mag], use_container_width=True)
        else:
            st.info("Magazzino vuoto.")
            
# ==========================================
# 3. VENDITE
# ==========================================
elif scelta == "Vendite":
    st.title("Gestione Vendite")
    tab_inserimento, tab_modifica, tab_elenco = st.tabs(["Nuova Vendita", "Modifica / Elimina Vendita", "Elenco Vendite"])
    
    with tab_elenco:
        df = fetch_table("vendite", order_by_date=True)
        if not df.empty:
            df_table = df.drop(columns=[col for col in ['id'] if col in df.columns]).copy() if 'id' in df.columns else df.copy()
            df_table['totale'] = df_table['totale'].apply(lambda x: f"€ {x:,.2f}")
            st.dataframe(df_table, use_container_width=True)
        else:
            st.info("Nessuna vendita presente.")
            
    with tab_modifica:
        st.subheader("✏️ Modifica o Annulla Vendita Esistente")
        df_vendite_mod = fetch_table("vendite", order_by_date=True)
        df_prodotti_all = fetch_table("prodotti")
        
        if not df_vendite_mod.empty:
            df_vendite_mod['etichetta_scelta'] = df_vendite_mod.apply(lambda r: f"ID:{r['id']} | Data: {r['data']} | Cliente: {r['cliente']} | Articolo: {r['articolo']} (Qt: {r['quantita']}) - Tot: € {r['totale']:,.2f}", axis=1)
            
            vendita_selezionata_str = st.selectbox("Seleziona Vendita da modificare/eliminare", df_vendite_mod['etichetta_scelta'].tolist(), key="sel_vend_mod_box")
            r_vend_sel = df_vendite_mod[df_vendite_mod['etichetta_scelta'] == vendita_selezionata_str].iloc[0]
            v_id_edit = int(r_vend_sel['id'])
            
            df_clienti = fetch_table("contatti")
            if not df_clienti.empty and 'tipo' in df_clienti.columns:
                lista_clienti_edit = df_clienti[df_clienti['tipo'].isin(['Cliente', 'Clienti'])]['nome'].tolist()
            else:
                lista_clienti_edit = []
            
            with st.form("form_modifica_vendita_dettaglio"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    m_data = st.date_input("Data Vendita", datetime.strptime(str(r_vend_sel['data']), "%Y-%m-%d").date())
                with ec2:
                    m_tipo_op = st.selectbox("Tipo operazione", ["Vendita", "Reso"], index=0 if r_vend_sel['tipo']=="Vendita" else 1)
                
                if lista_clienti_edit and r_vend_sel['cliente'] in lista_clienti_edit:
                    idx_cli = lista_clienti_edit.index(r_vend_sel['cliente'])
                else:
                    idx_cli = 0
                m_cliente = st.selectbox("Cliente", options=lista_clienti_edit if lista_clienti_edit else [r_vend_sel['cliente']], index=idx_cli)
                
                lista_prod_edit = df_prodotti_all['descrizione'].tolist() if not df_prodotti_all.empty else []
                
                art_attuale = r_vend_sel['articolo']
                idx_prod = lista_prod_edit.index(art_attuale) if art_attuale in lista_prod_edit else 0
                m_articolo = st.selectbox("Articolo", options=lista_prod_edit, index=idx_prod)
                
                if not df_prodotti_all.empty and m_articolo:
                    p_info_mod = df_prodotti_all[df_prodotti_all['descrizione'] == m_articolo]
                    if not p_info_mod.empty:
                        giac_reale_edit = int(p_info_mod.iloc[0]['giacenza'])
                        st.info(f"📦 **Giacenza reale disponibile per '{m_articolo}':** {giac_reale_edit} pz")

                ec_q, ec_p = st.columns(2)
                with ec_q:
                    m_quantita = st.number_input("Quantità", min_value=1, value=int(r_vend_sel['quantita']), step=1)
                
                prezzo_iniziale_edit = float(r_vend_sel['totale']) / int(r_vend_sel['quantita']) if int(r_vend_sel['quantita']) > 0 else 0.0
                with ec_p:
                    m_prezzo_unitario = st.number_input("Prezzo Unitario (€)", min_value=0.0, value=prezzo_iniziale_edit, step=0.10, format="%.2f")
                
                st.markdown("<br>", unsafe_allow_html=True)
                bc1, bc2 = st.columns(2)
                with bc1:
                    btn_salva_mod = st.form_submit_button("💾 Salva Modifiche", use_container_width=True)
                with bc2:
                    btn_elimina_vend = st.form_submit_button("🗑️ Elimina Vendita", use_container_width=True)
                    
                if btn_salva_mod:
                    vecchia_qta = int(r_vend_sel['quantita'])
                    vecchio_articolo = r_vend_sel['articolo']
                    vecchio_tipo = r_vend_sel['tipo']
                    
                    if vecchio_articolo == m_articolo:
                        if not df_prodotti_all.empty:
                            prod_curr = df_prodotti_all[df_prodotti_all['descrizione'] == m_articolo]
                            if not prod_curr.empty:
                                p_id_c = int(prod_curr.iloc[0]['id'])
                                giac_c = int(prod_curr.iloc[0]['giacenza'])
                                
                                if vecchio_tipo == "Vendita" and m_tipo_op == "Vendita":
                                    differenza = m_quantita - vecchia_qta
                                    nuova_giac = giac_c - differenza
                                elif vecchio_tipo == "Reso" and m_tipo_op == "Reso":
                                    differenza = m_quantita - vecchia_qta
                                    nuova_giac = giac_c + differenza
                                else:
                                    if m_tipo_op == "Vendita":
                                        nuova_giac = giac_c - m_quantita + vecchia_qta
                                    else:
                                        nuova_giac = giac_c + m_quantita - vecchia_qta
                                        
                                if m_tipo_op == "Vendita" and nuova_giac < 0:
                                    st.error("⚠️ Quantità richiesta superiore alla giacenza disponibile!")
                                else:
                                    supabase.table("prodotti").update({"giacenza": nuova_giac}).eq("id", p_id_c).execute()
                    else:
                        if vecchio_articolo and not df_prodotti_all.empty:
                            p_old = df_prodotti_all[df_prodotti_all['descrizione'] == vecchio_articolo]
                            if not p_old.empty:
                                id_p_o = int(p_old.iloc[0]['id'])
                                giac_o = int(p_old.iloc[0]['giacenza'])
                                ripr_giac = giac_o + vecchia_qta if vecchio_tipo == "Vendita" else giac_o - vecchia_qta
                                supabase.table("prodotti").update({"giacenza": ripr_giac}).eq("id", id_p_o)
                        
                        if m_articolo and not df_prodotti_all.empty:
                            p_new = df_prodotti_all[df_prodotti_all['descrizione'] == m_articolo]
                            if not p_new.empty:
                                id_p_n = int(p_new.iloc[0]['id'])
                                giac_n = int(p_new.iloc[0]['giacenza'])
                                nuova_giac = giac_n - m_quantita if m_tipo_op == "Vendita" else giac_n + m_quantita
                                supabase.table("prodotti").update({"giacenza": nuova_giac}).eq("id", id_p_n).execute()

                    nuovo_totale = m_prezzo_unitario * m_quantita
                    
                    supabase.table("vendite").update({
                        "data": str(m_data), "tipo": m_tipo_op, "cliente": m_cliente,
                        "totale": nuovo_totale, "articolo": m_articolo, "quantita": m_quantita
                    }).eq("id", v_id_edit).execute()
                    
                    supabase.table("prima_nota").delete().eq("vendita_id", v_id_edit).execute()
                    cat_pn = "Vendite" if m_tipo_op == "Vendita" else "Resi"
                    desc_pn = f"{m_tipo_op} - {m_cliente} - {m_articolo} (x{m_quantita})"
                    tipo_pn = "Incasso" if m_tipo_op == "Vendita" else "Spesa"
                    supabase.table("prima_nota").insert({
                        "data": str(m_data), "tipo": tipo_pn, "categoria": cat_pn,
                        "descrizione": desc_pn, "importo": nuovo_totale, "vendita_id": v_id_edit
                    }).execute()
                    
                    st.success("✅ Vendita modificata con successo!")
                    st.rerun()
                    
                elif btn_elimina_vend:
                    art_venduto = r_vend_sel['articolo']
                    qta_venduta = r_vend_sel['quantita']
                    tipo_vendita = r_vend_sel['tipo']
                    
                    if art_venduto and not df_prodotti_all.empty:
                        prod_check = df_prodotti_all[df_prodotti_all['descrizione'] == art_venduto]
                        if not prod_check.empty:
                            p_id_mag = int(prod_check.iloc[0]['id'])
                            giac_att = int(prod_check.iloc[0]['giacenza'])
                            nuova_giac = giac_att + int(qta_venduta) if tipo_vendita == "Vendita" else giac_att - int(qta_venduta)
                            supabase.table("prodotti").update({"giacenza": nuova_giac}).eq("id", p_id_mag).execute()
                    
                    supabase.table("prima_nota").delete().eq("vendita_id", v_id_edit).execute()
                    supabase.table("vendite").delete().eq("id", v_id_edit).execute()
                    
                    st.success("✅ Vendita eliminata e magazzino ripristinato!")
                    st.rerun()
        else:
            st.info("Nessuna vendita disponibile da modificare.")
            
    with tab_inserimento:
        df_contatti = fetch_table("contatti")
        lista_clienti = df_contatti[df_contatti['tipo'].isin(['Cliente', 'Clienti'])]['nome'].tolist() if not df_contatti.empty and 'tipo' in df_contatti.columns else []
        df_prodotti = fetch_table("prodotti")
        
        if st.session_state.get("show_success", False):
            st.success("✅ Vendita registrata con successo su Supabase!")
            st.session_state.show_success = False

        col_a, col_b = st.columns(2)
        with col_a:
            data = st.date_input("Data", datetime.today(), key="v_data")
        with col_b:
            tipo = st.selectbox("Tipo operazione", ["Vendita", "Reso"], key="v_tipo")
        
        if lista_clienti:
            cliente = st.selectbox("Cliente *", options=lista_clienti, index=None, placeholder="Seleziona un cliente...", key="v_cliente")
        else:
            cliente = st.text_input("Cliente * (Digita nome)", key="v_cliente_txt")
            
        st.markdown("---")
        st.markdown("#### 📦 Selezione Articolo & Prezzo")
        
        totale_calcolato = 0.0
        articolo_scelto = None
        
        if not df_prodotti.empty:
            lista_prod = df_prodotti['descrizione'].tolist()
            articolo_scelto = st.selectbox("Prodotto *", options=lista_prod, index=None, placeholder="Seleziona un prodotto...", key="v_prodotto")
            
            col_q, col_p = st.columns(2)
            with col_q:
                quantita = st.number_input("Quantità", min_value=1, value=1, step=1, key="v_qta")
            
            if articolo_scelto:
                prod_info = df_prodotti[df_prodotti['descrizione'] == articolo_scelto].iloc[0]
                prezzo_default = float(prod_info['prezzo_vendita'])
                giacenza_disponibile = int(prod_info['giacenza'])
                
                st.info(f"📦 **Giacenza reale disponibile per '{articolo_scelto}':** {giacenza_disponibile} pz")
                
                with col_p:
                    prezzo_unitario = st.number_input("Prezzo Unitario (€)", min_value=0.0, value=prezzo_default, step=0.10, format="%.2f")
                
                totale_calcolato = prezzo_unitario * quantita
                st.markdown(f"### 💶 Totale Complessivo: **€ {totale_calcolato:,.2f}**")
        else:
            st.warning("Nessun prodotto disponibile in magazzino.")
            
        if st.button("🚀 Registra Vendita", type="primary", use_container_width=True):
            cli_val = st.session_state.get("v_cliente") if lista_clienti else st.session_state.get("v_cliente_txt")
            art_val = st.session_state.get("v_prodotto")
            qta_val = st.session_state.get("v_qta", 1)
            prezzo_finale_unitario = prezzo_unitario if 'prezzo_unitario' in locals() else 0.0
            totale_finale = prezzo_finale_unitario * qta_val
            
            if not cli_val or not art_val:
                st.error("⚠️ I campi 'Cliente' e 'Prodotto' sono obbligatori!")
            else:
                prod_info = df_prodotti[df_prodotti['descrizione'] == art_val].iloc[0]
                prod_id = int(prod_info['id'])
                giacenza_attuale = int(prod_info['giacenza'])
                
                if tipo == "Vendita" and qta_val > giacenza_attuale:
                    st.error(f"⚠️ Quantità richiesta ({qta_val}) superiore alla giacenza ({giacenza_attuale} pz)!")
                else:
                    res_ins = supabase.table("vendite").insert({
                        "data": str(data), "tipo": tipo, "cliente": cli_val,
                        "totale": totale_finale, "stato": "Pagata", "articolo": art_val, "quantita": int(qta_val)
                    }).execute()
                    
                    id_vendita_creata = res_ins.data[0]['id'] if res_ins.data else None
                    
                    nuova_giacenza = giacenza_attuale - int(qta_val) if tipo == "Vendita" else giacenza_attuale + int(qta_val)
                    supabase.table("prodotti").update({"giacenza": nuova_giacenza}).eq("id", prod_id).execute()
                    
                    cat_pn = "Vendite" if tipo == "Vendita" else "Resi"
                    desc_pn = f"{tipo} - {cli_val} - {art_val} (x{qta_val})"
                    tipo_pn = "Incasso" if tipo == "Vendita" else "Spesa"
                    
                    supabase.table("prima_nota").insert({
                        "data": str(data), "tipo": tipo_pn, "categoria": cat_pn,
                        "descrizione": desc_pn, "importo": totale_finale, "vendita_id": id_vendita_creata
                    }).execute()
                    
                    st.session_state.show_success = True
                    st.rerun()

# ==========================================
# 4. CARICO MERCI (SMIELATURA)
# ==========================================
elif scelta == "Carico Merci (Smielatura)":
    st.title("Carico Merci e Smielatura")
    tab_reg_sm, tab_gest_sm = st.tabs(["Nuova Smielatura", "Modifica / Elimina Smielatura"])
    
    df_prodotti = fetch_table("prodotti")
    
    with tab_reg_sm:
        if not df_prodotti.empty:
            with st.form("form_smielatura", clear_on_submit=True):
                data_carico = st.date_input("Data Smielatura", datetime.today())
                prodotto_scelto = st.selectbox("Prodotto da caricare *", options=df_prodotti['descrizione'].tolist())
                quantita_carico = st.number_input("Quantità prodotta", min_value=1, value=10, step=1)
                note_carico = st.text_input("Note / Descrizione opzionale", value="Smielatura")
                
                registra_spesa = st.checkbox("Registra costo anche in Prima Nota (Cassa)")
                importo_spesa = st.number_input("Costo sostenuto (€)", min_value=0.0, format="%.2f")
                
                if st.form_submit_button("🍯 Conferma e Carica", use_container_width=True):
                    # 1. Registra il carico nella tabella dedicata
                    supabase.table("carichi_merci").insert({
                        "data": str(data_carico),
                        "articolo": prodotto_scelto,
                        "quantita": int(quantita_carico),
                        "note": note_carico
                    }).execute()
                    
                    # 2. Aggiorna la giacenza del prodotto in magazzino
                    prod_info = df_prodotti[df_prodotti['descrizione'] == prodotto_scelto].iloc[0]
                    prod_id = int(prod_info['id'])
                    giacenza_attuale = int(prod_info['giacenza'])
                    nuova_giacenza = giacenza_attuale + int(quantita_carico)
                    supabase.table("prodotti").update({"giacenza": nuova_giacenza}).eq("id", prod_id).execute()
                    
                    # 3. Opzionalmente registra la spesa in prima nota
                    if registra_spesa and importo_spesa > 0:
                        supabase.table("prima_nota").insert({
                            "data": str(data_carico), 
                            "tipo": "Spesa", 
                            "categoria": "Smielatura/Produzione",
                            "descrizione": f"{note_carico} - {prodotto_scelto} (+{quantita_carico} pz)", 
                            "importo": importo_spesa
                        }).execute()
                    
                    st.success(f"✅ Carico effettuato! Nuova giacenza: {nuova_giacenza} pz.")
                    st.rerun()
        else:
            st.warning("⚠️ Nessun prodotto presente in magazzino.")

    with tab_gest_sm:
        st.subheader("✏️ Storico e Gestione Smielature")
        df_carichi = fetch_table("carichi_merci", order_by_date=True)
        
        if not df_carichi.empty:
            df_carichi['etichetta_sm'] = df_carichi.apply(lambda r: f"ID:{r['id']} | Data: {r['data']} | {r['articolo']} (+{r['quantita']} pz)", axis=1)
            sm_scelta = st.selectbox("Seleziona Smielatura da modificare/eliminare", df_carichi['etichetta_sm'].tolist(), key="sel_sm_mod")
            r_sm = df_carichi[df_carichi['etichetta_sm'] == sm_scelta].iloc[0]
            sm_id = int(r_sm['id'])
            
            with st.form("form_mod_smielatura"):
                msm_data = st.date_input("Data Smielatura", datetime.strptime(str(r_sm['data']), "%Y-%m-%d").date())
                
                lista_prod_sm = df_prodotti['descrizione'].tolist() if not df_prodotti.empty else []
                art_corrente = r_sm['articolo']
                idx_p_sm = lista_prod_sm.index(art_corrente) if art_corrente in lista_prod_sm else 0
                
                msm_prodotto = st.selectbox("Prodotto", options=lista_prod_sm, index=idx_p_sm)
                msm_quantita = st.number_input("Quantità prodotta", min_value=1, value=int(r_sm['quantita']), step=1)
                msm_note = st.text_input("Note", value=str(r_sm['note']) if pd.notnull(r_sm['note']) else "")
                
                sc1, sc2 = st.columns(2)
                with sc1:
                    btn_agg_sm = st.form_submit_button("💾 Salva Modifiche", use_container_width=True)
                with sc2:
                    btn_del_sm = st.form_submit_button("🗑️ Elimina Carico", use_container_width=True)
                    
                if btn_agg_sm:
                    vecchia_qta = int(r_sm['quantita'])
                    vecchio_articolo = r_sm['articolo']
                    
                    # Gestione ricalcolo magazzino in base alle modifiche
                    if vecchio_articolo == msm_prodotto:
                        differenza = msm_quantita - vecchia_qta
                        if differenza != 0 and not df_prodotti.empty:
                            p_info = df_prodotti[df_prodotti['descrizione'] == msm_prodotto].iloc[0]
                            p_id = int(p_info['id'])
                            nuova_g = int(p_info['giacenza']) + differenza
                            supabase.table("prodotti").update({"giacenza": nuova_g}).eq("id", p_id).execute()
                    else:
                        # Ripristina il vecchio prodotto togliendo la vecchia quantità
                        if not df_prodotti.empty:
                            p_old = df_prodotti[df_prodotti['descrizione'] == vecchio_articolo]
                            if not p_old.empty:
                                id_po = int(p_old.iloc[0]['id'])
                                giac_po = int(p_old.iloc[0]['giacenza']) - vecchia_qta
                                supabase.table("prodotti").update({"giacenza": max(0, giac_po)}).eq("id", id_po).execute()
                            
                            # Aggiungi al nuovo prodotto
                            p_new = df_prodotti[df_prodotti['descrizione'] == msm_prodotto]
                            if not p_new.empty:
                                id_pn = int(p_new.iloc[0]['id'])
                                giac_pn = int(p_new.iloc[0]['giacenza']) + msm_quantita
                                supabase.table("prodotti").update({"giacenza": giac_pn}).eq("id", id_pn).execute()
                    
                    # Aggiorna il record del carico
                    supabase.table("carichi_merci").update({
                        "data": str(msm_data),
                        "articolo": msm_prodotto,
                        "quantita": int(msm_quantita),
                        "note": msm_note
                    }).eq("id", sm_id).execute()
                    
                    st.success("✅ Carico aggiornato con successo!")
                    st.rerun()
                    
                elif btn_del_sm:
                    qta_da_stornare = int(r_sm['quantita'])
                    art_da_stornare = r_sm['articolo']
                    
                    # Storna la giacenza dal magazzino
                    if not df_prodotti.empty:
                        p_storno = df_prodotti[df_prodotti['descrizione'] == art_da_stornare]
                        if not p_storno.empty:
                            id_st = int(p_storno.iloc[0]['id'])
                            giac_st = int(p_storno.iloc[0]['giacenza']) - qta_da_stornare
                            supabase.table("prodotti").update({"giacenza": max(0, giac_st)}).eq("id", id_st).execute()
                    
                    # Elimina il carico
                    supabase.table("carichi_merci").delete().eq("id", sm_id).execute()
                    st.success("✅ Carico eliminato e magazzino ripristinato!")
                    st.rerun()
        else:
            st.info("Nessun carico merci registrato.")
            
# ==========================================
# 5. PRIMA NOTA
# ==========================================
elif scelta == "Prima Nota (Cassa)":
    st.title("Prima Nota e Cassa")
    tab_mov, tab_reg = st.tabs(["Elenco Movimenti", "Registra Movimento"])
    
    with tab_mov:
        df = fetch_table("prima_nota", order_by_date=True)
        if not df.empty:
            df_table = df.drop(columns=[col for col in ['id', 'vendita_id'] if col in df.columns]).copy() if 'id' in df.columns else df.copy()
            df_table['importo'] = df_table['importo'].apply(lambda x: f"€ {x:,.2f}")
            st.dataframe(df_table, use_container_width=True)
            
            st.markdown("### ✏️ Modifica o Elimina Movimento")
            df['etichetta_pn'] = df.apply(lambda r: f"Data: {r['data']} | [{r['tipo']}] {r['descrizione']} - € {r['importo']:,.2f}", axis=1)
            mov_scelto = st.selectbox("Seleziona Movimento", df['etichetta_pn'].tolist())
            r_pn = df[df['etichetta_pn'] == mov_scelto].iloc[0]
            pn_id = int(r_pn['id'])
            
            with st.form("form_mod_pn"):
                mpn_data = st.date_input("Data", datetime.strptime(str(r_pn['data']), "%Y-%m-%d").date())
                mpn_tipo = st.selectbox("Tipo", ["Incasso", "Spesa"], index=0 if r_pn['tipo']=="Incasso" else 1)
                mpn_cat = st.text_input("Categoria", value=r_pn['categoria'])
                mpn_desc = st.text_input("Descrizione", value=r_pn['descrizione'])
                mpn_imp = st.number_input("Importo (€)", min_value=0.0, value=float(r_pn['importo']), format="%.2f")
                
                c1, c2 = st.columns(2)
                with c1:
                    b_apn = st.form_submit_button("Aggiorna Movimento", use_container_width=True)
                with c2:
                    b_dpn = st.form_submit_button("Elimina Movimento", use_container_width=True)
                    
                if b_apn:
                    supabase.table("prima_nota").update({
                        "data": str(mpn_data), "tipo": mpn_tipo, "categoria": mpn_cat,
                        "descrizione": mpn_desc, "importo": mpn_imp
                    }).eq("id", pn_id).execute()
                    st.success("Movimento aggiornato!")
                    st.rerun()
                elif b_dpn:
                    supabase.table("prima_nota").delete().eq("id", pn_id).execute()
                    st.success("Movimento eliminato!")
                    st.rerun()
        else:
            st.info("Nessun movimento registrato.")
            
    with tab_reg:
        with st.form("form_pn", clear_on_submit=True):
            data = st.date_input("Data", datetime.today())
            tipo = st.selectbox("Tipo", ["Incasso", "Spesa"])
            categoria = st.text_input("Categoria")
            descrizione = st.text_input("Descrizione")
            importo = st.number_input("Importo (€)", min_value=0.0, format="%.2f")
            
            if st.form_submit_button("Salva Movimento", use_container_width=True):
                if importo > 0:
                    supabase.table("prima_nota").insert({
                        "data": str(data), "tipo": tipo, "categoria": categoria,
                        "descrizione": descrizione, "importo": importo
                    }).execute()
                    st.success("Movimento salvato!")
                else:
                    st.error("Inserisci un importo valido.")

# ==========================================
# 6. MAGAZZINO & PRODOTTI
# ==========================================
elif scelta == "Magazzino & Prodotti":
    st.title("Gestione Magazzino")
    tab_cat, tab_add = st.tabs(["Stock a magazzino", "Aggiungi Prodotto"])
    
    with tab_cat:
        df = fetch_table("prodotti")
        if not df.empty:
            df_table = df.drop(columns=[col for col in ['id'] if col in df.columns]).copy()
            df_table['prezzo_acquisto'] = df_table['prezzo_acquisto'].apply(lambda x: f"€ {x:,.2f}")
            df_table['prezzo_vendita'] = df_table['prezzo_vendita'].apply(lambda x: f"€ {x:,.2f}")
            st.dataframe(df_table, use_container_width=True)
            
            st.markdown("### ✏️ Modifica Prodotto")
            prod_scelto = st.selectbox("Seleziona Prodotto", df['descrizione'].tolist())
            r_prod = df[df['descrizione'] == prod_scelto].iloc[0]
            p_id = int(r_prod['id'])
            
            with st.form("form_mod_prod"):
                m_codice = st.text_input("Codice", value=r_prod['codice'])
                m_desc = st.text_input("Descrizione", value=r_prod['descrizione'])
                m_pa = st.number_input("Prezzo Acquisto (€)", min_value=0.0, value=float(r_prod['prezzo_acquisto']), format="%.2f")
                m_pv = st.number_input("Prezzo Vendita (€)", min_value=0.0, value=float(r_prod['prezzo_vendita']), format="%.2f")
                m_giac = st.number_input("Giacenza", min_value=0, value=int(r_prod['giacenza']), step=1)
                
                c1, c2 = st.columns(2)
                with c1:
                    b_agg = st.form_submit_button("Aggiorna", use_container_width=True)
                with c2:
                    b_del = st.form_submit_button("Elimina", use_container_width=True)
                    
                if b_agg:
                    supabase.table("prodotti").update({
                        "codice": m_codice, "descrizione": m_desc,
                        "prezzo_acquisto": m_pa, "prezzo_vendita": m_pv, "giacenza": m_giac
                    }).eq("id", p_id).execute()
                    st.success("Prodotto aggiornato!")
                    st.rerun()
                elif b_del:
                    supabase.table("prodotti").delete().eq("id", p_id).execute()
                    st.success("Prodotto eliminato!")
                    st.rerun()
        else:
            st.info("Magazzino vuoto.")
            
    with tab_add:
        with st.form("form_prod", clear_on_submit=True):
            codice = st.text_input("Codice Articolo")
            descrizione = st.text_input("Descrizione")
            p_acquisto = st.number_input("Prezzo Acquisto (€)", min_value=0.0, format="%.2f")
            p_vendita = st.number_input("Prezzo Vendita (€)", min_value=0.0, format="%.2f")
            giacenza = st.number_input("Giacenza Iniziale", min_value=0, step=1)
            
            if st.form_submit_button("Salva Prodotto", use_container_width=True):
                if codice and descrizione:
                    supabase.table("prodotti").insert({
                        "codice": codice, "descrizione": descrizione,
                        "prezzo_acquisto": p_acquisto, "prezzo_vendita": p_vendita, "giacenza": giacenza
                    }).execute()
                    st.success("Prodotto aggiunto correttamente!")
                else:
                    st.error("Codice e descrizione obbligatori.")

# ==========================================
# 7. CONTATTI
# ==========================================
elif scelta == "Contatti (Clienti/Fornitori)":
    st.title("Anagrafica Clienti e Fornitori")
    tab_vis, tab_estratto, tab_ins = st.tabs(["Visualizza / Modifica", "🔍 Estratto Conto", "Nuovo Contatto"])
    
    with tab_vis:
        df = fetch_table("contatti")
        if not df.empty:
            df_table = df.drop(columns=[col for col in ['id'] if col in df.columns]).copy()
            st.dataframe(df_table, use_container_width=True)
            
            st.markdown("### ✏️ Modifica Contatto")
            contatto_scelto = st.selectbox("Seleziona Contatto", df['nome'].tolist(), key="sel_mod_contatto")
            riga = df[df['nome'] == contatto_scelto].iloc[0]
            id_contatto = int(riga['id'])
            
            with st.form("form_mod_contatto"):
                m_tipo = st.selectbox("Tipo", ["Cliente", "Fornitore"], index=0 if riga['tipo']=="Cliente" else 1)
                m_nome = st.text_input("Nome", value=riga['nome'])
                m_email = st.text_input("Email", value=riga['email'])
                m_tel = st.text_input("Telefono", value=riga['telefono'])
                
                c1, c2 = st.columns(2)
                with c1:
                    btn_aggiorna = st.form_submit_button("Aggiorna", use_container_width=True)
                with c2:
                    btn_elimina = st.form_submit_button("Elimina", use_container_width=True)
                
                if btn_aggiorna:
                    supabase.table("contatti").update({
                        "tipo": m_tipo, "nome": m_nome, "email": m_email, "telefono": m_tel
                    }).eq("id", id_contatto).execute()
                    st.success("Contatto aggiornato!")
                    st.rerun()
                elif btn_elimina:
                    supabase.table("contatti").delete().eq("id", id_contatto).execute()
                    st.success("Contatto eliminato!")
                    st.rerun()
        else:
            st.info("Nessun contatto.")
            
    with tab_estratto:
        st.subheader("🔍 Storico Cliente (dal più recente)")
        df_contatti = fetch_table("contatti")
        lista_clienti_estratto = df_contatti[df_contatti['tipo'].isin(['Cliente', 'Clienti'])]['nome'].tolist() if not df_contatti.empty and 'tipo' in df_contatti.columns else []
        
        if lista_clienti_estratto:
            cliente_selezionato = st.selectbox("Seleziona Cliente", options=lista_clienti_estratto)
            df_vendite_all = fetch_table("vendite", order_by_date=True)
            if not df_vendite_all.empty and 'cliente' in df_vendite_all.columns:
                df_storico = df_vendite_all[(df_vendite_all['cliente'] == cliente_selezionato) & (df_vendite_all['stato'] != 'Annullata')]
                if not df_storico.empty:
                    st.dataframe(df_storico, use_container_width=True)
                else:
                    st.info("Nessuna vendita per questo cliente.")
        else:
            st.warning("Nessun cliente in anagrafica.")

    with tab_ins:
        with st.form("form_contatto", clear_on_submit=True):
            tipo = st.selectbox("Tipo", ["Cliente", "Fornitore"])
            nome = st.text_input("Nome / Ragione Sociale")
            email = st.text_input("Email")
            telefono = st.text_input("Telefono")
            
            if st.form_submit_button("Salva Contatto", use_container_width=True):
                if nome:
                    supabase.table("contatti").insert({
                        "tipo": tipo, "nome": nome, "email": email, "telefono": telefono
                    }).execute()
                    st.success(f"Contatto '{nome}' salvato su Supabase!")
                else:
                    st.error("Il nome è obbligatorio.")
