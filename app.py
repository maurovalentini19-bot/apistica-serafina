import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configurazione della pagina
st.set_page_config(
    page_title="Apistica Serafina",
    page_icon="🐝",
    layout="wide"
)

# --- CUSTOM CSS: TEMA DELICATO & NATURALE (APICOLTURA) + FONT ACCATTIVANTE ---
st.markdown("""
    <style>
    /* Importazione font elegante per i titoli */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;1,400&display=swap');

    /* Sfondo generale dell'app caldo e naturale (effetto panna/avorio) */
    .stApp {
        background-color: #fbf9f5;
    }
    
    /* Stile delle metriche (Dashboard) */
    .stMetric {
        background-color: #ffffff;
        border: 1px solid #ebe5dc;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(44, 44, 44, 0.03);
    }
    
    /* Personalizzazione dei bottoni principali in stile "miele naturale" */
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
    
    /* Sidebar più pulita, calda e integrata */
    [data-testid="stSidebar"] {
        background-color: #f4efe6;
        border-right: 1px solid #e6e1da;
    }
    
    /* Tipografia e titoli raffinati applicati a tutte le pagine */
    h1, h2, h3 {
        font-family: 'Playfair Display', Georgia, serif;
        color: #2c2c2c;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
def get_connection():
    return sqlite3.connect("gestionale.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contatti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            nome TEXT,
            email TEXT,
            telefono TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prodotti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codice TEXT UNIQUE,
            descrizione TEXT,
            prezzo_acquisto REAL,
            prezzo_vendita REAL,
            giacenza INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendite (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            cliente TEXT,
            totale REAL,
            stato TEXT,
            articolo TEXT,
            quantita INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prima_nota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            categoria TEXT,
            descrizione TEXT,
            importo REAL,
            vendita_id INTEGER
        )
    """)
    
    cursor.execute("PRAGMA table_info(vendite)")
    colonne_vendite = [col[1] for col in cursor.fetchall()]
    if "articolo" not in colonne_vendite:
        cursor.execute("ALTER TABLE vendite ADD COLUMN articolo TEXT")
    if "quantita" not in colonne_vendite:
        cursor.execute("ALTER TABLE vendite ADD COLUMN quantita INTEGER")

    cursor.execute("PRAGMA table_info(prima_nota)")
    colonne_pn = [col[1] for col in cursor.fetchall()]
    if "vendita_id" not in colonne_pn:
        cursor.execute("ALTER TABLE prima_nota ADD COLUMN vendita_id INTEGER")

    conn.commit()
    conn.close()

init_db()

def run_query(query, params=(), fetch=True):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch:
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            return pd.DataFrame(data, columns=columns)
        else:
            conn.commit()
            conn.close()
            return True
    except sqlite3.IntegrityError as e:
        conn.close()
        return str(e)

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
st.sidebar.caption("Gestionale interno v3.0")

# ==========================================
# 1. DASHBOARD
# ==========================================
if scelta == "Dashboard":
    st.title("Apistica Serafina")
    st.markdown("Panoramica generale sull'andamento dell'attività.")
    
    df_pn = run_query("SELECT * FROM prima_nota")
    df_prod = run_query("SELECT * FROM prodotti")
    df_vendite = run_query("SELECT * FROM vendite")
    
    incassi = df_pn[df_pn['tipo'] == 'Incasso']['importo'].sum() if not df_pn.empty else 0.0
    spese = df_pn[df_pn['tipo'] == 'Spesa']['importo'].sum() if not df_pn.empty else 0.0
    utile = incassi - spese
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Totale Incassi", f"€ {incassi:,.2f}")
    c2.metric("📉 Totale Spese", f"€ {spese:,.2f}")
    c3.metric("📈 Utile Corrente", f"€ {utile:,.2f}")
    
    valore_mag = (df_prod['prezzo_acquisto'] * df_prod['giacenza']).sum() if not df_prod.empty else 0.0
    c4.metric("📦 Valore Magazzino", f"€ {valore_mag:,.2f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📦 Stock a magazzino", "🛒 Report Vendite", "💶 Report Cassa"])
    
    with tab1:
        st.subheader("Stock a magazzino")
        if not df_prod.empty:
            df_disp = df_prod.drop(columns=['id']).copy()
            df_disp['prezzo_acquisto'] = df_disp['prezzo_acquisto'].apply(lambda x: f"€ {x:,.2f}")
            df_disp['prezzo_vendita'] = df_disp['prezzo_vendita'].apply(lambda x: f"€ {x:,.2f}")
            df_disp['Valore Vendita Totale'] = (df_prod['prezzo_vendita'] * df_prod['giacenza']).apply(lambda x: f"€ {x:,.2f}")
            st.dataframe(df_disp, use_container_width=True)
        else:
            st.info("Nessun prodotto disponibile.")
            
    with tab2:
        st.subheader("Elenco Vendite")
        if not df_vendite.empty:
            df_disp = df_vendite.drop(columns=['id']).copy()
            df_disp['totale'] = df_disp['totale'].apply(lambda x: f"€ {x:,.2f}")
            st.dataframe(df_disp, use_container_width=True)
        else:
            st.info("Nessuna vendita registrata.")
            
    with tab3:
        st.subheader("Movimenti Prima Nota")
        if not df_pn.empty:
            df_disp = df_pn.drop(columns=[col for col in ['id', 'vendita_id'] if col in df_pn.columns]).copy()
            df_disp['importo'] = df_disp['importo'].apply(lambda x: f"€ {x:,.2f}")
            st.dataframe(df_disp, use_container_width=True)
        else:
            st.info("Nessun movimento registrato.")

# ==========================================
# 2. REPORT & ANALISI (CON FILTRI E DRILL-DOWN)
# ==========================================
elif scelta == "Report & Analisi":
    st.title("Report & Analisi Statistiche")
    st.markdown("Filtra per intervallo di date, visualizza i totali specifici della selezione ed esplodi i singoli movimenti.")
    
    tab_rep_vendite, tab_rep_cassa, tab_rep_mag = st.tabs(["🍯 Vendite per Prodotto", "💶 Analisi Cassa & Spese", "📦 Valore Potenziale Magazzino"])
    
    with tab_rep_vendite:
        st.subheader("Riepilogo Quantità e Fatturato per Articolo")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            data_inizio_v = st.date_input("Data Inizio (Vendite)", datetime(datetime.today().year, 1, 1), key="rep_v_1")
        with col_f2:
            data_fine_v = st.date_input("Data Fine (Vendite)", datetime.today(), key="rep_v_2")
            
        query_v = """
            SELECT articolo, SUM(quantita) as qta_totale, SUM(totale) as fatturato_totale 
            FROM vendite 
            WHERE stato != 'Annullata' AND articolo IS NOT NULL AND data BETWEEN ? AND ?
            GROUP BY articolo
            ORDER BY fatturato_totale DESC
        """
        df_v = run_query(query_v, (str(data_inizio_v), str(data_fine_v)))
        
        if not df_v.empty:
            tot_fatturato_sel = df_v['fatturato_totale'].sum()
            tot_qta_sel = df_v['qta_totale'].sum()
            
            mk1, mk2 = st.columns(2)
            mk1.metric("💰 Fatturato Selezionato", f"€ {tot_fatturato_sel:,.2f}")
            mk2.metric("📦 Quantità Totale Venduta", f"{int(tot_qta_sel)} pz")
            st.markdown("<br>", unsafe_allow_html=True)

            # --- REPORT: CLIENTE – FATTURATO (SPOSTATO SOPRA LA TABELLA RIEPILOGATIVA) ---
            st.markdown("### 👥 Report: Cliente – Fatturato")
            st.caption("Elenco dei clienti ordinati per fatturato decrescente nel periodo selezionato.")
            
            query_cli_rep = """
                SELECT cliente, SUM(totale) as fatturato_cliente, SUM(quantita) as qta_totale_cliente
                FROM vendite 
                WHERE stato != 'Annullata' AND cliente IS NOT NULL AND data BETWEEN ? AND ?
                GROUP BY cliente
                ORDER BY fatturato_cliente DESC
            """
            df_cli_rep = run_query(query_cli_rep, (str(data_inizio_v), str(data_fine_v)))
            
            if not df_cli_rep.empty:
                tot_fatt_cli = df_cli_rep['fatturato_cliente'].sum()
                tot_qta_cli = df_cli_rep['qta_totale_cliente'].sum()
                
                riga_tot_cli = pd.DataFrame({
                    'cliente': ['--- TOTALE COMPLESSIVO ---'],
                    'fatturato_cliente': [tot_fatt_cli],
                    'qta_totale_cliente': [int(tot_qta_cli)]
                })
                df_cli_rep_full = pd.concat([df_cli_rep, riga_tot_cli], ignore_index=True)
                df_cli_rep_full['fatturato_cliente_fmt'] = df_cli_rep_full['fatturato_cliente'].apply(lambda x: f"€ {x:,.2f}")
                
                df_cli_show = df_cli_rep_full[['cliente', 'qta_totale_cliente', 'fatturato_cliente_fmt']].copy()
                df_cli_show.columns = ['Cliente', 'Pezzi Acquistati Totali', 'Fatturato']
                st.dataframe(df_cli_show, use_container_width=True)
            else:
                st.info("Nessun dato cliente disponibile per il periodo selezionato.")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- TABELLA RIEPILOGATIVA PER ARTICOLO (ORDINATA PER FATTURATO DECRESCENTE) ---
            st.markdown("### 📋 Tabella Riepilogativa per Articolo")
            
            df_v_display = df_v.copy()
            df_v_display['prezzo_medio'] = df_v_display['fatturato_totale'] / df_v_display['qta_totale']
            
            # Riga Totale da aggiungere in fondo
            media_ponderata_totale = tot_fatturato_sel / tot_qta_sel if tot_qta_sel > 0 else 0.0
            riga_totale = pd.DataFrame({
                'articolo': ['--- TOTALE / MEDIA ---'],
                'qta_totale': [int(tot_qta_sel)],
                'fatturato_totale': [tot_fatturato_sel],
                'prezzo_medio': [media_ponderata_totale]
            })
            df_v_display_full = pd.concat([df_v_display, riga_totale], ignore_index=True)
            
            # Formattazione valute per la visualizzazione
            df_v_display_full['fatturato_totale_fmt'] = df_v_display_full['fatturato_totale'].apply(lambda x: f"€ {x:,.2f}")
            df_v_display_full['prezzo_medio_fmt'] = df_v_display_full['prezzo_medio'].apply(lambda x: f"€ {x:,.2f}")
            
            df_table_show = df_v_display_full[['articolo', 'qta_totale', 'prezzo_medio_fmt', 'fatturato_totale_fmt']].copy()
            df_table_show.columns = ['Articolo', 'Quantità Totale', 'Prezzo Medio di Vendita', 'Fatturato Totale']
            st.dataframe(df_table_show, use_container_width=True)

            st.markdown("---")

            # --- DRILL-DOWN VENDITE (ESPLOSIONE MOVIMENTI) ---
            st.markdown("### 🔍 Esplosione Movimenti Vendita per Articolo")
            st.caption("Seleziona un articolo per visualizzare l'elenco analitico di tutte le vendite collegate nel periodo.")
            
            lista_articoli_drill = df_v['articolo'].dropna().unique().tolist()
            articolo_scelto_drill = st.selectbox("Seleziona Articolo da esplodere", options=lista_articoli_drill)
            if articolo_scelto_drill:
                query_drill_v = """
                    SELECT data, cliente, tipo, stato, quantita, totale 
                    FROM vendite 
                    WHERE articolo = ? AND data BETWEEN ? AND ?
                    ORDER BY data DESC
                """
                df_d_v = run_query(query_drill_v, (articolo_scelto_drill, str(data_inizio_v), str(data_fine_v)))
                if not df_d_v.empty:
                    st.info(f"Trovate {len(df_d_v)} operazioni per **{articolo_scelto_drill}** nel periodo selezionato.")
                    df_d_v_disp = df_d_v.copy()
                    df_d_v_disp['totale'] = df_d_v_disp['totale'].apply(lambda x: f"€ {x:,.2f}")
                    st.dataframe(df_d_v_disp, use_container_width=True)
                else:
                    st.warning("Nessuna transazione per questo articolo nel periodo selezionato.")

            st.markdown("---")
            st.markdown("### 📊 Grafico Fatturato per Articolo")
            df_grafico = df_v.set_index('articolo')['fatturato_totale']
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
            
        query_pn = """
            SELECT tipo, categoria, SUM(importo) as totale_importo 
            FROM prima_nota 
            WHERE data BETWEEN ? AND ?
            GROUP BY tipo, categoria
        """
        df_pn_rep = run_query(query_pn, (str(data_inizio_pn), str(data_fine_pn)))
        
        if not df_pn_rep.empty:
            inc_periodo = df_pn_rep[df_pn_rep['tipo'] == 'Incasso']['totale_importo'].sum()
            spe_periodo = df_pn_rep[df_pn_rep['tipo'] == 'Spesa']['totale_importo'].sum()
            uti_periodo = inc_periodo - spe_periodo
            
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("💰 Incassi nel periodo", f"€ {inc_periodo:,.2f}")
            mc2.metric("📉 Spese nel periodo", f"€ {spe_periodo:,.2f}")
            mc3.metric("📈 Saldo del periodo", f"€ {uti_periodo:,.2f}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            df_pn_rep_display = df_pn_rep.copy()
            df_pn_rep_display['totale_importo'] = df_pn_rep_display['totale_importo'].apply(lambda x: f"€ {x:,.2f}")
            st.dataframe(df_pn_rep_display, use_container_width=True)
            
            # --- DRILL-DOWN CASSA ---
            st.markdown("---")
            st.markdown("### 🔍 Esplosione Dettaglio Movimenti di Cassa")
            st.caption("Seleziona una categoria per visualizzare tutti i singoli movimenti registrati nel periodo.")
            
            cat_uniche = df_pn_rep['categoria'].dropna().unique().tolist()
            cat_scelta_drill = st.selectbox("Seleziona Categoria da esplodere", options=cat_uniche)
            
            if cat_scelta_drill:
                query_drill_c = """
                    SELECT data, tipo, descrizione, importo 
                    FROM prima_nota 
                    WHERE categoria = ? AND data BETWEEN ? AND ?
                    ORDER BY data DESC
                """
                df_d_c = run_query(query_drill_c, (cat_scelta_drill, str(data_inizio_pn), str(data_fine_pn)))
                if not df_d_c.empty:
                    st.info(f"Trovati {len(df_d_c)} movimenti per la categoria **{cat_scelta_drill}**.")
                    df_d_c_disp = df_d_c.copy()
                    df_d_c_disp['importo'] = df_d_c_disp['importo'].apply(lambda x: f"€ {x:,.2f}")
                    st.dataframe(df_d_c_disp, use_container_width=True)
                else:
                    st.warning("Nessun movimento trovato per questa categoria nel periodo.")
        else:
            st.info("Nessun movimento registrato in prima nota nel periodo selezionato.")
            
    with tab_rep_mag:
        st.subheader("Analisi Valore Magazzino a Prezzo di Vendita")
        st.caption("Il magazzino riflette lo stock attuale in tempo reale (non soggetto a filtro storico).")
        
        df_pm = run_query("SELECT codice, descrizione, prezzo_acquisto, prezzo_vendita, giacenza FROM prodotti")
        if not df_pm.empty:
            df_pm['Valore d\'Acquisto Totale'] = df_pm['prezzo_acquisto'] * df_pm['giacenza']
            df_pm['Valore di Vendita Potenziale'] = df_pm['prezzo_vendita'] * df_pm['giacenza']
            
            tot_acq = df_pm['Valore d\'Acquisto Totale'].sum()
            tot_vend = df_pm['Valore di Vendita Potenziale'].sum()
            
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("📦 Valore Totale Acquisto/Produzione", f"€ {tot_acq:,.2f}")
            col_m2.metric("💰 Valore Potenziale di Vendita", f"€ {tot_vend:,.2f}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            df_pm_disp = df_pm.copy()
            df_pm_disp['prezzo_acquisto'] = df_pm_disp['prezzo_acquisto'].apply(lambda x: f"€ {x:,.2f}")
            df_pm_disp['prezzo_vendita'] = df_pm_disp['prezzo_vendita'].apply(lambda x: f"€ {x:,.2f}")
            df_pm_disp['Valore d\'Acquisto Totale'] = df_pm_disp['Valore d\'Acquisto Totale'].apply(lambda x: f"€ {x:,.2f}")
            df_pm_disp['Valore di Vendita Potenziale'] = df_pm_disp['Valore di Vendita Potenziale'].apply(lambda x: f"€ {x:,.2f}")
            st.dataframe(df_pm_disp, use_container_width=True)
        else:
            st.info("Magazzino vuoto.")

# ==========================================
# 3. VENDITE (NUOVA, MODIFICA E ELENCO)
# ==========================================
elif scelta == "Vendite":
    st.title("Gestione Vendite")
    
    tab_inserimento, tab_modifica, tab_elenco = st.tabs(["Nuova Vendita", "Modifica / Elimina Vendita", "Elenco Vendite"])
    
    with tab_elenco:
        df = run_query("SELECT * FROM vendite")
        if not df.empty:
            df_table = df.drop(columns=['id']).copy()
            df_table['totale'] = df_table['totale'].apply(lambda x: f"€ {x:,.2f}")
            st.dataframe(df_table, use_container_width=True)
        else:
            st.info("Nessuna vendita presente.")
            
    with tab_modifica:
        st.subheader("✏️ Modifica o Annulla Vendita Esistente")
        st.caption("Seleziona una vendita per correggere i dati, modificare il prezzo applicato (es. sconti) o eliminare l'operazione ripristinando il magazzino.")
        
        df_vendite_mod = run_query("SELECT * FROM vendite")
        if not df_vendite_mod.empty:
            df_vendite_mod['etichetta_scelta'] = df_vendite_mod.apply(lambda r: f"ID:{r['id']} | Data: {r['data']} | Cliente: {r['cliente']} | Articolo: {r['articolo']} (Qt: {r['quantita']}) - Tot: € {r['totale']:,.2f}", axis=1)
            
            vendita_selezionata_str = st.selectbox("Seleziona Vendita da modificare/eliminare", df_vendite_mod['etichetta_scelta'].tolist(), key="sel_vend_mod_box")
            r_vend_sel = df_vendite_mod[df_vendite_mod['etichetta_scelta'] == vendita_selezionata_str].iloc[0]
            v_id_edit = int(r_vend_sel['id'])
            
            df_clienti = run_query("SELECT nome FROM contatti WHERE tipo = 'Cliente' OR tipo = 'Clienti'")
            lista_clienti_edit = df_clienti['nome'].tolist() if not df_clienti.empty else []
            
            with st.form("form_modifica_vendita_dettaglio"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    m_data = st.date_input("Data Vendita", datetime.strptime(r_vend_sel['data'], "%Y-%m-%d").date())
                with ec2:
                    m_tipo_op = st.selectbox("Tipo operazione", ["Vendita", "Reso"], index=0 if r_vend_sel['tipo']=="Vendita" else 1)
                
                if lista_clienti_edit and r_vend_sel['cliente'] in lista_clienti_edit:
                    idx_cli = lista_clienti_edit.index(r_vend_sel['cliente'])
                else:
                    idx_cli = 0
                m_cliente = st.selectbox("Cliente", options=lista_clienti_edit if lista_clienti_edit else [r_vend_sel['cliente']], index=idx_cli)
                
                df_prodotti_all = run_query("SELECT id, descrizione, prezzo_vendita, giacenza FROM prodotti")
                lista_prod_edit = df_prodotti_all['descrizione'].tolist() if not df_prodotti_all.empty else []
                
                art_attuale = r_vend_sel['articolo']
                idx_prod = lista_prod_edit.index(art_attuale) if art_attuale in lista_prod_edit else 0
                m_articolo = st.selectbox("Articolo", options=lista_prod_edit, index=idx_prod)
                
                ec_q, ec_p = st.columns(2)
                with ec_q:
                    m_quantita = st.number_input("Quantità", min_value=1, value=int(r_vend_sel['quantita']), step=1)
                
                prezzo_iniziale_edit = float(r_vend_sel['totale']) / int(r_vend_sel['quantita']) if int(r_vend_sel['quantita']) > 0 else 0.0
                with ec_p:
                    m_prezzo_unitario = st.number_input("Prezzo Unitario (€) [Modificabile]", min_value=0.0, value=prezzo_iniziale_edit, step=0.10, format="%.2f")
                
                st.caption(f"💶 Totale ricalcolato: € {m_prezzo_unitario * m_quantita:,.2f}")
                
                stati_possibili = ["Emessa", "Pagata", "Annullata"]
                idx_st = stati_possibili.index(r_vend_sel['stato']) if r_vend_sel['stato'] in stati_possibili else 1
                m_stato = st.selectbox("Stato pagamento/ordine", stati_possibili, index=idx_st)
                
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
                    
                    if vecchio_articolo:
                        df_p_v = run_query("SELECT id, giacenza FROM prodotti WHERE descrizione = ?", (vecchio_articolo,))
                        if not df_p_v.empty:
                            id_p_v = int(df_p_v.iloc[0]['id'])
                            giac_v = int(df_p_v.iloc[0]['giacenza'])
                            ripr_giac = giac_v + vecchia_qta if vecchio_tipo == "Vendita" else giac_v - vecchia_qta
                            run_query("UPDATE prodotti SET giacenza = ? WHERE id = ?", (ripr_giac, id_p_v), fetch=False)
                    
                    df_p_n = run_query("SELECT id, giacenza FROM prodotti WHERE descrizione = ?", (m_articolo,))
                    if not df_p_n.empty:
                        id_p_n = int(df_p_n.iloc[0]['id'])
                        giac_n = int(df_p_n.iloc[0]['giacenza'])
                        nuova_giac = giac_n - m_quantita if m_tipo_op == "Vendita" else giac_n + m_quantita
                        run_query("UPDATE prodotti SET giacenza = ? WHERE id = ?", (nuova_giac, id_p_n), fetch=False)
                    
                    nuovo_totale = m_prezzo_unitario * m_quantita
                    
                    run_query("UPDATE vendite SET data = ?, tipo = ?, cliente = ?, totale = ?, stato = ?, articolo = ?, quantita = ? WHERE id = ?",
                              (str(m_data), m_tipo_op, m_cliente, nuovo_totale, m_stato, m_articolo, m_quantita, v_id_edit), fetch=False)
                    
                    run_query("DELETE FROM prima_nota WHERE vendita_id = ?", (v_id_edit,), fetch=False)
                    if m_stato != "Annullata":
                        cat_pn = "Vendite" if m_tipo_op == "Vendita" else "Resi"
                        desc_pn = f"{m_tipo_op} - {m_cliente} - {m_articolo} (x{m_quantita})"
                        tipo_pn = "Incasso" if m_tipo_op == "Vendita" else "Spesa"
                        run_query("INSERT INTO prima_nota (data, tipo, categoria, descrizione, importo, vendita_id) VALUES (?, ?, ?, ?, ?, ?)",
                                  (str(m_data), tipo_pn, cat_pn, desc_pn, nuovo_totale, v_id_edit), fetch=False)
                    
                    st.success("✅ Vendita modificata con successo! Magazzino e Prima Nota aggiornati.")
                    st.rerun()
                    
                elif btn_elimina_vend:
                    art_venduto = r_vend_sel['articolo']
                    qta_venduta = r_vend_sel['quantita']
                    tipo_vendita = r_vend_sel['tipo']
                    
                    if art_venduto and qta_venduta:
                        df_p_check = run_query("SELECT id, giacenza FROM prodotti WHERE descrizione = ?", (art_venduto,))
                        if not df_p_check.empty:
                            p_id_mag = int(df_p_check.iloc[0]['id'])
                            giac_att = int(df_p_check.iloc[0]['giacenza'])
                            nuova_giac = giac_att + int(qta_venduta) if tipo_vendita == "Vendita" else giac_att - int(qta_venduta)
                            run_query("UPDATE prodotti SET giacenza = ? WHERE id = ?", (nuova_giac, p_id_mag), fetch=False)
                    
                    run_query("DELETE FROM prima_nota WHERE vendita_id = ?", (v_id_edit,), fetch=False)
                    run_query("DELETE FROM vendite WHERE id = ?", (v_id_edit,), fetch=False)
                    
                    st.success("✅ Vendita eliminata! Magazzino ripristinato e Prima Nota aggiornata.")
                    st.rerun()
        else:
            st.info("Nessuna vendita disponibile da modificare.")
            
    with tab_inserimento:
        df_clienti = run_query("SELECT nome FROM contatti WHERE tipo = 'Cliente' OR tipo = 'Clienti'")
        lista_clienti = df_clienti['nome'].tolist() if not df_clienti.empty else []
        
        df_prodotti = run_query("SELECT id, descrizione, prezzo_vendita, giacenza FROM prodotti")
        
        if st.session_state.get("show_success", False):
            st.success("✅ Vendita registrata con successo! Magazzino e Prima Nota aggiornati.")
            st.session_state.show_success = False

        col_a, col_b = st.columns(2)
        with col_a:
            data = st.date_input("Data", datetime.today(), key="v_data")
        with col_b:
            tipo = st.selectbox("Tipo operazione", ["Vendita", "Reso"], key="v_tipo")
        
        if lista_clienti:
            cliente = st.selectbox("Cliente *", options=lista_clienti, index=None, placeholder="Seleziona un cliente...", key="v_cliente")
        else:
            cliente = st.text_input("Cliente * (Nessun cliente in anagrafica, digita nome)", key="v_cliente_txt")
            
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
                
                with col_p:
                    prezzo_unitario = st.number_input(
                        "Prezzo Unitario (€) [Modificabile per sconti]", 
                        min_value=0.0, 
                        value=prezzo_default, 
                        step=0.10, 
                        format="%.2f", 
                        key="v_prezzo_mod"
                    )
                
                st.caption(f"🏷️ Listino standard anagrafica: € {prezzo_default:,.2f} | 📦 Giacenza attuale: **{giacenza_disponibile} pz**")
                
                totale_calcolato = prezzo_unitario * quantita
                st.markdown(f"### 💶 Totale Complessivo: **€ {totale_calcolato:,.2f}**")
            else:
                with col_p:
                    st.info("Seleziona un prodotto per abilitare il prezzo.")
                st.info("👈 Seleziona un prodotto per visualizzare e modificare il prezzo unitario.")
        else:
            st.warning("Nessun prodotto disponibile in magazzino. Inserisci prima i prodotti nella sezione Magazzino.")
            
        stato = st.selectbox("Stato pagamento/ordine", ["Emessa", "Pagata", "Annullata"], index=1, key="v_stato")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Registra Vendita", type="primary", use_container_width=True):
            cli_val = st.session_state.get("v_cliente") if lista_clienti else st.session_state.get("v_cliente_txt")
            art_val = st.session_state.get("v_prodotto")
            qta_val = st.session_state.get("v_qta", 1)
            prezzo_finale_unitario = st.session_state.get("v_prezzo_mod", 0.0)
            totale_finale = prezzo_finale_unitario * qta_val
            
            if not cli_val or not art_val:
                st.error("⚠️ Errore: I campi 'Cliente' e 'Prodotto' sono obbligatori! Selezionali prima di registrare.")
            else:
                prod_info = df_prodotti[df_prodotti['descrizione'] == art_val].iloc[0]
                prod_id = int(prod_info['id'])
                giacenza_attuale = int(prod_info['giacenza'])
                
                if tipo == "Vendita" and qta_val > giacenza_attuale:
                    st.error(f"⚠️ Attenzione: Quantità richiesta ({qta_val}) superiore alla giacenza disponibile ({giacenza_attuale} pz)!")
                else:
                    descrizione_vendita = f"{art_val} (x{qta_val})"
                    
                    cursor_ins = get_connection()
                    cur = cursor_ins.cursor()
                    cur.execute("INSERT INTO vendite (data, tipo, cliente, totale, stato, articolo, quantita) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (str(data), tipo, cli_val, totale_finale, stato, art_val, int(qta_val)))
                    id_vendita_creata = cur.lastrowid
                    cursor_ins.commit()
                    cursor_ins.close()
                    
                    if tipo == "Vendita":
                        nuova_giacenza = giacenza_attuale - int(qta_val)
                    else:
                        nuova_giacenza = giacenza_attuale + int(qta_val)
                        
                    run_query("UPDATE prodotti SET giacenza = ? WHERE id = ?", (nuova_giacenza, prod_id), fetch=False)
                    
                    if stato != "Annullata":
                        cat_pn = "Vendite" if tipo == "Vendita" else "Resi"
                        desc_pn = f"{tipo} - {cli_val} - {descrizione_vendita}"
                        tipo_pn = "Incasso" if tipo == "Vendita" else "Spesa"
                        
                        run_query("INSERT INTO prima_nota (data, tipo, categoria, descrizione, importo, vendita_id) VALUES (?, ?, ?, ?, ?, ?)",
                                  (str(data), tipo_pn, cat_pn, desc_pn, totale_finale, id_vendita_creata), fetch=False)
                    
                    keys_to_clear = ["v_cliente", "v_cliente_txt", "v_prodotto", "v_qta", "v_prezzo_mod"]
                    for k in keys_to_clear:
                        if k in st.session_state:
                            del st.session_state[k]
                            
                    st.session_state.show_success = True
                    st.rerun()

# ==========================================
# 4. CARICO MERCI (SMIELATURA)
# ==========================================
elif scelta == "Carico Merci (Smielatura)":
    st.title("Carico Merci e Smielatura")
    st.markdown("Registra l'ingresso di nuovi barattoli o prodotti derivanti dalla smielatura per aggiornare automaticamente la giacenza in magazzino.")
    
    df_prodotti = run_query("SELECT id, descrizione, giacenza FROM prodotti")
    
    if not df_prodotti.empty:
        with st.form("form_smielatura", clear_on_submit=True):
            data_carico = st.date_input("Data Smielatura / Carico", datetime.today())
            
            lista_prod = df_prodotti['descrizione'].tolist()
            prodotto_scelto = st.selectbox("Prodotto da caricare *", options=lista_prod, placeholder="Seleziona prodotto...")
            
            quantita_carico = st.number_input("Quantità prodotta / caricata (pezzi o unità)", min_value=1, value=10, step=1)
            
            st.markdown("---")
            st.markdown("#### 💶 Eventuali Costi di Lavorazione (Opzionale)")
            st.caption("Se hai sostenuto spese per la smielatura e vuoi registrarle subito in Prima Nota, compila i campi sottostanti. Altrimenti lascia a zero.")
            
            registra_spesa = st.checkbox("Registra costo anche in Prima Nota (Spesa)")
            importo_spesa = st.number_input("Costo sostenuto (€)", min_value=0.0, format="%.2f")
            descrizione_spesa = st.text_input("Descrizione spesa (es. Lavorazione smielatura, vasetti, etichette)", value="Costi smielatura")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("🍯 Conferma e Carica in Magazzino", use_container_width=True):
                if prodotto_scelto and quantita_carico > 0:
                    prod_info = df_prodotti[df_prodotti['descrizione'] == prodotto_scelto].iloc[0]
                    prod_id = int(prod_info['id'])
                    giacenza_attuale = int(prod_info['giacenza'])
                    
                    nuova_giacenza = giacenza_attuale + int(quantita_carico)
                    
                    run_query("UPDATE prodotti SET giacenza = ? WHERE id = ?", (nuova_giacenza, prod_id), fetch=False)
                    
                    if registra_spesa and importo_spesa > 0:
                        run_query(
                            "INSERT INTO prima_nota (data, tipo, categoria, descrizione, importo) VALUES (?, ?, ?, ?, ?)",
                            (str(data_carico), "Spesa", "Smielatura/Produzione", f"{descrizione_spesa} - {prodotto_scelto} (+{quantita_carico} pz)", importo_spesa),
                            fetch=False
                        )
                    
                    st.success(f"✅ Carico effettuato con successo! Aggiunti {quantita_carico} pezzi di '{prodotto_scelto}'. Nuova giacenza: {nuova_giacenza} pz.")
                else:
                    st.error("Seleziona un prodotto valido e una quantità maggiore di zero.")
    else:
        st.warning("⚠️ Nessun prodotto presente in magazzino. Vai prima nella sezione 'Magazzino & Prodotti' per censire i prodotti.")

# ==========================================
# 5. PRIMA NOTA
# ==========================================
elif scelta == "Prima Nota (Cassa)":
    st.title("Prima Nota e Cassa")
    
    tab_mov, tab_reg = st.tabs(["Elenco Movimenti", "Registra Movimento"])
    
    with tab_mov:
        df = run_query("SELECT * FROM prima_nota")
        if not df.empty:
            df_table = df.drop(columns=[col for col in ['id', 'vendita_id'] if col in df.columns]).copy()
            df_table['importo'] = df_table['importo'].apply(lambda x: f"€ {x:,.2f}")
            st.dataframe(df_table, use_container_width=True)
            
            st.markdown("### ✏️ Modifica o Elimina Movimento")
            df['etichetta_pn'] = df.apply(lambda r: f"Data: {r['data']} | [{r['tipo']}] {r['descrizione']} - € {r['importo']:,.2f}", axis=1)
            
            mov_scelto = st.selectbox("Seleziona Movimento", df['etichetta_pn'].tolist())
            r_pn = df[df['etichetta_pn'] == mov_scelto].iloc[0]
            pn_id = int(r_pn['id'])
            
            with st.form("form_mod_pn"):
                mpn_data = st.date_input("Data", datetime.strptime(r_pn['data'], "%Y-%m-%d").date())
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
                    run_query("UPDATE prima_nota SET data=?, tipo=?, categoria=?, descrizione=?, importo=? WHERE id=?",
                              (str(mpn_data), mpn_tipo, mpn_cat, mpn_desc, mpn_imp, pn_id), fetch=False)
                    st.success("Movimento aggiornato!")
                    st.rerun()
                elif b_dpn:
                    run_query("DELETE FROM prima_nota WHERE id=?", (pn_id,), fetch=False)
                    st.success("Movimento eliminato!")
                    st.rerun()
        else:
            st.info("Nessun movimento registrato.")
            
    with tab_reg:
        with st.form("form_pn", clear_on_submit=True):
            data = st.date_input("Data", datetime.today())
            tipo = st.selectbox("Tipo", ["Incasso", "Spesa"])
            categoria = st.text_input("Categoria (es. Merci, Affitto, Utenze)")
            descrizione = st.text_input("Descrizione")
            importo = st.number_input("Importo (€)", min_value=0.0, format="%.2f")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Salva Movimento in Cassa", use_container_width=True):
                if importo > 0:
                    run_query("INSERT INTO prima_nota (data, tipo, categoria, descrizione, importo) VALUES (?, ?, ?, ?, ?)",
                              (str(data), tipo, categoria, descrizione, importo), fetch=False)
                    st.success("Movimento salvato in cassa!")
                else:
                    st.error("Inserisci un importo valido.")

# ==========================================
# 6. MAGAZZINO & PRODOTTI
# ==========================================
elif scelta == "Magazzino & Prodotti":
    st.title("Gestione Magazzino")
    
    tab_cat, tab_add = st.tabs(["Stock a magazzino", "Aggiungi Prodotto"])
    
    with tab_cat:
        df = run_query("SELECT * FROM prodotti")
        if not df.empty:
            df_table = df.drop(columns=['id']).copy()
            df_table['prezzo_acquisto'] = df_table['prezzo_acquisto'].apply(lambda x: f"€ {x:,.2f}")
            df_table['prezzo_vendita'] = df_table['prezzo_vendita'].apply(lambda x: f"€ {x:,.2f}")
            st.dataframe(df_table, use_container_width=True)
            
            st.markdown("### ✏️ Modifica o Correzione Rapida Prodotto")
            
            prod_scelto = st.selectbox(
                "Seleziona Prodotto", 
                df['descrizione'].tolist(), 
                format_func=lambda x: f"{df[df['descrizione']==x]['codice'].values[0]} - {x} (Giacenza: {df[df['descrizione']==x]['giacenza'].values[0]} pz)"
            )
            r_prod = df[df['descrizione'] == prod_scelto].iloc[0]
            p_id = int(r_prod['id'])
            
            with st.form("form_mod_prod"):
                m_codice = st.text_input("Codice Articolo", value=r_prod['codice'])
                m_desc = st.text_input("Descrizione", value=r_prod['descrizione'])
                m_pa = st.number_input("Prezzo Acquisto (€)", min_value=0.0, value=float(r_prod['prezzo_acquisto']), format="%.2f")
                m_pv = st.number_input("Prezzo Vendita (€)", min_value=0.0, value=float(r_prod['prezzo_vendita']), format="%.2f")
                m_giac = st.number_input("Giacenza (Correzione manuale)", min_value=0, value=int(r_prod['giacenza']), step=1)
                
                c1, c2 = st.columns(2)
                with c1:
                    b_agg = st.form_submit_button("Aggiorna Prodotto", use_container_width=True)
                with c2:
                    b_del = st.form_submit_button("Elimina Prodotto", use_container_width=True)
                    
                if b_agg:
                    res = run_query("UPDATE prodotti SET codice=?, descrizione=?, prezzo_acquisto=?, prezzo_vendita=?, giacenza=? WHERE id=?",
                                    (m_codice, m_desc, m_pa, m_pv, m_giac, p_id), fetch=False)
                    if res is True:
                        st.success("Prodotto e giacenza aggiornati con successo!")
                        st.rerun()
                    else:
                        st.error("Errore: Il codice articolo esiste già per un altro prodotto.")
                elif b_del:
                    run_query("DELETE FROM prodotti WHERE id=?", (p_id,), fetch=False)
                    st.success("Prodotto eliminato!")
                    st.rerun()
        else:
            st.info("Il magazzino è vuoto.")
            
    with tab_add:
        with st.form("form_prod", clear_on_submit=True):
            codice = st.text_input("Codice Articolo")
            descrizione = st.text_input("Descrizione")
            p_acquisto = st.number_input("Prezzo Acquisto (€)", min_value=0.0, format="%.2f")
            p_vendita = st.number_input("Prezzo Vendita (€)", min_value=0.0, format="%.2f")
            giacenza = st.number_input("Giacenza Iniziale", min_value=0, step=1)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Salva Nuovo Prodotto", use_container_width=True):
                if codice and descrizione:
                    res = run_query("INSERT INTO prodotti (codice, descrizione, prezzo_acquisto, prezzo_vendita, giacenza) VALUES (?, ?, ?, ?, ?)",
                              (codice, descrizione, p_acquisto, p_vendita, giacenza), fetch=False)
                    if res is True:
                        st.success("Prodotto aggiunto correttamente!")
                    else:
                        st.error("Errore: Esiste già un prodotto con questo Codice Articolo!")
                else:
                    st.error("Codice e descrizione sono obbligatori.")

# ==========================================
# 7. CONTATTI
# ==========================================
elif scelta == "Contatti (Clienti/Fornitori)":
    st.title("Anagrafica Clienti e Fornitori")
    
    tab_vis, tab_estratto, tab_ins = st.tabs(["Visualizza / Modifica / Elimina", "🔍 Estratto Conto & Storico Cliente", "Nuovo Contatto"])
    
    with tab_vis:
        df = run_query("SELECT * FROM contatti")
        if not df.empty:
            df_table = df.drop(columns=['id']).copy()
            st.dataframe(df_table, use_container_width=True)
            
            st.markdown("### ✏️ Modifica o Elimina Contatto")
            
            contatto_scelto = st.selectbox(
                "Seleziona Contatto", 
                df['nome'].tolist(), 
                format_func=lambda x: f"[{df[df['nome']==x]['tipo'].values[0]}] {x}",
                key="sel_mod_contatto"
            )
            riga = df[df['nome'] == contatto_scelto].iloc[0]
            id_contatto = int(riga['id'])
            
            with st.form("form_mod_contatto"):
                m_tipo = st.selectbox("Tipo", ["Cliente", "Fornitore"], index=0 if riga['tipo']=="Cliente" else 1)
                m_nome = st.text_input("Nome / Ragione Sociale", value=riga['nome'])
                m_email = st.text_input("Email", value=riga['email'])
                m_tel = st.text_input("Telefono", value=riga['telefono'])
                
                col1, col2 = st.columns(2)
                with col1:
                    btn_aggiorna = st.form_submit_button("Aggiorna Contatto", use_container_width=True)
                with col2:
                    btn_elimina = st.form_submit_button("Elimina Contatto", use_container_width=True)
                
                if btn_aggiorna:
                    run_query("UPDATE contatti SET tipo=?, nome=?, email=?, telefono=? WHERE id=?", 
                              (m_tipo, m_nome, m_email, m_tel, id_contatto), fetch=False)
                    st.success("Contatto aggiornato con successo!")
                    st.rerun()
                elif btn_elimina:
                    run_query("DELETE FROM contatti WHERE id = ?", (id_contatto,), fetch=False)
                    st.success("Contatto eliminato!")
                    st.rerun()
        else:
            st.info("Nessun contatto inserito.")
            
    with tab_estratto:
        st.subheader("🔍 Storico Acquisti e Prodotti per Cliente")
        st.caption("Seleziona un cliente per visualizzare l'estratto conto completo e l'esploso di tutti i prodotti acquistati.")
        
        df_clienti_solo = run_query("SELECT nome FROM contatti WHERE tipo = 'Cliente' OR tipo = 'Clienti'")
        lista_clienti_estratto = df_clienti_solo['nome'].tolist() if not df_clienti_solo.empty else []
        
        if lista_clienti_estratto:
            cliente_selezionato = st.selectbox("Seleziona Cliente", options=lista_clienti_estratto, key="sel_cliente_estratto")
            
            if cliente_selezionato:
                query_storico_cliente = """
                    SELECT data, tipo, articolo, quantita, totale, stato 
                    FROM vendite 
                    WHERE cliente = ? AND stato != 'Annullata'
                    ORDER BY data DESC
                """
                df_storico = run_query(query_storico_cliente, (cliente_selezionato,))
                
                if not df_storico.empty:
                    tot_speso_cliente = df_storico[df_storico['tipo'] == 'Vendita']['totale'].sum() - df_storico[df_storico['tipo'] == 'Reso']['totale'].sum()
                    tot_ordini = len(df_storico)
                    
                    mc1, mc2 = st.columns(2)
                    mc1.metric("💰 Totale Speso dal Cliente", f"€ {tot_speso_cliente:,.2f}")
                    mc2.metric("📦 Operazioni Registrate", f"{tot_ordini}")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"### 📋 Dettaglio movimenti di: {cliente_selezionato}")
                    
                    df_storico_disp = df_storico.copy()
                    df_storico_disp['totale'] = df_storico_disp['totale'].apply(lambda x: f"€ {x:,.2f}")
                    st.dataframe(df_storico_disp, use_container_width=True)
                else:
                    st.info(f"Nessuna vendita registrata per il cliente **{cliente_selezionato}**.")
        else:
            st.warning("Nessun cliente presente in anagrafica.")

    with tab_ins:
        with st.form("form_contatto", clear_on_submit=True):
            tipo = st.selectbox("Tipo", ["Cliente", "Fornitore"])
            nome = st.text_input("Nome / Ragione Sociale")
            email = st.text_input("Email")
            telefono = st.text_input("Telefono")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Salva Contatto", use_container_width=True):
                if nome:
                    run_query("INSERT INTO contatti (tipo, nome, email, telefono) VALUES (?, ?, ?, ?)", 
                              (tipo, nome, email, telefono), fetch=False)
                    st.success(f"Contatto '{nome}' salvato con successo!")
                else:
                    st.error("Il campo Nome è obbligatorio.")