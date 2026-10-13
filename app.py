import streamlit as st
import pandas as pd
import sqlite3
import datetime
from datetime import datetime as dt_class

# ==============================================================================
# 🎨 CONFIGURAÇÃO VISUAL MASTER DA TELA (TELA CHEIA TOTAL DE PONTA A PONTA)
# ==============================================================================
st.set_page_config(
    page_title="DLR Confecções — ERP Corporativo",
    page_icon="🪡",
    layout="wide", # <=== DESTRANCA AS LATERAIS DO SEU MONITOR!
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .block-container {
            max-width: 100% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            padding-top: 1.5rem !important;
            padding-bottom: 1.5rem !important;
        }
        /* Design compacto do formulário de login */
        div[data-testid="stForm"] {
            max-width: 400px !important;
            margin: 0 auto !important;
            padding: 20px !important;
            border-radius: 10px !important;
            border: 1px solid #4A154B !important;
        }
        footer {visibility: hidden;}

        /* 🚀 TRAVA MÁGICA ATUALIZADA: Força TODO o texto do período na barra lateral a encolher */
        [data-testid="stSidebar"] [data-testid="stMarkdown"] p,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] span {
            font-size: 18px !important;      /* Largura/Tamanho perfeito e sutil para o texto! */
            font-weight: 500 !important;     /* Deixa a letra fina e corporativa */
            color: #CCCCCC !important;       /* Cor cinza clara discreta */
        }
    </style>
""", unsafe_allow_html=True)

# Inicializa as variáveis espiãs de controle de acesso se não existirem
if "sistema_autorizado" not in st.session_state:
    st.session_state.sistema_autorizado = False
if "perfil_usuario" not in st.session_state:
    st.session_state.perfil_usuario = ""

# ==============================================================================
# 🔑 CENTRAL DE SEGURANÇA MASTER DLR — 3 PERFIS INDEPENDENTES
# ==============================================================================
SENHA_ADMINISTRADOR = "204060"
SENHA_CONFERENCIA   = "2026"
SENHA_SETOR_MANUAL  = "2233"

# ==============================================================================
# 🗄️ 2. INICIALIZAÇÃO DO BANCO DE DADOS LOCAL OFICIAL — COFRE V3 DEFINITIVO
# ==============================================================================
def inicializar_banco_dados():
    conn = sqlite3.connect("dlr_confecoes_v3.db")
    cursor = conn.cursor()
    
    # Gaveta 1: Ficha Viva dos Funcionários Ativos (Fábrica Geral)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            tipo_pagamento TEXT,
            valor_base REAL,
            chave_pix TEXT,
            externo TEXT DEFAULT 'Não',
            status_cadastro TEXT DEFAULT 'Ativo'
        )
    """)
    
    # Gaveta 2: COFRE HISTÓRICO DA FOLHA DE PAGAMENTO (Administração)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_folha_pagamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes_ano TEXT,
            nome TEXT,
            tipo_pagamento TEXT,
            valor_base REAL,
            chave_pix TEXT,
            horas_trabalhadas REAL DEFAULT 0.0,
            total_vales REAL DEFAULT 0.0,
            valor_liquido REAL DEFAULT 0.0,
            status_pagto TEXT DEFAULT 'Pendente'
        )
    """)

    # Gaveta 3: ESTEIRA GERAL DE LOTES (Conferência e Manual)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lotes_gerais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_cadastro TEXT,
            data_inicio_producao TEXT DEFAULT '',
            data_entrega TEXT,
            fornecedor TEXT,
            of TEXT UNIQUE,
            referencia TEXT,
            qtd_prevista INTEGER,
            preco REAL,
            status TEXT DEFAULT 'Pendente',
            porcentagem_pronta INTEGER DEFAULT 0,
            qtd_pronta INTEGER DEFAULT 0,
            prioridade TEXT DEFAULT 'Não'
        )
    """)

    # Gaveta 4: GAVETA DO LIVRO CAIXA GERAL (Bota o motor no topo para o Dashboard ler de primeira!)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS livro_caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes_ano TEXT,
            data_movimento TEXT,
            tipo_movimentacao TEXT,
            descricao TEXT,
            valor_total REAL,
            parcela_atual INTEGER DEFAULT 1,
            total_parcelas INTEGER DEFAULT 1,
            valor_parcela REAL
        )
    """)

    # Gaveta 5: GAVETA DE SERVIÇOS EXTERNOS (Evita o mesmo erro na aba terceirizada!)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servicos_externos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes_ano TEXT,
            data_lancamento TEXT,
            costureira TEXT,
            of_numero TEXT,
            referencia_peca TEXT,
            nome_peca TEXT,
            valor_peca REAL,
            qtd_pecas INTEGER,
            valor_total REAL,
            status_servico TEXT DEFAULT 'Em produção',
            situacao_pagto TEXT DEFAULT 'Pendente'
        )
    """)
    # 🚀 NOVA GAVETA DE MEMÓRIA: Guarda os registros de eficiência horária da fábrica
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS producao_hora_hora (
            id INTEGER PRIMARY KEY AUTOINCREMENT, mes_ano TEXT, data_lancamento TEXT, costureira TEXT,
            operacao TEXT, qtd_pecas INTEGER, valor_unitario REAL, valor_total REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operacoes_frente (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome_operacao TEXT UNIQUE, preco_peca REAL
        )
    """)

    # 🚀 GAVETA DE MEMÓRIA DO PONTO: Guarda as horas trabalhadas mensais das horistas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registro_ponto_horistas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, mes_ano TEXT, data_registro TEXT, costureira TEXT, horas_totais REAL
        )
    """)

    conn.commit()
    conn.close()

inicializar_banco_dados()

# ==============================================================================
# 🌍 3. CENTRAL MASTER DE CALENDÁRIO GLOBAL DLR
# ==============================================================================
lista_meses_sistema = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
lista_anos_sistema = ["2026", "2027", "2028", "2029", "2030"]

mes_relogio_atual = datetime.datetime.now().month
ano_relogio_atual = str(datetime.datetime.now().year)

if "calendario_master_mes" not in st.session_state:
    st.session_state.calendario_master_mes = lista_meses_sistema[mes_relogio_atual - 1]
if "calendario_master_ano" not in st.session_state:
    st.session_state.calendario_master_ano = ano_relogio_atual

mes_ativo_txt = st.session_state.calendario_master_mes
ano_ativo_txt = st.session_state.calendario_master_ano

mapa_meses_num = {"Janeiro":"01", "Fevereiro":"02", "Março":"03", "Abril":"04", "Maio":"05", "Junho":"06", "Julho":"07", "Agosto":"08", "Setembro":"09", "Outubro":"10", "Novembro":"11", "Dezembro":"12"}
mes_ativo_num = mapa_meses_num[mes_ativo_txt]
periodo_ativo_chave = f"{mes_ativo_num}/{ano_ativo_txt}"

if "pagina_admin_atual" not in st.session_state: st.session_state.pagina_admin_atual = "🏠 Dashboard Inicial"
if "pagina_conf_atual" not in st.session_state: st.session_state.pagina_conf_atual = "📈 Progresso de Lotes"
if "pagina_manual_atual" not in st.session_state: st.session_state.pagina_manual_atual = "📦 Entrada de Lotes (Fornecedor)"

# 🔒 4. PORTAL DE LOGIN SUPREMO — SUPER COMPACTO E ELEVADO (DESIGN DE ALTO NÍVEL)
# ==============================================================================
if not st.session_state.sistema_autorizado:
    # CSS Injetado de Ouro: Oculta a barra lateral e força o bloco a ter no máximo 400px centralizado
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="stSidebarCollapseButton"] { display: none !important; }
            
            /* Remove margens e centraliza o bloco principal */
            .block-container {
                max-width: 100% !important;
                padding-top: 2rem !important;
            }
            
            /* Encolhe e estiliza a caixa do formulário para não ficar esparramada */
            div[data-testid="stForm"] {
                max-width: 400px !important;
                margin: 0 auto !important;
                padding: 20px !important;
                border-radius: 10px !important;
                border: 1px solid #4A154B !important;
            }
            footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)
    
    # Cria colunas simétricas para espremer o conteúdo exatamente no meio
    col_l1, col_l_centro, col_l2 = st.columns([1.2, 1, 1.2])
    
    with col_l_centro:
        # Exibe a logo oficial rosa de forma super compacta e sutil
        try:
            st.image("logo_dlr.png.png", width=380)
        except:
            st.markdown("<h2 style='text-align: center; color: #D81B60; margin-top: 0px;'>DLR CONFECÇÕES</h2>", unsafe_allow_html=True)
            
        st.markdown("<p style='text-align: center; color: #B0BEC5; font-size: 14px; margin-top: -10px; margin-bottom: 20px;'>🔑 Controle de Acesso Corporativo</p>", unsafe_allow_html=True)
        
        # Formulário compacto travado na largura de 400px
        with st.form(key="form_login_dlr_supremo_triplo_compacto", clear_on_submit=True):
            perfil_input = st.selectbox("Selecione o seu Setor:", ["Administração", "Conferência / Qualidade", "Setor Manual / Production"])
            senha_input = st.text_input("Senha de Acesso:", type="password")
            btn_acessar = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
        if btn_acessar:
            if perfil_input == "Administração" and senha_input == SENHA_ADMINISTRADOR:
                st.session_state.sistema_autorizado = True
                st.session_state.perfil_usuario = "Admin"
                st.rerun()
            elif perfil_input == "Conferência / Qualidade" and senha_input == SENHA_CONFERENCIA:
                st.session_state.sistema_autorizado = True
                st.session_state.perfil_usuario = "Conferencia"
                st.rerun()
            elif perfil_input == "Setor Manual / Production" and senha_input == SENHA_SETOR_MANUAL:
                st.session_state.sistema_autorizado = True
                st.session_state.perfil_usuario = "Manual"
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")

# 🔓 5. ESTRUTURA DOS MENUS ROXOS LATERAIS (VINCULADO AO PERFIL AUTORIZADO)
# ==============================================================================
else:
    with st.sidebar:
        st.title("🧵 DLR Confecções")
        st.subheader(f"📅 Período: {mes_ativo_txt}/{ano_ativo_txt}")
        st.markdown("---")
        st.markdown("### 📁 Menu de Páginas")
        
        if st.session_state.perfil_usuario == "Admin":
            paginas_admin = {
                "🏠 Dashboard Inicial": "🏠 Dashboard Inicial",
                "👤 Cadastrar Funcionário": "👥 Funcionários & Vales",
                "📋 Lotes em Andamento": "📋 Lotes em Andamento",
                "🚚 Serviços Externos": "🚚 Serviços Externos",
                "💰 Financeiro Geral": "💰 Financeiro Geral",
                "📅 Extrato do Mês": "📅 Extrato do Mês"
            }
            for label, pag_id in paginas_admin.items():
                if st.session_state.pagina_admin_atual == pag_id:
                    st.markdown(f"<div style='background-color: #FFFFFF; color: #000000; padding: 10px 15px; border-radius: 6px; font-weight: bold; text-align: center; border: 2px solid #4A154B; margin-bottom: 10px; font-size: 14px;'>{label}</div>", unsafe_allow_html=True)
                else:
                    if st.button(label, use_container_width=True, key=f"sidebar_btn_adm_{label}"):
                        st.session_state.pagina_admin_atual = pag_id; st.rerun()
            menu_selecionado = st.session_state.pagina_admin_atual
            
        elif st.session_state.perfil_usuario == "Conferencia":
            if "pagina_conf_atual" not in st.session_state:
                st.session_state.pagina_conf_atual = "📈 Progresso de Lotes"
                
            paginas_conf = {
                "📈 Progresso de Lotes": "📈 Progresso de Lotes",
                "📥 Importar Ponto": "📥 Importar Ponto",
                "📅 Extrato do Mês": "📅 Extrato do Mês"
            }
            for label, pag_id in paginas_conf.items():
                if st.session_state.pagina_conf_atual == pag_id:
                    st.markdown(f"<div style='background-color: #FFFFFF; color: #000000; padding: 10px 15px; border-radius: 6px; font-weight: bold; text-align: center; border: 2px solid #4A154B; margin-bottom: 10px; font-size: 14px;'>{label}</div>", unsafe_allow_html=True)
                else:
                    if st.button(label, use_container_width=True, key=f"sidebar_btn_conf_{label}"):
                        st.session_state.pagina_conf_atual = pag_id; st.rerun()
            menu_selecionado = st.session_state.pagina_conf_atual

        elif st.session_state.perfil_usuario == "Manual":
            menus_manual = {
                "📦 Entrada de Lotes (Fornecedor)": "📦 Entrada de Lotes (Fornecedor)",
                "⏱️ Produção de Hora em Hora": "⏱️ Produção de Hora em Hora",
                "📊 Peças Produzidas por Dia (P.D)": "📊 Peças Produzidas por Dia (P.D)"
            }
            for label, pag_id in menus_manual.items():
                if st.session_state.pagina_manual_atual == pag_id:
                    st.markdown(f"<div style='background-color: #FFFFFF; color: #000000; padding: 10px 15px; border-radius: 6px; font-weight: bold; text-align: center; border: 2px solid #4A154B; margin-bottom: 10px; font-size: 14px;'>{label}</div>", unsafe_allow_html=True)
                else:
                    if st.button(label, use_container_width=True, key=f"sidebar_btn_man_{label}"):
                        st.session_state.pagina_manual_atual = pag_id; st.rerun()
            menu_selecionado = st.session_state.pagina_manual_atual
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # 🚀 REQUISITO VITALÍCIO: O botão Sair fecha o bloco do with de forma limpa!
        if st.button("🚪 SAIR DO SISTEMA", use_container_width=True, type="secondary", key="btn_sair_lateral_master"):
            st.session_state.sistema_autorizado = False
            st.session_state.perfil_usuario = ""
            st.rerun()
# ==============================================================================
    # 🏢 CONTEÚDO EXCLUSIVO DO ADMINISTRADOR (5 CARDS SUPREMOS DE LARGURA TOTAL)
    # ==============================================================================
    if st.session_state.perfil_usuario == "Admin":
        if menu_selecionado == "🏠 Dashboard Inicial":
            st.title("🏠 Painel Executivo — Gestão de Desempenho DLR")
            
            col_m_master, col_a_master, col_esp_master = st.columns(3)
            with col_m_master:
                mes_escolhido = st.selectbox("Mês de Referência:", lista_meses_sistema, index=lista_meses_sistema.index(st.session_state.calendario_master_mes), key="caixa_master_mes_admin_v4")
            with col_a_master:
                ano_escolhido = st.selectbox("Ano de Referência:", lista_anos_sistema, index=lista_anos_sistema.index(st.session_state.calendario_master_ano), key="caixa_master_ano_admin_v4")
                
            if mes_escolhido != st.session_state.calendario_master_mes or ano_escolhido != st.session_state.calendario_master_ano:
                st.session_state.calendario_master_mes = mes_escolhido
                st.session_state.calendario_master_ano = ano_escolhido
                st.rerun()

            st.markdown(f"Exibindo balanço consolidado de: **{mes_ativo_txt} de {ano_ativo_txt}**")
            st.markdown("<br>", unsafe_allow_html=True)

            entradas_caixa_mes = 0.0; saidas_caixa_mes = 0.0; total_folha_mes = 0.0; total_externo_mes = 0.0
            
            conn = sqlite3.connect("dlr_confecoes_v3.db")
            cursor = conn.cursor()
            
            # 1. Soma as Entradas de Caixa Fixadas no Mês de Cadastro Master (SÓ NO MÊS CORRENTE)
            # 🚀 TRAVA DEFINITIVA: O faturamento ignora as datas digitadas e olha unicamente a coluna mes_ano_cadastro!
            cursor.execute("""
                SELECT SUM(qtd_pronta * preco) 
                FROM lotes_gerais 
                WHERE status = 'Concluído' AND mes_ano_cadastro = ?
            """, (periodo_ativo_chave,))
            res_e = cursor.fetchone()
            entradas_lotes = float(res_e[0]) if res_e and res_e[0] is not None else 0.0
            
            cursor.execute("SELECT SUM(valor_parcela) FROM livro_caixa WHERE mes_ano = ? AND tipo_movimentacao = 'Entrada'", (periodo_ativo_chave,))
            res_cx_e = cursor.fetchone()
            entradas_manuais = float(res_cx_e[0]) if res_cx_e and res_cx_e[0] is not None else 0.0
            entradas_caixa_mes = entradas_lotes + entradas_manuais

            # --- 🔸 2. SOMA AS SAÍDAS GERAIS (GÊMEO IDENTICO DA TABELA VISUAL DO EXTRATO GERAL) ---
            # 🚀 SINCRONISMO ABSOLUTO: Executa exatamente a mesma regra linha por linha da planilha E.G!
            conn_saidas_master = sqlite3.connect("dlr_confecoes_v3.db")
            cursor_saidas_master = conn_saidas_master.cursor()
            
            cursor_saidas_master.execute("""
                SELECT tipo_movimentacao, parcela_atual, valor_total, valor_parcela 
                FROM livro_caixa 
                WHERE mes_ano = ?
            """, (periodo_ativo_chave,))
            todos_movimentos_caixa = cursor_saidas_master.fetchall()
            cursor_saidas_master.close()
            conn_saidas_master.close()
            
            saidas_caixa_mes_calculado = 0.0
            for mov_c in todos_movimentos_caixa:
                t_mov = str(mov_c[0]).strip()
                p_atual = int(mov_c[1]) if mov_c[1] is not None else 1
                v_total = float(mov_c[2]) if mov_c[2] is not None else 0.0
                v_parc = float(mov_c[3]) if mov_c[3] is not None else 0.0
                
                # REPLICA A REGRA DA SUA TABELA: Se for Vale, só computa no card se for a parcela 1 e pega o valor TOTAL bruto!
                if t_mov == "Vale":
                    if p_atual == 1:
                        saidas_caixa_mes_calculado += v_total
                # Se for Saída manual comum (Gasolina, Contas), soma o valor normal da despesa
                elif t_mov == "Saída":
                    saidas_caixa_mes_calculado += v_parc
            
            # Tranca o valor blindado final na variável oficial do Dashboard para renderizar no card laranja
            saidas_caixa_mes = float(saidas_caixa_mes_calculado)
            # 3. Soma a Folha Interna Inteligente (Fixo Integral + Horistas por Produção de Ponto)
            total_folha_mes = 0.0
            cursor.execute("SELECT nome, tipo_pagamento, valor_base, total_vales FROM historico_folha_pagamento WHERE mes_ano = ?", (periodo_ativo_chave,))
            funcionarios_mes = cursor.fetchall()
            
            for func_f in funcionarios_mes:
                f_nome, f_tipo, f_valor_base, f_vales = func_f
                f_valor_base = float(f_valor_base) if f_valor_base else 0.0
                f_vales = float(f_vales) if f_vales else 0.0
                
                # REGRA FIXO: Adiciona o valor base integral abatendo os vales do mês
                if f_tipo == "Fixo":
                    total_folha_mes += (f_valor_base - f_vales)
                    
                # REGRA POR HORA: Busca as horas reais e faz a multiplicação (Se não trabalhou, é R$ 0,00)
                elif f_tipo == "Por hora":
                    cursor.execute("SELECT horas_totais FROM registro_ponto_horistas WHERE costureira = ? AND mes_ano = ?", (f_nome, periodo_ativo_chave))
                    res_ponto = cursor.fetchone()
                    
                    horas_trabalhadas = float(res_ponto[0]) if res_ponto and res_ponto[0] is not None else 0.0
                    
                    # Carga horária multiplicada pelo salário hora estabelecido na lista, abatendo vales
                    valor_hora_calculado = (f_valor_base * horas_trabalhadas) - f_vales
                    total_folha_mes += valor_hora_calculado
            
            # 4. Soma a Folha Externa vinda dos Serviços Externos Concluídos do mês
            cursor.execute("SELECT SUM(valor_total) FROM servicos_externos WHERE mes_ano = ?", (periodo_ativo_chave,))
            res_ext = cursor.fetchone()
            total_externo_mes = float(res_ext[0]) if res_ext and res_ext[0] is not None else 0.0
            
            conn.close()

            # Cálculo automático do Saldo Líquido Real Comercial
            saldo_liquido_mes = entradas_caixa_mes - saidas_caixa_mes - total_folha_mes - total_externo_mes

            # --- RENDERIZADOR DOS CARDS MASTER SUPREMOS — CENTRALIZAÇÃO ABSOLUTA RECALIBRADA ---
            c1, c2, c3, c4, c5 = st.columns(5, gap="small")
            
            with c1:
                st.markdown(f"""
                    <div style='background-color: #2E7D32; padding: 12px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center;'>
                        <div style='font-size: 13px; font-weight: normal; color: #E8F5E9; opacity: 0.9; display: flex; align-items: center; justify-content: center; gap: 4px; width: 100%;'>💵 Entrada Caixa</div>
                        <h3 style='margin-top: 6px; margin-bottom: 0px; color: white; font-size: 21px; font-weight: bold; width: 100%; text-align: center;'>R$ {entradas_caixa_mes:,.2f}</h3>
                    </div>
                """, unsafe_allow_html=True)
                
            with c2:
                st.markdown(f"""
                    <div style='background-color: #E65100; padding: 12px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center;'>
                        <div style='font-size: 13px; font-weight: normal; color: #FFF3E0; opacity: 0.9; display: flex; align-items: center; justify-content: center; gap: 4px; width: 100%;'>🔸 Saídas Gerais</div>
                        <h3 style='margin-top: 6px; margin-bottom: 0px; color: white; font-size: 21px; font-weight: bold; width: 100%; text-align: center;'>R$ {saidas_caixa_mes:,.2f}</h3>
                    </div>
                """, unsafe_allow_html=True)
                
            with c3:
                st.markdown(f"""
                    <div style='background-color: #C62828; padding: 12px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center;'>
                        <div style='font-size: 13px; font-weight: normal; color: #FFEBEE; opacity: 0.9; display: flex; align-items: center; justify-content: center; gap: 4px; width: 100%;'>🧱 Folha Interna</div>
                        <h3 style='margin-top: 6px; margin-bottom: 0px; color: white; font-size: 21px; font-weight: bold; width: 100%; text-align: center;'>R$ {total_folha_mes:,.2f}</h3>
                    </div>
                """, unsafe_allow_html=True)
                
            with c4:
                st.markdown(f"""
                    <div style='background-color: #7B1FA2; padding: 12px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center;'>
                        <div style='font-size: 13px; font-weight: normal; color: #F3E5F5; opacity: 0.9; display: flex; align-items: center; justify-content: center; gap: 4px; width: 100%;'>📌 Folha Externa</div>
                        <h3 style='margin-top: 6px; margin-bottom: 0px; color: white; font-size: 21px; font-weight: bold; width: 100%; text-align: center;'>R$ {total_externo_mes:,.2f}</h3>
                    </div>
                """, unsafe_allow_html=True)
                
            with c5:
                cor_l = "#1565C0" if saldo_liquido_mes >= 0 else "#B71C1C"
                st.markdown(f"""
                    <div style='background-color: {cor_l}; padding: 12px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center;'>
                        <div style='font-size: 13px; font-weight: normal; color: #E3F2FD; opacity: 0.9; display: flex; align-items: center; justify-content: center; gap: 4px; width: 100%;'>💰 Saldo Líquido</div>
                        <h3 style='margin-top: 6px; margin-bottom: 0px; color: white; font-size: 21px; font-weight: bold; width: 100%; text-align: center;'>R$ {saldo_liquido_mes:,.2f}</h3>
                    </div>
                """, unsafe_allow_html=True)

                # 📊 GRÁFICO MASTER EM TEMPO REAL: FATURAMENTO DE PRODUÇÃO DIÁRIA DA FÁBRICA
            # ==============================================================================
            st.markdown("<br><hr>", unsafe_allow_html=True)
            st.subheader(f"📈 Monitor de Produtividade Diária — Faturamento por Dia ({mes_ativo_txt}/{ano_ativo_txt})")
            st.write("O gráfico abaixo consolida o valor total bruto produzido pela fábrica dia por dia dentro do mês selecionado:")
            
            # 🚀 MOTOR DE VARREDURA CONECTADO À TABELA REAL: Busca direto na tabela oficial de eficiência
            try:
                conn_grafico = sqlite3.connect("dlr_confecoes_v3.db")
                df_dados_producao = pd.read_sql_query(f"""
                    SELECT data_lancamento, valor_total 
                    FROM producao_hora_hora 
                    WHERE mes_ano = '{periodo_ativo_chave}'
                """, conn_grafico)
                conn_grafico.close()
            except:
                df_dados_producao = pd.DataFrame(columns=['data_lancamento', 'valor_total'])

            # Cria a estrutura base do calendário de 1 a 31 dias para o gráfico nascer perfeito
            dias_do_mes = [f"{d:02d}" for d in range(1, 32)]
            valores_por_dia = {dia: 0.0 for dia in dias_do_mes}

            # Aloca os faturamentos reais acumulando por dia correspondente
            if not df_dados_producao.empty:
                for _, row_p in df_dados_producao.iterrows():
                    dt_p = str(row_p['data_lancamento']).strip() # Formato salvo: "05/10/2026"
                    if len(dt_p) >= 2:
                        dia_extraido = dt_p[:2] # Pega os dois primeiros caracteres (o dia)
                        if dia_extraido in valores_por_dia:
                            valores_por_dia[dia_extraido] += float(row_p['valor_total'] if row_p['valor_total'] else 0.0)

            # Transforma o dicionário na planilha final de leitura visual do Streamlit
            df_grafico_final = pd.DataFrame({
                "Dia do Mês": list(valores_por_dia.keys()),
                "Total Produzido (R$)": list(valores_por_dia.values())
            }).set_index("Dia do Mês")

            # 🎨 DESENHA O GRÁFICO DE BARRAS TOTALMENTE INTEGRADO COM A SOMA REAL
            st.bar_chart(df_grafico_final, color="#2E7D32", use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            # ==============================================================================

        # ==============================================================================
        # 👤 SUB-PÁGINA ADMINISTRATIVE: CADASTRAR FUNCIONÁRIO (RETÂNGULOS ROXOS NO TOPO)
        # ==============================================================================
        if menu_selecionado == "👥 Funcionários & Vales":
            st.title("👤 Gestão de Colaboradores — Administração DLR")
            st.markdown(f"Período de Referência Ativo: **{mes_ativo_txt} de {ano_ativo_txt}**")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if "sub_menu_funcionarios" not in st.session_state:
                st.session_state.sub_menu_funcionarios = "R.F"
                
            # --- DESENHO DOS DOIS RETÂNGULOS ROXOS NO TOPO DA TELA (IGUAL À IMAGEM) ---
            col_sub1, col_sub2, col_sub_esp = st.columns([2.5, 2.5, 5])
            
            with col_sub1:
                if st.session_state.sub_menu_funcionarios == "R.F":
                    st.markdown("<div style='background-color: #FFFFFF; color: #000000; padding: 10px; border-radius: 6px; font-weight: bold; text-align: center; border: 2px solid #4A154B; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); font-size: 14px;'>📇 Registrar Funcionário (R.F)</div>", unsafe_allow_html=True)
                else:
                    if st.button("📇 Registrar Funcionário (R.F)", use_container_width=True, key="btn_sub_rf_v4"):
                        st.session_state.sub_menu_funcionarios = "R.F"
                        st.rerun()
                        
            with col_sub2:
                if st.session_state.sub_menu_funcionarios == "L.F":
                    st.markdown("<div style='background-color: #FFFFFF; color: #000000; padding: 10px; border-radius: 6px; font-weight: bold; text-align: center; border: 2px solid #4A154B; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); font-size: 14px;'>📋 Lista de Funcionários (L.F)</div>", unsafe_allow_html=True)
                else:
                    if st.button("📋 Lista de Funcionários (L.F)", use_container_width=True, key="btn_sub_lf_v4"):
                        st.session_state.sub_menu_funcionarios = "L.F"
                        st.rerun()

            st.markdown("<br><hr>", unsafe_allow_html=True)

            # --- INTERFACE INTERNA 1: FORMULÁRIO COM AVISO DE CONFIRMAÇÃO E REATIVADOR (R.F) ---
            if st.session_state.sub_menu_funcionarios == "R.F":
                st.subheader("📇 Formulário de Registro")
                
                if "clicou_salvar_func" not in st.session_state: st.session_state.clicou_salvar_func = False
                if "dados_temporarios_func" not in st.session_state: st.session_state.dados_temporarios_func = {}

                # CONTROLADOR DO AVISO AMARELO DE CONFIRMAÇÃO DE TELA
                if st.session_state.clicou_salvar_func:
                    tmp = st.session_state.dados_temporarios_func
                    st.warning(f"⚠️ **Aviso de Confirmação:** Tem certeza que deseja registrar **{tmp['nome']}** como **{tmp['cargo']}** com o valor de **R$ {tmp['valor']:.2f}** no cofre de {mes_ativo_txt}?")
                    
                    col_c_sim, col_c_nao = st.columns(2)
                    with col_c_sim:
                        if st.button("✅ Sim, confirmar e registrar", use_container_width=True, type="primary", key="btn_conf_cad_v4"):
                            conn = sqlite3.connect("dlr_confecoes_v3.db")
                            cursor = conn.cursor()
                            try:
                                # 1. VERIFICAÇÃO DE HISTÓRICO: Vê se o funcionário já existia arquivado na tabela
                                cursor.execute("SELECT status_cadastro FROM funcionarios WHERE nome = ?", (tmp['nome'],))
                                existe_na_base = cursor.fetchone()
                                
                                if existe_na_base:
                                    # Se ele já existia, atualiza os dados e salva a marcação seletiva
                                    cursor.execute("""
                                        UPDATE funcionarios 
                                        SET tipo_pagamento = ?, valor_base = ?, chave_pix = ?, externo = ?, status_cadastro = ?
                                        WHERE nome = ?
                                    """, (tmp['pagto'], tmp['valor'], tmp['pix'], tmp['cargo'], tmp['lancar_manual'], tmp['nome']))
                                else:
                                    # Se for novo, grava a marcação na coluna de controle
                                    cursor.execute("""
                                        INSERT INTO funcionarios (nome, tipo_pagamento, valor_base, chave_pix, externo, status_cadastro) 
                                        VALUES (?, ?, ?, ?, ?, ?)
                                    """, (tmp['nome'], tmp['pagto'], tmp['valor'], tmp['pix'], tmp['cargo'], tmp['lancar_manual']))
                                
                                # 2. SINCRO DE MESES: Garante a criação ou atualização da linha do mês na folha histórica
                                cursor.execute("SELECT id FROM historico_folha_pagamento WHERE nome = ? AND mes_ano = ?", (tmp['nome'], periodo_ativo_chave))
                                if not cursor.fetchone():
                                    cursor.execute("""
                                        INSERT INTO historico_folha_pagamento (mes_ano, nome, tipo_pagamento, valor_base, chave_pix, total_vales, status_pagto) 
                                        VALUES (?, ?, ?, ?, ?, 0.0, 'Pendente')
                                    """, (periodo_ativo_chave, tmp['nome'], tmp['pagto'], tmp['valor'], tmp['pix']))
                                else:
                                    cursor.execute("""
                                        UPDATE historico_folha_pagamento
                                        SET tipo_pagamento = ?, valor_base = ?, chave_pix = ?
                                        WHERE nome = ? AND mes_ano = ?
                                    """, (tmp['pagto'], tmp['valor'], tmp['pix'], tmp['nome'], periodo_ativo_chave))
                                
                                conn.commit()
                                st.success(f"🎉 Sucesso! Registro de {tmp['nome']} processado e integrado com o cargo de {tmp['cargo']}!")
                                st.session_state.clicou_salvar_func = False
                                st.rerun()
                            except sqlite3.Error as e:
                                st.error(f"⚠️ Erro técnico operacional no cofre v3: {e}")
                                st.session_state.clicou_salvar_func = False
                            finally: 
                                conn.close()
                    with col_c_nao:
                        if st.button("❌ Não, cancelar", use_container_width=True, key="btn_canc_cad_v4"):
                            st.session_state.clicou_salvar_func = False
                            st.rerun()
                            
                st.markdown("<br>", unsafe_allow_html=True)

                # --- FORMULÁRIO PURIFICADO, ALINHADO E SEM DUPLICIDADE ---
                with st.form(key="form_cadastro_oficial_v4", clear_on_submit=True):
                    nome_completo = st.text_input("Nome Completo").strip().title()
                    cargo_sel = st.selectbox("Cargo / Função", ["Costureira", "Manual", "Revisora", "Conferente", "Supervisor(a)", "Entregador"])
                    forma_pagto = st.selectbox("Tipo de Pagamento", ["Fixo", "Por hora", "Por operação"])
                    
                    col_v_b, col_v_e = st.columns(2)
                    with col_v_b: 
                        valor_rs = st.number_input("Valor R$", min_value=0.0, step=10.0, format="%.2f")
                    with col_v_e: 
                        # Pergunta integrada perfeitamente no formulário original
                        lancar_manual_input = st.selectbox("Lançar no Manual?", ["Não", "Sim"])
                        
                    chave_pix_input = st.text_input("Chave PIX")
                    btn_salvar_oficial = st.form_submit_button("💾 Salvar Registro na Base")
                    
                if btn_salvar_oficial:
                    if not nome_completo:
                        st.error("❌ O nome do colaborador é obrigatório!")
                    else:
                        # Guarda a resposta na memória temporária para a caixa de aviso ler
                        st.session_state.dados_temporarios_func = {
                            "nome": nome_completo, "cargo": cargo_sel, "pagto": forma_pagto, 
                            "valor": valor_rs, "pix": chave_pix_input, "lancar_manual": lancar_manual_input
                        }
                        st.session_state.clicou_salvar_func = True
                        st.rerun()

                        # --- INTERFACE INTERNA 2: PLANILHA MASTER DE CADASTRO COM AS 5 COLUNAS (L.F) ---
            elif st.session_state.sub_menu_funcionarios == "L.F":
                st.subheader(f"📋 Ficha de Colaboradores Ativos — {mes_ativo_txt}/{ano_ativo_txt}")
                st.write("📖 **Dica do Chefe:** Altere os dados ou apague linhas livremente na tabela abaixo. O sistema salva as alterações e atualizações de forma automática!")
                
                btn_clonar_folha = st.button("🔄 Importar Funcionários Ativos do Mês Passado", use_container_width=True, key=f"btn_clonar_fp_{periodo_ativo_chave}")
                if btn_clonar_folha:
                    m_atual = int(mes_ativo_num); a_atual = int(ano_ativo_txt)
                    m_anterior = m_atual - 1; a_anterior = a_atual
                    if m_anterior == 0: m_anterior = 12; a_anterior -= 1
                    chave_periodo_anterior = f"{m_anterior:02d}/{a_anterior}"

                    conn = sqlite3.connect("dlr_confecoes_v3.db")
                    cursor = conn.cursor()
                    # 🚀 CORREÇÃO DE OURO: Busca todo mundo que não está demitido ou resgata do histórico do mês passado!
                    cursor.execute("SELECT nome, tipo_pagamento, valor_base, chave_pix FROM funcionarios WHERE status_cadastro != 'Demitido'")
                    funcionarios_vivos = cursor.fetchall()
                    
                    if not funcionarios_vivos:
                        cursor.execute("SELECT nome, tipo_pagamento, valor_base, chave_pix FROM historico_folha_pagamento WHERE mes_ano = ?", (chave_periodo_anterior,))
                        funcionarios_vivos = cursor.fetchall()
                        
                    for f_vivo in funcionarios_vivos:
                        v_nome, v_tipo, v_valor, v_pix = f_vivo
                        cursor.execute("SELECT id FROM historico_folha_pagamento WHERE nome = ? AND mes_ano = ?", (v_nome, periodo_ativo_chave))
                        if not cursor.fetchone():
                            cursor.execute("INSERT INTO historico_folha_pagamento (mes_ano, nome, tipo_pagamento, valor_base, chave_pix, total_vales, status_pagto) VALUES (?, ?, ?, ?, ?, 0.0, 'Pendente')", (periodo_ativo_chave, v_nome, v_tipo, v_valor, v_pix))
                    conn.commit(); conn.close()
                    st.success("🎉 Lista de colaboradores sincronizada com o mês atual!"); st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)
                
                # CORREÇÃO DE OURO: Garante que a coluna de controle exista de forma blindada no banco de dados do HD
                conn = sqlite3.connect("dlr_confecoes_v3.db")
                cursor = conn.cursor()
                try: cursor.execute("ALTER TABLE funcionarios ADD COLUMN status_cadastro TEXT DEFAULT 'Não'")
                except: pass
                conn.commit()

                # Puxa os dados oficiais do banco de dados fazendo o cruzamento das tabelas
                df_folha_mes = pd.read_sql_query(f"""
                    SELECT 
                        h.id as 'ID_Original', 
                        h.nome as 'Nome Completo', 
                        f.externo as 'Cargo / Função',
                        h.tipo_pagamento as 'Tipo de Pagamento', 
                        h.valor_base as 'Valor R$', 
                        h.chave_pix as 'Chave PIX',
                        COALESCE(f.status_cadastro, 'Não') as 'Lançar no Manual'
                    FROM historico_folha_pagamento h
                    LEFT JOIN funcionarios f ON h.nome = f.nome
                    WHERE h.mes_ano = '{periodo_ativo_chave}'
                """, conn)
                conn.close()

                if not df_folha_mes.empty:
                    # 🚀 RESTAURAÇÃO MASTER: Alinhamento numérico de fábrica compatível com FLOAT (13.50, 1000.00...)
                    tabela_final_fp = st.data_editor(
                        df_folha_mes,
                        column_config={
                            "ID_Original": None,
                            "Nome Completo": st.column_config.TextColumn("👤 Nome Completo", width=220, required=True), 
                            "Cargo / Função": st.column_config.SelectboxColumn("🗂️ Cargo / Função", options=["Costureira", "Manual", "Revisora", "Conferente", "Supervisor(a)", "Entregador"], required=True, width=150), 
                            "Tipo de Pagamento": st.column_config.SelectboxColumn("⌨️ Tipo de Pagamento", options=["Fixo", "Por hora", "Por operation"], required=True, width=150), 
                            # 💸 PADRÃO DA MOEDA VOLTOU: Aceita o ponto normal e deixa as células fluidas
                            "Valor R$": st.column_config.NumberColumn("💰 Valor R$", format="%.2f", min_value=0.0, step=0.50, width=120, required=True), 
                            "Chave PIX": st.column_config.TextColumn("⚡ Chave PIX", width=160),
                            "Lançar no Manual": st.column_config.SelectboxColumn("🎛️ Lançar no Manual", options=["Não", "Sim"], required=True, width=140)
                        },
                        hide_index=True, use_container_width=True, num_rows="dynamic", key=f"planilha_folha_DL_master_{periodo_ativo_chave}"
                    )
                    
                    chave_cache_fp = f"planilha_folha_DL_master_{periodo_ativo_chave}"
                    if chave_cache_fp in st.session_state:
                        mudou_algo = False
                        conn = sqlite3.connect("dlr_confecoes_v3.db")
                        cursor = conn.cursor()
                        
                        # Monitor de exclusão de linhas por clique no lixo lateral
                        if st.session_state[chave_cache_fp]["deleted_rows"]:
                            for idx_l in st.session_state[chave_cache_fp]["deleted_rows"]:
                                id_reg_h = int(df_folha_mes.iloc[idx_l]["ID_Original"])
                                n_colab = df_folha_mes.iloc[idx_l]["Nome Completo"]
                                cursor.execute("DELETE FROM historico_folha_pagamento WHERE id = ?", (id_reg_h,))
                                cursor.execute("UPDATE funcionarios SET status_cadastro = 'Demitido' WHERE nome = ?", (n_colab,))
                            mudou_algo = True
                        
                        # Monitor de atualizações dinâmicas digitadas diretamente nas células
                        if st.session_state[chave_cache_fp]["edited_rows"]:
                            for idx_s, mudancas in st.session_state[chave_cache_fp]["edited_rows"].items():
                                idx_l = int(idx_s)
                                id_reg_h = int(df_folha_mes.iloc[idx_l]["ID_Original"])
                                n_orig = df_folha_mes.iloc[idx_l]["Nome Completo"]
                                
                                if "Nome Completo" in mudancas:
                                    novo_nome = str(mudancas["Nome Completo"]).strip().title()
                                    cursor.execute("UPDATE historico_folha_pagamento SET nome = ? WHERE id = ?", (novo_nome, id_reg_h))
                                    cursor.execute("UPDATE funcionarios SET nome = ? WHERE nome = ?", (novo_nome, n_orig))
                                    n_orig = novo_nome
                                if "Cargo / Função" in mudancas:
                                    cursor.execute("UPDATE funcionarios SET externo = ? WHERE nome = ?", (mudancas["Cargo / Função"], n_orig))
                                if "Tipo de Pagamento" in mudancas:
                                    cursor.execute("UPDATE historico_folha_pagamento SET tipo_pagamento = ? WHERE id = ?", (mudancas["Tipo de Pagamento"], id_reg_h))
                                    cursor.execute("UPDATE funcionarios SET tipo_pagamento = ? WHERE nome = ?", (mudancas["Tipo de Pagamento"], n_orig))
                                if "Valor R$" in mudancas:
                                    # 🧼 TRATAMENTO DE OURO: Pega o texto (ex: "13,5"), limpa espaços, troca vírgula por ponto e converte para número!
                                    texto_valor_cru = str(mudancas["Valor R$"]).replace("R$", "").replace(" ", "").replace(",", ".").strip()
                                    try:
                                        v_valor_convertido = float(texto_valor_cru)
                                        cursor.execute("UPDATE historico_folha_pagamento SET valor_base = ? WHERE id = ?", (v_valor_convertido, id_reg_h))
                                        cursor.execute("UPDATE funcionarios SET valor_base = ? WHERE nome = ?", (v_valor_convertido, n_orig))
                                    except ValueError:
                                        st.error("❌ Erro de digitação! Insira apenas números válidos usando vírgula ou ponto.")
                                if "Chave PIX" in mudancas:
                                    cursor.execute("UPDATE historico_folha_pagamento SET chave_pix = ? WHERE id = ?", (mudancas["Chave PIX"], id_reg_h))
                                    cursor.execute("UPDATE funcionarios SET chave_pix = ? WHERE nome = ?", (mudancas["Chave PIX"], n_orig))
                                if "Lançar no Manual" in mudancas:
                                    cursor.execute("UPDATE funcionarios SET status_cadastro = ? WHERE nome = ?", (mudancas["Lançar no Manual"], n_orig))
                            mudou_algo = True
                            
                        if mudou_algo: conn.commit(); conn.close(); st.rerun()
                        else: conn.close()
                else:
                    st.info("💡 Nenhuma ficha ativa localizada para este período. Use o botão acima para trazer os ativos!")

        # 🚚 SUB-PÁGINA ADMINISTRATIVE: SERVIÇOS EXTERNOS (RADAR 100% BLINDADO V19)
        # ==============================================================================
        if menu_selecionado == "🚚 Serviços Externos":
            st.title("🚚 Gerenciamento de Serviços Externos")
            st.markdown(f"Período de Referência Ativo: **{mes_ativo_txt} de {ano_txt_sel if 'ano_txt_sel' in locals() else ano_ativo_txt}**")
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- 🔌 GAVETA DE MEMÓRIA DAS CAIXAS OPERACIONAIS PARA AUTO-LIMPEZA ---
            if "se_costureira_clean" not in st.session_state: st.session_state.se_costureira_clean = ""
            if "se_of_clean" not in st.session_state: st.session_state.se_of_clean = "Escolha um OF..."
            if "se_valor_clean" not in st.session_state: st.session_state.se_valor_clean = 0.0
            if "se_qtd_clean" not in st.session_state: st.session_state.se_qtd_clean = 1
            if "se_nome_peca_clean" not in st.session_state: st.session_state.se_nome_peca_clean = ""

            # --- MOTOR DE BUSCA EM TEMPO REAL PARA PUXADA AUTOMÁTICA DA REF ---
            conn = sqlite3.connect("dlr_confecoes_v3.db")
            cursor = conn.cursor()
            
            # Puxa os OFs ativos convertendo para texto limpo para evitar curto-circuito de tipos
            cursor.execute("SELECT of FROM lotes_gerais WHERE status != 'Concluído' ORDER BY id DESC")
            lista_ofs_vivos = [str(row[0]).strip() for row in cursor.fetchall() if row]
            
            # 🚀 CORREÇÃO DE OURO 1: Se o banco foi resetado, busca as costureiras pela função ou marcação viva sem travar!
            cursor.execute("SELECT nome FROM funcionarios WHERE status_cadastro = 'Sim' OR externo = 'Costureira'")
            lista_funcs_ext = [str(row[0]).strip() for row in cursor.fetchall() if row]
            conn.close()

            # Variável espiã que controla o preenchimento automático da Referência
            ref_automatica = "Aguardando OF..."

            # --- MOTOR DE RECONHECIMENTO ADAPTATIVO V4 (DESEMPACOTAMENTO DE TUPLA) ---
            ref_automatica = "Aguardando OF..."
            of_atual_cache = str(st.session_state.se_of_clean).strip()

            if of_atual_cache and of_atual_cache != "Escolha um OF...":
                conn = sqlite3.connect("dlr_confecoes_v3.db")
                cursor = conn.cursor()
                
                # 1. Tenta buscar tratando o OF como número inteiro puro (Igual ao seu banco)
                try:
                    of_numerico = int(of_atual_cache)
                    cursor.execute("SELECT referencia FROM lotes_gerais WHERE of = ?", (of_numerico,))
                    res_busca = cursor.fetchone()
                except ValueError:
                    res_busca = None

                # 2. Se não achou como número, tenta buscar comparando como texto puro
                if not res_busca:
                    cursor.execute("SELECT referencia FROM lotes_gerais WHERE of = ?", (of_atual_cache,))
                    res_busca = cursor.fetchone()
                    
                conn.close()
                
                # 🚀 CORREÇÃO DE OURO 1: Captura a posição [0] para rasgar a tupla e extrair o texto puro do HD!
                if res_busca and res_busca[0] is not None:
                    ref_automatica = str(res_busca[0]).strip()

            # --- 🎨 DESENHO DOS CAMPOS EM COLUNAS PERFEITAS E FLUIDAS ---
            col_se1, col_se2, col_se3 = st.columns(3)
            with col_se1:
                costureira_ext_sel = st.selectbox(
                    "Selecionar Costureira", 
                    lista_funcs_ext if lista_funcs_ext else ["Nenhuma cadastrada"],
                    key="se_costureira_clean"
                )
            with col_se2:
                # 🚀 CORREÇÃO DE OURO 2: Removido o key fixo antigo para forçar o Streamlit a atualizar o value em tempo real!
                st.text_input("Referência da Peça", value=ref_automatica, disabled=True)
            with col_se3:
                valor_por_peca = st.number_input("Valor por Peça (R$)", min_value=0.0, step=0.50, format="%.2f", key="se_valor_clean")

            col_se4, col_se5, col_se6 = st.columns(3)
            with col_se4:
                of_ext_sel = st.selectbox(
                    "Selecionar Número do OF", 
                    ["Escolha um OF..."] + lista_ofs_vivos,
                    key="se_of_clean"
                )
            with col_se5:
                nome_peca_ext = st.text_input(
                    "Nome da Peça (ex: Camiseta, Bermuda)", 
                    placeholder="Digite a descrição da peça...", 
                    key="se_nome_peca_clean"
                ).strip().title()
            with col_se6:
                qtd_pecas_ext = st.number_input("Quantidade de Peças", min_value=1, step=1, key="se_qtd_clean")

            st.markdown("<br>", unsafe_allow_html=True)
            btn_registrar_ext = st.button("🧵 Registrar Lote Externo", use_container_width=True, key="btn_registrar_servico_externo_v5")

            # 🚀 MOTOR DE GRAVAÇÃO RECONECTADO: Captura o clique do botão e salva fisicamente no banco!
            if btn_registrar_ext:
                if of_ext_sel == "Escolha um OF..." or costureira_ext_sel == "Nenhuma cadastrada":
                    st.error("❌ Operação Recusada! Selecione um Número de OF e uma Costureira válida para salvar!")
                elif not nome_peca_ext or str(nome_peca_ext).strip() == "":
                    st.error("❌ Operação Recusada! O campo Nome da Peça é obrigatório!")
                elif valor_por_peca <= 0 or qtd_pecas_ext <= 0:
                    st.error("❌ Operação Recusada! O valor por peça e a quantidade devem ser maiores que zero!")
                else:
                    data_hoje_se = datetime.datetime.now().strftime("%d/%m/%Y")
                    valor_total_calculado = valor_por_peca * qtd_pecas_ext
                    
                    conn = sqlite3.connect("dlr_confecoes_v3.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO servicos_externos (mes_ano, data_lancamento, costureira, of_numero, referencia_peca, nome_peca, valor_peca, qtd_pecas, valor_total)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (periodo_ativo_chave, data_hoje_se, costureira_ext_sel, of_ext_sel, ref_automatica, nome_peca_ext, valor_por_peca, qtd_pecas_ext, valor_total_calculado))
                    conn.commit()
                    conn.close()
                    
                    # 🧼 OPERAÇÃO LIMPEZA AUTOMÁTICA BLINDADA: Evita o erro de widget já instanciado!
                    for chave_limpar in ["se_of_clean", "se_valor_clean", "se_qtd_clean", "se_nome_peca_clean"]:
                        if chave_limpar in st.session_state:
                            st.session_state.pop(chave_limpar)
                            
                    # Injeta os valores padrão de fábrica limpos no cache de transição
                    st.session_state.se_of_clean = "Escolha um OF..."
                    st.session_state.se_valor_clean = 0.0
                    st.session_state.se_qtd_clean = 1
                    st.session_state.se_nome_peca_clean = ""

                    st.success(f"🎉 Sucesso! Lote do OF {of_ext_sel} gravado e campos limpos automaticamente!")
                    st.rerun()
            # --- INTERFACE INFERIOR: HISTÓRICO DE LANÇAMENTOS COM EDIÇÃO E LIXEIRA V19 ---
            st.markdown("<br><hr>", unsafe_allow_html=True)
            st.subheader("📋 Histórico de Lançamentos e Controle de Serviços Externos")
            
            col_b_se1, col_b_se2 = st.columns([7, 3])
            with col_b_se2:
                termo_busca_se = st.text_input("🔍 Pesquisar por Nome ou OF:", placeholder="Digite o nome ou número...", key=f"busca_se_input_{periodo_ativo_chave}")

            st.markdown("💡 *Dica do Chefe: Dê dois cliques em Nome da Peça, Valor Pç ou Qtd para editar! Use a lixeira abaixo para apagar lançamentos.*")
            st.markdown("<br>", unsafe_allow_html=True)

            conn = sqlite3.connect("dlr_confecoes_v3.db")
            df_servicos_brutos = pd.read_sql_query(f"""
                SELECT 
                    s.id as 'ID_T',
                    s.data_lancamento as 'Data',
                    s.costureira as 'Costureira',
                    COALESCE(f.chave_pix, 'Sem PIX') as '⚡ Chave PIX',
                    s.of_numero as 'Nº do OF',
                    s.referencia_peca as 'Referência',
                    s.nome_peca as 'Nome da Peça',
                    s.valor_peca as 'Valor Pç',
                    s.qtd_pecas as 'Qtd',
                    s.valor_total as 'Total (R$)'
                FROM servicos_externos s
                LEFT JOIN funcionarios f ON s.costureira = f.nome
                WHERE s.mes_ano = '{periodo_ativo_chave}'
                ORDER BY s.id DESC
            """, conn)
            conn.close()

            if termo_busca_se:
                termo_b = termo_busca_se.strip().lower()
                df_servicos_brutos = df_servicos_brutos[
                    df_servicos_brutos['Costureira'].str.lower().str.contains(termo_b) | 
                    df_servicos_brutos['Nº do OF'].astype(str).str.lower().str.contains(termo_b)
                ]

            # --- RENDERIZAÇÃO DA PLANILHA MASTER 100% LIBERADA ---
            if not df_servicos_brutos.empty:
                chave_cache_se_tabela = f"tabela_servicos_externos_master_{periodo_ativo_chave}"
                
                tabela_editada_se = st.data_editor(
                    df_servicos_brutos,
                    column_config={
                        "ID_T": None,
                        "Data": st.column_config.TextColumn("Data", width=85, disabled=True),
                        "Costureira": st.column_config.TextColumn("Costureira", width=140, disabled=True),
                        "⚡ Chave PIX": st.column_config.TextColumn("⚡ Chave PIX", width=120, disabled=True),
                        "Nº do OF": st.column_config.TextColumn("Nº do OF", width=75, disabled=True),
                        "Referência": st.column_config.TextColumn("Referência", width=75, disabled=True),
                        # 🚀 LIBERADAS: Removido o 'disabled=True' destas três colunas conforme solicitado!
                        "Nome da Peça": st.column_config.TextColumn("Nome da Peça", width=130),
                        "Valor Pç": st.column_config.NumberColumn("Valor Pç", format="R$ %.2f", width=90),
                        "Qtd": st.column_config.NumberColumn("Qtd", format="%d", width=60),
                        "Total (R$)": st.column_config.NumberColumn("Total (R$)", format="R$ %.2f", width=110, disabled=True)
                    },
                    hide_index=True, use_container_width=True, key=chave_cache_se_tabela
                )
                
                # --- MOTOR DE ATUALIZAÇÃO E RECALCULO EM TEMPO REAL ---
                if chave_cache_se_tabela in st.session_state and st.session_state[chave_cache_se_tabela]["edited_rows"]:
                    conn = sqlite3.connect("dlr_confecoes_v3.db"); cursor = conn.cursor()
                    for idx_s, mudancas in st.session_state[chave_cache_se_tabela]["edited_rows"].items():
                        id_lote_se = int(df_servicos_brutos.iloc[int(idx_s)]["ID_T"])
                        v_peca_atual = float(df_servicos_brutos.iloc[int(idx_s)]["Valor Pç"])
                        qtd_atual = int(df_servicos_brutos.iloc[int(idx_s)]["Qtd"])
                        
                        if "Nome da Peça" in mudancas:
                            cursor.execute("UPDATE servicos_externos SET nome_peca = ? WHERE id = ?", (str(mudancas["Nome da Peça"]).strip(), id_lote_se))
                        if "Valor Pç" in mudancas:
                            v_peca_atual = float(mudancas["Valor Pç"])
                            cursor.execute("UPDATE servicos_externos SET valor_peca = ? WHERE id = ?", (v_peca_atual, id_lote_se))
                        if "Qtd" in mudancas:
                            qtd_atual = int(mudancas["Qtd"])
                            cursor.execute("UPDATE servicos_externos SET qtd_pecas = ? WHERE id = ?", (qtd_atual, id_lote_se))
                            
                        # Recalcula e salva o valor total com base nas alterações
                        novo_total = v_peca_atual * qtd_atual
                        cursor.execute("UPDATE servicos_externos SET valor_total = ? WHERE id = ?", (novo_total, id_lote_se))
                        
                    conn.commit(); conn.close(); st.rerun()

                # --- 🗑️ SEÇÃO DE REMOÇÃO SELETIVA DE LOTES EXTERNOS (RODAPÉ) ---
                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                lista_se_excluir = [f"ID: {r['ID_T']} | {r['Costureira']} - OF: {r['Nº do OF']} ({r['Nome da Peça']})" for _, r in df_servicos_brutos.iterrows()]
                se_selecionado_excluir = st.selectbox("🗑️ Selecione um Lote Externo para excluir:", ["Selecionar..."] + lista_se_excluir, key=f"lix_se_{periodo_ativo_chave}")
                
                if se_selecionado_excluir != "Selecionar...":
                    id_se_del = int(se_selecionado_excluir.split("|")[0].replace("ID: ", "").strip())
                    st.warning("⚠️ **Aviso de Segurança:** Tem certeza que deseja apagar permanentemente este serviço externo?")
                    c_se_d1, c_se_d2 = st.columns(2)
                    with c_se_d1:
                        if st.button("✅ Sim, confirmar exclusão", use_container_width=True, type="primary", key="btn_conf_del_se_f"):
                            conn = sqlite3.connect("dlr_confecoes_v3.db"); cursor = conn.cursor()
                            cursor.execute("DELETE FROM servicos_externos WHERE id = ?", (id_se_del,))
                            conn.commit(); conn.close()
                            if f"lix_se_{periodo_ativo_chave}" in st.session_state:
                                st.session_state.pop(f"lix_se_{periodo_ativo_chave}")
                            st.success("Removido com sucesso!"); st.rerun()
                    with c_se_d2:
                        if st.button("❌ Não, manter", use_container_width=True, key="btn_canc_del_se_f"):
                            if f"lix_se_{periodo_ativo_chave}" in st.session_state:
                                st.session_state.pop(f"lix_se_{periodo_ativo_chave}")
                            st.rerun()
            else:
                st.info("💡 Nenhum lote de serviço externo registrado para este período até o momento.")

        # 💰 SUB-PÁGINA ADMINISTRATIVE: FINANCEIRO GERAL (VERSÃO BLINDADA AUTO-LIMPANTE)
        # ==============================================================================
        if menu_selecionado == "💰 Financeiro Geral":
            st.title("💰 Fluxo de Caixa Dinâmico — Entradas e Saídas")
            st.markdown("""
            <style>
                div[data-testid="stForm"] {
                    max-width: 650px !important;
                    margin: 0px auto !important;
                    padding: 20px !important;
                }
            </style>
        """, unsafe_allow_html=True)
            st.markdown(f"Período de Referência Active: **{mes_ativo_txt} de {ano_ativo_txt}**")
            st.markdown("<br>", unsafe_allow_html=True)

            # Usamos o st.container para que a mudança do selectbox mude a tela em tempo real
            tipo_mov_sel = st.selectbox(
                "Tipo de Movimentação", 
                ["Saída (Geral)", "Entrada", "Saída (Vale de Funcionário)"], 
                key="tipo_movimentacao_master_v3"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)

            # --- ENGENHARIA DE FORMULÁRIO COM LIMPEZA AUTOMÁTICA COMPLETA ---
            # O clear_on_submit=True limpa TODAS as caixas da tela assim que o botão é clicado!
            with st.form(key="form_financeiro_clean_definitivo", clear_on_submit=True):
                
                # 🚨 SUB-FORMULÁRIO: CASO SEJA VALE DE FUNCIONÁRIO
                if tipo_mov_sel == "Saída (Vale de Funcionário)":
                    conn = sqlite3.connect("dlr_confecoes_v3.db")
                    cursor = conn.cursor()
                    # 🚀 CORREÇÃO DE OURO INDESTRUTÍVEL: Busca todo mundo que está na folha de pagamentos ativa deste mês!
                    cursor.execute("SELECT nome FROM historico_folha_pagamento WHERE mes_ano = ? ORDER BY nome ASC", (periodo_ativo_chave,))
                    
                    # O row[0] rasga o formato do SQLite e joga o texto puro dos nomes na tela sem parênteses!
                    lista_funcs_fin = [str(row[0]).strip() for row in cursor.fetchall() if row and row[0] is not None]
                    conn.close()
                    
                    funcionario_vale_sel = st.selectbox("Selecione o Funcionário que pediu o Vale", lista_funcs_fin if lista_funcs_fin else ["Nenhum funcionário ativo cadastrado"])
                    valor_total_mov = st.number_input("Valor do Vale (R$)", min_value=0.0, step=10.0, format="%.2f")
                    qtd_parcelas_mov = st.selectbox("Parcelar em quantas vezes? (Limite de 3x para Vales)", [1, 2, 3], index=0)
                    desc_final_mov = f"Vale Funcionário: {funcionario_vale_sel}"
                
                # 🏢 SUB-FORMULÁRIO: CASO SEJA ENTRADA OU SAÍDA GERAL
                else:
                    desc_final_mov = st.text_input("Descrição / Motivo da Movimentação (Linha, Luz, Combustível, etc.)").strip()
                    valor_total_mov = st.number_input("Valor Total (R$)", min_value=0.0, step=10.0, format="%.2f")
                    qtd_parcelas_mov = st.selectbox("Quantidade de parcelas (Se houver)", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], index=0)

                st.markdown("<br>", unsafe_allow_html=True)
                btn_registrar_caixa = st.form_submit_button("🔮 Registrar no Caixa", use_container_width=True)

            # --- MOTOR DE PROCESSAMENTO DO COFRE v3.db ---
            if btn_registrar_caixa:
                if valor_total_mov <= 0:
                    st.error("❌ O valor informado deve ser maior que R$ 0,00!")
                elif tipo_mov_sel != "Saída (Vale de Funcionário)" and not desc_final_mov:
                    st.error("❌ Por favor, digite a descrição do motivo da movimentação!")
                elif tipo_mov_sel == "Saída (Vale de Funcionário)" and (not lista_funcs_fin or funcionario_vale_sel == "Nenhum funcionário ativo cadastrado"):
                    st.error("❌ Cadastre colaboradores ativos antes de realizar adiantamentos!")
                else:
                    data_hoje_fin = datetime.datetime.now().strftime("%d/%m/%Y")
                    valor_da_parcela_fin = valor_total_mov / qtd_parcelas_mov
                    
                    conn = sqlite3.connect("dlr_confecoes_v3.db")
                    cursor = conn.cursor()
                    
                    m_corrido = int(mes_ativo_num)
                    a_corrido = int(ano_ativo_txt)
                    
                    tipo_banco_salvar = "Vale" if tipo_mov_sel == "Saída (Vale de Funcionário)" else ("Saída" if tipo_mov_sel == "Saída (Geral)" else "Entrada")
                    
                    for p_i in range(1, qtd_parcelas_mov + 1):
                        chave_mes_financeiro = f"{m_corrido:02d}/{a_corrido}"
                        desc_com_parcela = f"{desc_final_mov} ({p_i}/{qtd_parcelas_mov})" if qtd_parcelas_mov > 1 else desc_final_mov
                        
                        cursor.execute("""
                            INSERT INTO livro_caixa (mes_ano, data_movimento, tipo_movimentacao, descricao, valor_total, parcela_atual, total_parcelas, valor_parcela)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (chave_mes_financeiro, data_hoje_fin, tipo_banco_salvar, desc_com_parcela, valor_total_mov, p_i, qtd_parcelas_mov, valor_da_parcela_fin))
                        
                        if tipo_banco_salvar == "Vale":
                            cursor.execute("""
                                UPDATE historico_folha_pagamento 
                                SET total_vales = total_vales + ? 
                                WHERE nome = ? AND mes_ano = ?
                            """, (valor_da_parcela_fin, funcionario_vale_sel, chave_mes_financeiro))
                        
                        m_corrido += 1
                        if m_corrido > 12:
                            m_corrido = 1
                            a_corrido += 1
                            
                    conn.commit()
                    conn.close()
                    
                    # 🎉 Sucesso! O próprio Streamlit já limpou os campos das caixas por causa do clear_on_submit!
                    st.success(f"🎉 Lançamento de {tipo_banco_salvar} registrado com sucesso!")
                    st.rerun()
                    

  # ==============================================================================
        # 📅 SUB-PÁGINA ADMINISTRATIVE: EXTRATO DO MÊS (VERSÃO LIMPA VINCULADA AO MASTER)
        # ==============================================================================
        if menu_selecionado == "📅 Extrato do Mês":
            st.title("📅 Livro Caixa — Extrato de Todas as Movimentações")
            
            # Inicializa o estado de navegação interna dos extratos se não existia no cache
            if "sub_menu_extratos" not in st.session_state:
                st.session_state.sub_menu_extratos = "E.G"
                
            # CORREÇÃO DE OURO: Puxa diretamente o período ativo selecionado no calendário master global!
            periodo_ext_chave = periodo_ativo_chave
            mes_ext_sel = mes_ativo_txt
            ano_ext_sel = ano_ativo_txt
            
            st.markdown(f"Exibindo movimentações cronológicas referentes ao período ativo: **{mes_ext_sel} de {ano_ext_sel}**")
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- DESENHO RECALIBRADO EM 4 COLUNAS COMPACTAS E SIMÉTRICAS ---
            col_b1, col_b2, col_b3, col_b4 = st.columns(4)
            
            with col_b1:
                if st.session_state.sub_menu_extratos == "E.G":
                    st.markdown("<div style='background-color: #FFFFFF; color: #000000; padding: 10px; border-radius: 6px; font-weight: bold; text-align: center; border: 2px solid #4A154B; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); font-size: 14px;'>📊 Extrato Geral (E.G)</div>", unsafe_allow_html=True)
                else:
                    if st.button("📊 Extrato Geral (E.G)", use_container_width=True, key="btn_ext_eg_clean"):
                        st.session_state.sub_menu_extratos = "E.G"
                        st.rerun()
                        
            with col_b2:
                if st.session_state.sub_menu_extratos == "E.V":
                    st.markdown("<div style='background-color: #FFFFFF; color: #000000; padding: 10px; border-radius: 6px; font-weight: bold; text-align: center; border: 2px solid #4A154B; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); font-size: 14px;'>💸 Extrato de Vale (E.V)</div>", unsafe_allow_html=True)
                else:
                    if st.button("💸 Extrato de Vale (E.V)", use_container_width=True, key="btn_ext_ev_clean"):
                        st.session_state.sub_menu_manual_lotes = "A.P" if 'sub_menu_manual_lotes' in st.session_state else "A.P"
                        st.session_state.sub_menu_extratos = "E.V"
                        st.rerun()
                        
            with col_b3:
                if st.session_state.sub_menu_extratos == "F.P":
                    st.markdown("<div style='background-color: #FFFFFF; color: #000000; padding: 10px; border-radius: 6px; font-weight: bold; text-align: center; border: 2px solid #4A154B; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); font-size: 14px;'>📄 Folha de Pag. (F.P)</div>", unsafe_allow_html=True)
                else:
                    if st.button("📄 Folha de Pag. (F.P)", use_container_width=True, key="btn_ext_fp_clean"):
                        st.session_state.sub_menu_extratos = "F.P"
                        st.rerun()

            with col_b4:
                # 🚀 NOVO QUARTO BOTÃO NO LOCAL EXATO DO SEU RISCO VERMELHO — PERFEITAMENTE IGUAL AOS OUTROS
                if st.session_state.sub_menu_extratos == "E.H":
                    st.markdown("<div style='background-color: #FFFFFF; color: #000000; padding: 10px; border-radius: 6px; font-weight: bold; text-align: center; border: 2px solid #4A154B; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); font-size: 14px;'>⚙️ Eficiência Hora (E.H)</div>", unsafe_allow_html=True)
                else:
                    if st.button("⚙️ Eficiência Hora (E.H)", use_container_width=True, key="btn_ext_eh_clean"):
                        st.session_state.sub_menu_extratos = "E.H"
                        st.rerun()

                        # ⚙️ SUB-TELA D: ESPELHO DE EFICIÊNCIA HORÁRIA & CADASTRO DE PREÇOS (E.H)
            # ==============================================================================
            if st.session_state.sub_menu_extratos == "E.H":
                st.markdown(f"### 📋 Espelho de Produção Horária — {mes_ext_sel}/{ano_ext_sel}")
                
                # --- 🛠️ SEÇÃO A: TABELA DE CADASTRO DE OPERAÇÕES E VALORES (PARA O MANUAL LER) ---
                st.markdown("##### ⚙️ Tabela de Preços por Operação (Fábrica)")
                st.write("Insira ou altere o preço pago por cada operação. O Setor Manual lerá estes dados automaticamente:")
                
                conn = sqlite3.connect("dlr_confecoes_v3.db")
                cursor = conn.cursor()
                # Garante que a tabela de cadastro de preços exista de forma blindada
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS operacoes_frente (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        nome_operacao TEXT UNIQUE, 
                        preco_peca REAL
                    )
                """)
                conn.commit()
                
                # Lê os preços salvos para jogar no editor
                df_tabela_precos = pd.read_sql_query("SELECT id as 'ID_O', nome_operacao as 'Tipo de Operação', preco_peca as 'Preço por Peça (R$)' FROM operacoes_frente", conn)
                conn.close()
                
                # Editor dinâmico espremido de parede a parede que aceita adicionar e deletar linhas
                chave_tabela_precos_op = "editor_precos_operacoes_master_v3"
                tabela_precos_editada = st.data_editor(
                    df_tabela_precos,
                    column_config={
                        "ID_O": None, # Oculta o ID técnico
                        "Tipo de Operação": st.column_config.TextColumn("Tipo de Operação (ex: Cós, Pré, Elástico)", width=250, required=True),
                        "Preço por Peça (R$)": st.column_config.NumberColumn("Preço por Peça", format="R$ %.2f", min_value=0.0, step=0.05, width=150, required=True)
                    },
                    hide_index=True,
                    num_rows="dynamic", # Ativa os botões nativos de "Adicionar Linha" e o "Lixinho" de deletar na lateral!
                    use_container_width=True,
                    key=chave_tabela_precos_op
                )
                
                # MOTOR DE GRAVAÇÃO AUTOMÁTICA DE PREÇOS NO COFRE V3
                if chave_tabela_precos_op in st.session_state:
                    mudancas_op = st.session_state[chave_tabela_precos_op]
                    if mudancas_op["edited_rows"] or mudancas_op["added_rows"] or mudancas_op["deleted_rows"]:
                        conn = sqlite3.connect("dlr_confecoes_v3.db")
                        cursor = conn.cursor()
                        
                        # Caso 1: Novas linhas adicionadas na planilha
                        for nova_linha in mudancas_op["added_rows"]:
                            if "Tipo de Operação" in nova_linha and "Preço por Peça (R$)" in nova_linha:
                                nome_n = str(nova_linha["Tipo de Operação"]).strip().title()
                                preco_n = float(nova_linha["Preço por Peça (R$)"])
                                if nome_n:
                                    cursor.execute("INSERT OR REPLACE INTO operacoes_frente (nome_operacao, preco_peca) VALUES (?, ?)", (nome_n, preco_n))
                        
                        # Caso 2: Linhas editadas direto na célula
                        for idx_s, mudou_celula in mudancas_op["edited_rows"].items():
                            id_banco_op = int(df_tabela_precos.iloc[int(idx_s)]["ID_O"])
                            if "Tipo de Operação" in mudou_celula:
                                cursor.execute("UPDATE operacoes_frente SET nome_operacao = ? WHERE id = ?", (str(mudou_celula["Tipo de Operação"]).strip().title(), id_banco_op))
                            if "Preço por Peça (R$)" in mudou_celula:
                                cursor.execute("UPDATE operacoes_frente SET preco_peca = ? WHERE id = ?", (float(mudou_celula["Preço por Peça (R$)"]), id_banco_op))
                        
                        # Caso 3: Linhas deletadas pelo botão de lixo do Streamlit
                        for idx_del in mudancas_op["deleted_rows"]:
                            id_banco_del = int(df_tabela_precos.iloc[int(idx_del)]["ID_O"])
                            cursor.execute("DELETE FROM operacoes_frente WHERE id = ?", (id_banco_del,))
                            
                        conn.commit()
                        conn.close()
                        st.rerun()

                st.markdown("<br><hr style='border-top: 1px dashed #424242;'><br>", unsafe_allow_html=True)
                
                # --- 📊 SEÇÃO B RECALIBRADA: FILTRO EXCLUSIVO POR NÚMERO DO DIA ---
                st.markdown("##### 🧾 Comprovantes de Produção Diária (Eficiência)")
                st.write("Selecione o dia do mês corrente para isolar o cupom fiscal de produção:")
                
                # 🚀 NOVO SELETOR CIRÚRGICO: Cria uma lista limpa do dia 1 ao dia 31 para o chefe clicar
                lista_dias_mes = [str(d) for d in range(1, 32)]
                
                # Tenta capturar o número do dia de hoje para já vir pré-selecionado por padrão de fábrica
                dia_hoje_padrao = str(datetime.datetime.now().day)
                
                # Lista de dias do 1 ao 31
                lista_dias_mes = [str(d) for d in range(1, 32)]
                dia_hoje_padrao = str(datetime.datetime.now().day)
                
                # Monta a máscara de data exata (ex: "05/10/2026")
                # Inicializa a variável para garantir leitura antes de desenhar o card
                if 'dia_selecionado' not in st.session_state:
                    st.session_state.dia_selecionado_val = dia_hoje_padrao
                
                # --- ⚙️ MOTOR ANTECIPADO DE CÁLCULO DO TOTAL DO DIA ---
                # Criamos a busca antes para alimentar o número grande dentro do card
                dia_provisorio = st.session_state.get(f"filtro_dia_puro_eh_{periodo_ext_chave}", dia_hoje_padrao)
                data_busca_formatada = f"{int(dia_provisorio):02d}/{periodo_ext_chave}"
                
                conn = sqlite3.connect("dlr_confecoes_v3.db")
                df_calculo_card = pd.read_sql_query(f"SELECT valor_total FROM producao_hora_hora WHERE mes_ano = '{periodo_ext_chave}' AND data_lancamento = '{data_busca_formatada}'", conn)
                conn.close()
                
                # Soma tudo o que foi gerado por todas as costureiras nessa data específica
                faturamento_bruto_dia = float(df_calculo_card["valor_total"].sum()) if not df_calculo_card.empty else 0.0

                # --- 🎨 DESENHO DO FILTRO E DO CARD TOTAL COM TAMANHO MANUAL REDUZIDO ---
                # Adicionada a terceira coluna (col_respiro_vazio) com peso 5 para segurar o tamanho!
                col_dia_puro, col_card_total, col_respiro_vazio = st.columns([2.5, 2.5, 5])
                
                with col_dia_puro:
                    dia_selecionado = st.selectbox(
                        "📅 Selecionar Dia do Mês:", 
                        lista_dias_mes, 
                        index=lista_dias_mes.index(dia_hoje_padrao),
                        key=f"filtro_dia_puro_eh_{periodo_ext_chave}"
                    )
                    # Força a atualização do formato caso mude o clique
                    data_busca_formatada = f"{int(dia_selecionado):02d}/{periodo_ext_chave}"
                
                with col_card_total:
                    # 🚀 CORREÇÃO DE OURO: Adicionado max-width: 260px para encolher o card manualmente na tela!
                    st.markdown(f"""
                        <div style='background-color: #2E7D32; padding: 12px 15px; border-radius: 8px; color: white; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; height: 78px; margin-top: 24px; max-width: 260px;'>
                            <div style='font-size: 12px; font-weight: normal; color: #C8E6C9; opacity: 0.9; font-family: sans-serif; white-space: nowrap;'>💰 Total Produzido no Dia ({data_busca_formatada})</div>
                            <h3 style='margin: 2px 0 0 0; color: white; font-size: 24px; font-weight: bold; font-family: sans-serif;'>R$ {faturamento_bruto_dia:,.2f}</h3>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
                
                # --- RADAR DE EXIBIÇÃO DO HISTÓRICO ATUALIZADO ---
                conn = sqlite3.connect("dlr_confecoes_v3.db")
                df_eh = pd.read_sql_query(f"SELECT costureira, operacao, qtd_pecas, valor_total FROM producao_hora_hora WHERE mes_ano = '{periodo_ext_chave}' AND data_lancamento = '{data_busca_formatada}'", conn)
                conn.close()
                
                if not df_eh.empty:
                    lista_costureiras_com_producao = df_eh["costureira"].unique()
                    
                    for cost_nome in lista_costureiras_com_producao:
                        df_filtro_cost = df_eh[df_eh["costureira"] == cost_nome]
                        
                        st.markdown(f"""
                            <div style='background-color: #212121; padding: 18px; border-radius: 8px; border-left: 5px solid #4A154B; max-width: 550px; margin-bottom: 25px; font-family: monospace; box-shadow: 2px 2px 8px rgba(0,0,0,0.2);'>
                                <h4 style='color: #E040FB; margin: 0 0 12px 0; font-family: sans-serif; font-size: 15px;'>📇 COMPROVANTE DE PRODUÇÃO ACUMULADA</h4>
                                <div style='font-size: 13px; color: #CFD8DC; line-height: 1.6;'>
                                    <b>COLABORADORA:</b> {str(cost_nome).upper()}<br>
                                    <b>COMPETÊNCIA:</b> {mes_ext_sel} de {ano_ext_sel}<br>
                                    <span style='color: #69F0AE;'><b>DATA DO EXTRATO:</b> {data_busca_formatada}</span>
                                </div>
                                <hr style='border: 0; border-top: 1px dashed #555555; margin: 12px 0;'>
                        """, unsafe_allow_html=True)
                        
                        total_pecas_acumulada = 0
                        total_reais_produzido = 0.0
                        
                        for _, row_cupom in df_filtro_cost.iterrows():
                            qtd_p = int(row_cupom['qtd_pecas'])
                            val_t = float(row_cupom['valor_total'])
                            total_pecas_acumulada += qtd_p
                            total_reais_produzido += val_t
                            
                            st.markdown(f"""
                                <div style='display: flex; justify-content: space-between; font-size: 13px; color: #ECEFF1; margin-bottom: 4px;'>
                                    <span>🪡 {row_cupom['operacao']} (x{qtd_p})</span>
                                    <span>R$ {val_t:,.2f}</span>
                                </div>
                            """, unsafe_allow_html=True)
                            
                        st.markdown(f"""
                                <hr style='border: 0; border-top: 1px dashed #555555; margin: 12px 0;'>
                                <div style='display: flex; justify-content: space-between; font-weight: bold; font-size: 15px; color: #FFFFFF;'>
                                    <span>💰 VALOR TOTAL PRODUZIDO:</span>
                                    <span style='color: #69F0AE;'>R$ {total_reais_produzido:,.2f}</span>
                                </div>
                                <div style='font-size: 11px; color: #90A4AE; margin-top: 6px;'>Volume de peças processadas no dia: {total_pecas_acumulada} unidades</div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info(f"💡 Nenhum registro de eficiência horária localizado para o dia {data_busca_formatada} neste período.")

            st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
            # 📊 OPÇÃO 1: VISUALIZANDO EXTRATO GERAL (E.G) — VALOR TOTAL SÓ NO PRIMEIRO MÊS
            # ==============================================================================
            if st.session_state.sub_menu_extratos == "E.G":
                st.subheader(f"📂 Visualizando: Extrato Geral ({mes_ext_sel}/{ano_ext_sel})")
                
                conn = sqlite3.connect("dlr_confecoes_v3.db")
                # CORREÇÃO DE OURO: Trocado 'libro_caixa' para 'livro_caixa' (com V)
                df_eg = pd.read_sql_query(f"""
                    SELECT id as 'ID_T', data_movimento as 'Data', descricao as 'Descrição', tipo_movimentacao, valor_total, parcela_atual, valor_parcela
                    FROM livro_caixa 
                    WHERE mes_ano = '{periodo_ext_chave}'
                """, conn)
                conn.close()
                
                if not df_eg.empty:
                    linhas_eg_filtradas = []
                    for idx_eg, row_eg in df_eg.iterrows():
                        tipo_m = row_eg['tipo_movimentacao']
                        parc_atual = int(row_eg['parcela_atual'])
                        
                        # REGRA DE OURO: Se for Vale, só exibe no Extrato Geral se for a parcela 1 (mês de origem)
                        if tipo_m == "Vale":
                            if parc_atual == 1:
                                v_exibir = f"- R$ {float(row_eg['valor_total']):,.2f}"
                                lines_eg_f = {"Data": row_eg['Data'], "Descrição": row_eg['Descrição'], "Valor": v_exibir}
                                linhas_eg_filtradas.append(lines_eg_f)
                        else:
                            v_exibir = f"- R$ {float(row_eg['valor_parcela']):,.2f}" if tipo_m == "Saída" else f"+ R$ {float(row_eg['valor_parcela']):,.2f}"
                            linhas_eg_filtradas.append({"Data": row_eg['Data'], "Descrição": row_eg['Descrição'], "Valor": v_exibir})
                    
                    if linhas_eg_filtradas:
                        df_eg_final = pd.DataFrame(linhas_eg_filtradas)
                        
                        # 🚀 PLANILHA MASTER 100% LIBERADA: Mudamos para disabled=False para você conseguir editar!
                        tabela_editada_eg = st.data_editor(
                            df_eg_final,
                            column_config={
                                "Data": st.column_config.TextColumn("Data", width=120, disabled=True),
                                "Descrição": st.column_config.TextColumn("Descrição", width=480, disabled=False), # <=== LIBERADO!
                                "Valor": st.column_config.TextColumn("Valor", width=150, disabled=False)         # <=== LIBERADO!
                            },
                            hide_index=True, use_container_width=True, key=f"tab_extrato_eg_view_{periodo_ext_chave}"
                        )
                        
                        # 💾 MOTOR DE SALVAMENTO INTELIGENTE: Pega o que você digitou e atualiza o banco de dados
                        chave_cache_eg = f"tab_extrato_eg_view_{periodo_ext_chave}"
                        if chave_cache_eg in st.session_state and st.session_state[chave_cache_eg]["edited_rows"]:
                            conn = sqlite3.connect("dlr_confecoes_v3.db")
                            cursor = conn.cursor()
                            for idx_s, mudancas in st.session_state[chave_cache_eg]["edited_rows"].items():
                                # Descobre o ID real da linha do banco usando o DataFrame bruto de cima
                                id_reg_eg = int(df_eg.iloc[int(idx_s)]['ID_T'])
                                tipo_mov_original = str(df_eg.iloc[int(idx_s)]['tipo_movimentacao']).strip()
                                
                                if "Descrição" in mudancas:
                                    cursor.execute("UPDATE livro_caixa SET descricao = ? WHERE id = ?", (str(mudancas["Descrição"]).strip(), id_reg_eg))
                                
                                if "Valor" in mudancas:
                                    # Limpa os sinais de R$, espaços e converte pontos/vírgulas para número real puro
                                    valor_limpo = str(mudancas["Valor"]).replace("R$", "").replace(" ", "").replace("-", "").replace("+", "").replace(",", ".").strip()
                                    try:
                                        v_float = float(valor_limpo)
                                        # Se for um vale de parcela 1, atualiza a coluna valor_total, senão atualiza a valor_parcela
                                        if tipo_mov_original == "Vale":
                                            cursor.execute("UPDATE livro_caixa SET valor_total = ? WHERE id = ?", (v_float, id_reg_eg))
                                        else:
                                            cursor.execute("UPDATE livro_caixa SET valor_parcela = ? WHERE id = ?", (v_float, id_reg_eg))
                                    except ValueError:
                                        pass
                            conn.commit()
                            conn.close()
                            st.rerun()
                else:
                    st.info(f"💡 Nenhuma movimentação registrada no Extrato Geral em {periodo_ext_chave}.")

            # ==============================================================================
            # 💸 OPÇÃO 2: VISUALIZANDO EXTRATO DE VALE (E.V) — COM BOTÃO DE CANCELAR VALE
            # ==============================================================================
            elif st.session_state.sub_menu_extratos == "E.V":
                st.subheader(f"📂 Visualizando: Extrato de Vales ({mes_ext_sel}/{ano_ext_sel})")
                
                conn = sqlite3.connect("dlr_confecoes_v3.db")
                # CORREÇÃO DE OURO 1: Trocado de 'libro_caixa' para 'livro_caixa' (com V)
                df_ev = pd.read_sql_query(f"""
                    SELECT id as 'ID_T', data_movimento as 'Data', descricao as 'Descrição', valor_parcela as 'Valor do Vale'
                    FROM livro_caixa 
                    WHERE mes_ano = '{periodo_ext_chave}' AND tipo_movimentacao = 'Vale'
                """, conn)
                conn.close()
                
                if not df_ev.empty:
                    df_ev_copy = df_ev.copy()
                    df_ev_copy['Valor do Vale'] = df_ev_copy['Valor do Vale'].apply(lambda x: f"- R$ {float(x):,.2f}")
                    
                    st.data_editor(
                        df_ev_copy[['Data', 'Descrição', 'Valor do Vale']],
                        column_config={
                            "Data": st.column_config.TextColumn("Data", width=120, disabled=True),
                            "Descrição": st.column_config.TextColumn("Funcionário / Parcelamento", width=480, disabled=True),
                            "Valor do Vale": st.column_config.TextColumn("Valor da Parcela", width=150, disabled=True)
                        },
                        hide_index=True, use_container_width=True, key=f"tab_extrato_ev_view_{periodo_ext_chave}"
                    )
                    
                    # --- ❌ SEÇÃO DE CANCELAMENTO OFICIAL DE VALES ---
                    st.markdown("<br>", unsafe_allow_html=True)
                    lista_vales_cancelar = {f"{row['Descrição']} (Ref ID: {row['ID_T']})": row['ID_T'] for idx, row in df_ev.iterrows()}
                    
                    vale_sel_cancelar = st.selectbox("❌ Cancelar / Estornar Vale do Mês:", ["Selecionar vale para cancelar..."] + list(lista_vales_cancelar.keys()))
                    
                    if vale_sel_cancelar != "Selecionar vale para cancelar...":
                        id_vale_del = lista_vales_cancelar[vale_sel_cancelar]
                        st.warning(f"⚠️ **Aviso de Cancelamento:** Deseja estornar e cancelar permanentemente este lançamento de vale do cofre?")
                        
                        col_c_v_s, col_c_v_n = st.columns(2)
                        with col_c_v_s:
                            if st.button("✅ Confirmar Cancelamento", use_container_width=True, type="primary"):
                                conn = sqlite3.connect("dlr_confecoes_v3.db")
                                cursor = conn.cursor()
                                # CORREÇÃO DE OURO 2: Trocado de 'libro_caixa' para 'livro_caixa'
                                cursor.execute("SELECT descricao, valor_parcela FROM livro_caixa WHERE id = ?", (id_vale_del,))
                                info_v = cursor.fetchone()
                                if info_v:
                                    desc_v, v_parc = info_v
                                    nome_f_limpo = desc_v.replace("Vale Funcionário: ", "").split("(")[0].strip()
                                    cursor.execute("UPDATE historico_folha_pagamento SET total_vales = MAX(0.0, total_vales - ?) WHERE nome = ? AND mes_ano = ?", (v_parc, nome_f_limpo, periodo_ext_chave))
                                
                                # CORREÇÃO DE OURO 3: Trocado de 'libro_caixa' para 'livro_caixa'
                                cursor.execute("DELETE FROM livro_caixa WHERE id = ?", (id_vale_del,))
                                conn.commit(); conn.close()
                                st.success("🎉 Vale cancelado e estornado da folha com sucesso!")
                                st.rerun()
                        with col_c_v_n:
                            if st.button("❌ Manter Vale Ativo", use_container_width=True): st.rerun()
                else:
                    st.info(f"💡 Nenhum adiantamento ou vale registrado em {periodo_ext_chave}.")

            # ==============================================================================
            # 📄 OPÇÃO 3: FOLHA DE PAGAMENTO (F.P) — INTEGRAÇÃO DEFINITIVA DO LIVRO CAIXA V3
            # ==============================================================================
            elif st.session_state.sub_menu_extratos == "F.P":
                st.markdown(f"### 📂 Visualizando: Espelho de Folha de Pagamentos ({mes_ext_sel}/{ano_ext_sel})")
                st.write("Abaixo está o fechamento financeiro do mês com cálculo automático de horas e desconto de vales:")
                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                
                conn = sqlite3.connect("dlr_confecoes_v3.db")
                # Puxa as informações base da folha histórica das colaboradoras
                df_folha_bruta = pd.read_sql_query(f"SELECT id, nome as 'Funcionário', tipo_pagamento as 'Tipo', valor_base as 'Base (R$)', status_pagto as 'Status' FROM historico_folha_pagamento WHERE mes_ano = '{periodo_ext_chave}'", conn)
                
                linhas_folha_calculada = []
                
                if not df_folha_bruta.empty:
                    cursor = conn.cursor()
                    for idx, row_f in df_folha_bruta.iterrows():
                        f_id = int(row_f["id"])
                        f_nome = str(row_f["Funcionário"]).strip()
                        f_tipo = str(row_f["Tipo"]).strip()
                        f_base = float(row_f["Base (R$)"])
                        f_status = str(row_f["Status"]).strip()
                        
                         # 🚀 MOTOR DE DESCONTO SINCRONIZADO: Busca rigorosamente por tipo_movimentacao = 'Vale'
                        nome_busca_minusculo = f"%{f_nome.lower()}%"
                        
                        cursor.execute("""
                            SELECT SUM(valor_parcela) 
                            FROM livro_caixa 
                            WHERE mes_ano = ? 
                              AND tipo_movimentacao = 'Vale' 
                              AND LOWER(descricao) LIKE ?
                        """, (periodo_ext_chave, nome_busca_minusculo))
                        res_vales_cx = cursor.fetchone()
                        
                        # 🚀 DESEMPACOTAÇÃO SEGURA: Rasga a tupla do SQLite pegando a posição [0] com tratamento de nulos
                        f_vales = float(res_vales_cx[0]) if res_vales_cx and res_vales_cx[0] is not None else 0.0
                        
                        # ⚙️ ENGENHARIA DE CÁLCULO FINANCEIRO
                        if f_tipo == "Por hora":
                            # Busca as horas reais registradas no Importar Ponto
                            cursor.execute("SELECT horas_totais FROM registro_ponto_horistas WHERE costureira = ? AND mes_ano = ?", (f_nome, periodo_ext_chave))
                            res_pt = cursor.fetchone()
                            horas_reais = float(res_pt[0]) if res_pt and res_pt[0] is not None else 0.0
                            f_liquido = (f_base * horas_reais) - f_vales
                        else:
                            # Funcionários Fixos e por Operação: Salário Base - Vales coletados
                            f_liquido = f_base - f_vales
                            
                        if f_liquido < 0: f_liquido = 0.0
                        
                        linhas_folha_calculada.append({
                            "ID_FP": f_id, "Funcionário": f_nome, "Tipo": f_tipo,
                            "Base (R$)": f_base, "Vales (R$)": f_vales, "Líquido (R$)": f_liquido, "Status": f_status
                        })
                    cursor.close()
                conn.close()

                # --- INTERFACE DE EXIBIÇÃO EM TABELA COMPACTA ---
                if linhas_folha_calculada:
                    df_fp_calculado = pd.DataFrame(linhas_folha_calculada)
                    chave_cache_ext_fp = f"tabela_folha_pagto_extrato_v4_{periodo_ext_chave}"
                    
                    st.data_editor(
                        df_fp_calculado,
                        column_config={
                            "ID_FP": None,
                            "Funcionário": st.column_config.TextColumn("👤 Funcionário", width=180, disabled=True),
                            "Tipo": st.column_config.TextColumn("🗂️ Tipo", width=100, disabled=True),
                            "Base (R$)": st.column_config.NumberColumn("💰 Base (R$)", format="R$ %.2f", width=110, disabled=True),
                            "Vales (R$)": st.column_config.NumberColumn("📉 Vales (R$)", format="R$ %.2f", width=110, disabled=True),
                            "Líquido (R$)": st.column_config.NumberColumn("💵 Líquido (R$)", format="R$ %.2f", width=120, disabled=True),
                            "Status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Pago"], required=True, width=110)
                        },
                        hide_index=True, use_container_width=True, key=chave_cache_ext_fp
                    )
                    
                    # Salva alterações de Status (Pendente / Pago) de forma automática
                    if chave_cache_ext_fp in st.session_state and st.session_state[chave_cache_ext_fp]["edited_rows"]:
                        conn = sqlite3.connect("dlr_confecoes_v3.db"); cursor = conn.cursor()
                        for idx_s, mudancas in st.session_state[chave_cache_ext_fp]["edited_rows"].items():
                            id_reg_fp = int(df_fp_calculado.iloc[int(idx_s)]["ID_FP"])
                            if "Status" in mudancas:
                                cursor.execute("UPDATE historico_folha_pagamento SET status_pagto = ? WHERE id = ?", (mudancas["Status"], id_reg_fp))
                        conn.commit(); conn.close(); st.rerun()
                else:
                    st.info("💡 Nenhuma movimentação de folha localizada para o período selecionado.")              
    # ==============================================================================
# 🚪 RECONECTOR MASTER DLR — LOGOUT DA PORTA DO ADMIN E ENTRADA DA FÁBRICA
# ==============================================================================
# Encostado na parede esquerda (zero espaços)! Isso fecha a gaveta do Admin e abre a do Manual!
if st.session_state.sistema_autorizado and st.session_state.perfil_usuario == "Manual":
    menu_manual_ativo = st.session_state.pagina_manual_atual
    
    # 📦 INTERFACE 1: ENTRADA DE LOTES (FORNECEDOR) — PROPORÇÃO COMPACTA FIEL AO PRINT
    if menu_manual_ativo == "📦 Entrada de Lotes (Fornecedor)":
        if "sub_menu_manual_lotes" not in st.session_state:
            st.session_state.sub_menu_manual_lotes = "A.P"
            
        # CSS Master local: joga o conteúdo para baixo (alinhado à lateral) e limita a largura máxima
        st.markdown("""
            <style>
                .stMainBlockContainer {
                    padding-top: 65px !important;
                }
                h1, h3 {
                    font-size: 24px !important;
                    margin-bottom: 12px !important;
                }
                /* Trava os 4 cards para ficarem curtos na horizontal e não esticarem feito chiclete */
                .bloco-cards-curtos {
                    max-width: 820px !important;
                    margin: 0px !important;
                }
            </style>
        """, unsafe_allow_html=True)
            
        # --- 📄 RETÂNGULOS DO TOPO COM ORDENS INVERTIDAS (A.P PRIMEIRO, C.L SEGUNDO) ---
        col_sm_m1, col_sm_m2, col_sm_esp = st.columns([2.0, 2.0, 6])
        
        with col_sm_m1:
            # AGORA O ANDAMENTO DE PRODUÇÃO FICA NA PRIMEIRA POSIÇÃO DA ESQUERDA
            if st.button("📈 Andamento de Produção (A.P)", use_container_width=True, key="btn_sub_ap_manual_final_v2_inv"):
                st.session_state.sub_menu_manual_lotes = "A.P"
                st.rerun()
                
        with col_sm_m2:
            # O CADASTRAR LOTE PASSA PARA A SEGUNDA POSIÇÃO
            if st.button("📄 Cadastrar Lote (C.L)", use_container_width=True, key="btn_sub_cl_manual_final_v2_inv"):
                st.session_state.sub_menu_manual_lotes = "C.L"
                st.rerun()

        st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px; border: 0; border-top: 1px solid #424242;'>", unsafe_allow_html=True)

        # ==============================================================================
        # 📄 SUB-TELA A: CADASTRO E RECEPÇÃO DE NOVOS LOTES DE TECIDO (C.L) — LARGURA LIBERADA
        # ==============================================================================
        if st.session_state.sub_menu_manual_lotes == "C.L":
            # 🚀 INJEÇÃO MÁGICA: Destranca a largura máxima apenas para este formulário de trabalho!
            st.markdown("""
                <style>
                    div[data-testid="stForm"] {
                        max-width: 100% !important;
                        margin: 0px !important;
                        padding: 20px !important;
                    }
                </style>
            """, unsafe_allow_html=True)

            st.markdown("<h3 style='margin:0; padding:0;'>📦 Cadastro e Recepção de Novos Lotes</h3>", unsafe_allow_html=True)
            st.write("Preencha os dados da nota do fornecedor para dar entrada oficial na matéria-prima:")
            
            with st.form(key="form_cadastro_lotes_manual_clean_v5", clear_on_submit=True):
                fornecedor_input = st.text_input("Nome do Fornecedor / Marca").strip()
                of_input = st.text_input("Número da O.F (Ordem de Fabricação)").strip()
                referencia_input = st.text_input("Referência do Modelo (Peça)").strip()
                
                # --- LINHA DE COMPONENTES 1: QUANTIDADES E VALORES ---
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    qtd_input = st.number_input("Qtd na Nota", min_value=1, step=1, value=1)
                with col_c2:
                    preco_input = st.number_input("Preço Unitário (R$)", min_value=0.0, step=0.10, format="%.2f")
                
                # --- LINHA DE COMPONENTES 2: DATAS E PRIORIDADE ---
                col_c3, col_c4, col_c5 = st.columns([1.5, 1.5, 1])
                with col_c3:
                    dt_chegada_sel = st.date_input("📅 Chegada", value=datetime.date.today())
                with col_c4:
                    dt_entrega_sel = st.date_input("📅 Entrega", value=datetime.date.today())
                with col_c5:
                    prio_input = st.selectbox("🔥 Prioridade", ["Não", "Sim"])
                    
                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                btn_salvar_lote = st.form_submit_button("📦 Registrar Entrada do Lote", use_container_width=True)
                
            if btn_salvar_lote:
                if not fornecedor_input or not of_input or not referencia_input:
                    st.error("❌ Todos os campos de texto são obrigatórios!")
                elif preco_input <= 0:
                    st.error("❌ O preço unitário deve ser maior que R$ 0,00!")
                else:
                    dt_chegada_txt = dt_chegada_sel.strftime("%d/%m/%Y")
                    dt_entrega_txt = dt_entrega_sel.strftime("%d/%m/%Y")
                    
                    conn = sqlite3.connect("dlr_confecoes_v3.db")
                    cursor = conn.cursor()
                    
                    # 🚀 ENGENHARIA DE SEGURANÇA: Cria a coluna nova na tabela caso ela não exista no HD
                    try: cursor.execute("ALTER TABLE lotes_gerais ADD COLUMN mes_ano_cadastro TEXT DEFAULT ''")
                    except: pass
                    
                    try:
                        # Tranca de forma vitalícia a chave do mês do calendário ativo selecionado (ex: "10/2026")
                        cursor.execute("""
                            INSERT INTO lotes_gerais (data_cadastro, data_entrega, fornecedor, of, referencia, qtd_prevista, preco, status, porcentagem_pronta, qtd_pronta, prioridade, mes_ano_cadastro) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pendente', 0, 0, ?, ?)
                        """, (dt_chegada_txt, dt_entrega_txt, fornecedor_input, of_input, referencia_input, qtd_input, preco_input, prio_input, periodo_ativo_chave))
                        conn.commit()
                        st.success(f"🎉 Lote O.F {of_input} cadastrado e preso com sucesso no painel de {mes_ativo_txt}!")
                    except sqlite3.IntegrityError:
                        st.error("⚠️ Esse número de O.F já existe no banco de dados!")
                    finally:
                        conn.close()
        # 📈 SUB-TELA B: ANDAMENTO DE PRODUÇÃO E LINHA DO TEMPO DE LOTES (A.P) — UNIFICADO
        # ==============================================================================
        elif st.session_state.sub_menu_manual_lotes == "A.P":
            # --- SELETORES GERAIS DE FILTRO NA PARTE SUPERIOR ---
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                mes_ext_sel = st.selectbox("Filtrar por Mês:", lista_meses_sistema, index=lista_meses_sistema.index(st.session_state.calendario_master_mes), key="filtro_mes_manual_v15_final")
            with col_f2:
                ano_ext_sel = st.selectbox("Filtrar por Ano:", lista_anos_sistema, index=lista_anos_sistema.index(st.session_state.calendario_master_ano), key="filtro_ano_manual_v15_final")
                
            if mes_ext_sel != st.session_state.calendario_master_mes or ano_ext_sel != st.session_state.calendario_master_ano:
                st.session_state.calendario_master_mes = mes_ext_sel
                st.session_state.calendario_master_ano = ano_ext_sel
                st.rerun()

            # --- MOTOR DE CÁLCULO DOS CARDS CONTADORES ---
            qtd_pendentes = 0
            qtd_em_producao = 0
            qtd_vencidos = 0
            qtd_concluidos = 0
            data_hoje_dt = datetime.date.today()
            
            conn = sqlite3.connect("dlr_confecoes_v3.db")
            cursor = conn.cursor()
            try: cursor.execute("ALTER TABLE lotes_gerais ADD COLUMN mes_ano_cadastro TEXT DEFAULT ''")
            except: pass
            
            # Captura todas as colunas necessárias em uma busca única e limpa
            cursor.execute("SELECT status, data_entrega, prioridade, data_cadastro, mes_ano_cadastro FROM lotes_gerais")
            todos_lotes_db = cursor.fetchall()
            conn.close()
            
            for lote_db in todos_lotes_db:
                status_lote = str(lote_db[0]).strip()
                dt_ent_db = lote_db[1]
                prio_db = lote_db[2]
                dt_cad_db = lote_db[3]
                mes_ano_cad_db = lote_db[4]
                
                # TRAVA RESTRITA: Se tiver a chave oculta de cadastro, usa ela! Senão, pega do MM/AAAA da data de chegada antiga.
                chave_conferencia = mes_ano_cad_db if (mes_ano_cad_db and mes_ano_cad_db != '') else f"{dt_cad_db[3:5]}/{dt_cad_db[6:10]}"
                
                if chave_conferencia == periodo_ativo_chave:
                    try: dt_entrega_dt = dt_class.strptime(dt_ent_db, "%d/%m/%Y").date()
                    except: dt_entrega_dt = None
                    
                    # Contagem exata por status para alimentar os 4 cards do topo
                    if status_lote == "Pendente": 
                        qtd_pendentes += 1
                    elif status_lote == "Em produção": 
                        qtd_em_producao += 1
                    elif status_lote == "Concluído": 
                        qtd_concluidos += 1
                    
                    try:
                        if dt_entrega_dt and data_hoje_dt > dt_entrega_dt and status_lote != "Concluído":
                            qtd_vencidos += 1
                    except: pass

            # --- CARDS COMPACTOS COM AS MEDIDAS DE 120PX DE ALTURA E FONTES DE 30PX ---
            st.markdown(f"""
                <div style='width: 100%; display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 10px; margin-bottom: 10px;'>
                    <div style='background-color: #EF6C00; padding: 10px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center; height: 120px;'>
                        <div style='font-size: 18px; font-weight: normal; color: #FFE0B2; opacity: 0.9;'>Lotes Pendentes</div>
                        <h4 style='margin-top: 4px; margin-bottom: 0px; color: white; font-size: 30px; font-weight: bold;'>{qtd_pendentes}</h4>
                    </div>
                    <div style='background-color: #2E7D32; padding: 10px 5px; border-radius: 6px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center; height: 120px;'>
                        <div style='font-size: 18px; font-weight: normal; color: #E8F5E9; opacity: 0.9;'>Em Produção</div>
                        <h4 style='margin-top: 4px; margin-bottom: 0px; color: white; font-size: 30px; font-weight: bold;'>{qtd_em_producao}</h4>
                    </div>
                    <div style='background-color: #C62828; padding: 10px 5px; border-radius: 6px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center; height: 120px;'>
                        <div style='font-size: 18px; font-weight: normal; color: #FFEBEE; opacity: 0.9;'>Lotes Vencidos</div>
                        <h4 style='margin-top: 4px; margin-bottom: 0px; color: white; font-size: 30px; font-weight: bold;'>{qtd_vencidos}</h4>
                    </div>
                    <div style='background-color: #1565C0; padding: 10px 5px; border-radius: 6px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center; height: 120px;'>
                        <div style='font-size: 18px; font-weight: normal; color: #E3F2FD; opacity: 0.9;'>Concluídos</div>
                        <h4 style='margin-top: 4px; margin-bottom: 0px; color: white; font-size: 30px; font-weight: bold;'>{qtd_concluidos}</h4>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("<hr style='margin-top: 15px; margin-bottom: 10px; border: 0; border-top: 1px solid #424242;'>", unsafe_allow_html=True)
            st.write("📋 **Dica do Setor:** Altere entre Pendente e Em produção. Lotes ativos rolam de mês automaticamente!")

        # --- MONTAGEM DA PLANILHA EXCLUSIVA DO MÊS SELECIONADO ---
            linhas_tabela_manual = []
            conn = sqlite3.connect("dlr_confecoes_v3.db")
            df_lotes_brutos = pd.read_sql_query("SELECT id, data_cadastro, data_inicio_producao, data_entrega, fornecedor, of, referencia, qtd_prevista, preco, status, porcentagem_pronta, qtd_pronta, prioridade, mes_ano_cadastro FROM lotes_gerais", conn)
            conn.close()

            if not df_lotes_brutos.empty:
                for idx, row in df_lotes_brutos.iterrows():
                    dt_cad = row["data_cadastro"]; status_at = row["status"]; prio_at = row["prioridade"]
                    dt_ent = row["data_entrega"]; m_a_cad = row["mes_ano_cadastro"]
                    
                    # FILTRO RESTRITO EXIGIDO: O lote fica preso apenas no mês em que você clicou em salvar!
                    chave_conferencia_tabela = m_a_cad if (m_a_cad and m_a_cad != '') else f"{dt_cad[3:5]}/{dt_cad[6:10]}"
                    
                    if chave_conferencia_tabela == periodo_ativo_chave:
                        try: dt_chegada_dt = dt_class.strptime(dt_cad, "%d/%m/%Y").date()
                        except: dt_chegada_dt = data_hoje_dt
                        
                        # Motor de dias pendentes contínuo até HOJE (Zerado automaticamente se concluído)
                        if status_at == "Concluído":
                            dias_pendente = 0
                        else:
                            dias_pendente = (data_hoje_dt - dt_chegada_dt).days
                            if dias_pendente < 0: dias_pendente = 0

                        if status_at == "Pendente": cor_bola = "🟠"
                        elif status_at == "Em produção": cor_bola = "🟢"
                        else: cor_bola = "🔵"
                        
                        try:
                            dt_entrega_dt = dt_class.strptime(dt_ent, "%d/%m/%Y").date()
                            if dt_entrega_dt and data_hoje_dt > dt_entrega_dt and status_at != "Concluído":
                                cor_bola = "🔴"
                        except: pass
                        
                        signal_final = f"{cor_bola} {cor_bola}" if prio_at == "Sim" else cor_bola

                        linhas_tabela_manual.append({
                            "ID_T": int(row["id"]), "🚨 Alerta": signal_final, "Nome do fornecedor": row["fornecedor"],
                            "Nº do O.F": row["of"], "Referência": row["referencia"], "Quantidade Total de Peças na Nota": int(row["qtd_prevista"]),
                            "Dias pendente": int(dias_pendente), "Data chegada": dt_cad, "Data para entrega": dt_ent,
                            "Preço Unitário": float(row["preco"]), "Status": status_at, "Porcentagem já produzido": f"{row['porcentagem_pronta']}%",
                            "Peças Prontas Reais": int(row["qtd_pronta"]), "Prioridade": prio_at
                        })

            # --- PLANILHA ULTRA ESPREMIDADE COMPACTA EM LARGURA ---
            if linhas_tabela_manual:
                df_manual_visao = pd.DataFrame(linhas_tabela_manual)
                chave_editor_man_lotes = f"tabela_esteira_manual_DL_{periodo_ativo_chave}"
                
                tabela_editada_man = st.data_editor(
                    df_manual_visao,
                    column_config={
                        "ID_T": None,
                        "🚨 Alerta": st.column_config.TextColumn("🚨 Alerta", width=55, disabled=True),
                        "Nome do fornecedor": st.column_config.TextColumn("Nome do fornecedor", width=110, disabled=True),
                        "Nº do O.F": st.column_config.TextColumn("Nº do O.F", width=75, disabled=True),
                        "Referência": st.column_config.TextColumn("Referência", width=75, disabled=True),
                        "Quantidade Total de Peças na Nota": st.column_config.NumberColumn("Qtd Nota", width=75, disabled=True),
                        "Dias pendente": st.column_config.NumberColumn("Dias Pend", width=65, disabled=True),
                        "Data chegada": st.column_config.TextColumn("Chegada", width=85, disabled=True),
                        "Data para entrega": st.column_config.TextColumn("Entrega", width=85, disabled=True),
                        "Preço Unitário": st.column_config.NumberColumn("Preço Un", format="R$ %.2f", width=80, disabled=True),
                        "Status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Em produção"], required=True, width=105),
                        "Porcentagem já produzido": st.column_config.SelectboxColumn("Porcent", options=["0%", "10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%"], required=True, width=75),
                        "Peças Prontas Reais": st.column_config.NumberColumn("Pçs Reais", format="%d", disabled=True),
                        "Prioridade": st.column_config.SelectboxColumn("Prioridade", options=["Não", "Sim"], required=True, width=75)
                    },
                    hide_index=True, use_container_width=True, key=chave_editor_man_lotes
                )
                
                # MOTOR DE ATUALIZAÇÃO EM TEMPO REAL NO COFRE V3
                if chave_editor_man_lotes in st.session_state and st.session_state[chave_editor_man_lotes]["edited_rows"]:
                    conn = sqlite3.connect("dlr_confecoes_v3.db")
                    cursor = conn.cursor()
                    for idx_s, mudancas in st.session_state[chave_editor_man_lotes]["edited_rows"].items():
                        id_lote_db = int(df_manual_visao.iloc[int(idx_s)]["ID_T"])
                        if "Status" in mudancas:
                            cursor.execute("UPDATE lotes_gerais SET status = ? WHERE id = ?", (mudancas["Status"], id_lote_db))
                            if mudancas["Status"] == "Em produção":
                                cursor.execute("UPDATE lotes_gerais SET data_inicio_producao = ? WHERE id = ? AND (data_inicio_producao = '' OR data_inicio_producao IS NULL)", (datetime.datetime.now().strftime("%d/%m/%Y"), id_lote_db))
                            # 🚀 COMPUTAÇÃO DE CAIXA IMEDIATA: Se fechar o lote na fábrica, crava a data de faturamento do dia atual!
                            elif mudancas["Status"] == "Concluído":
                                cursor.execute("UPDATE lotes_gerais SET data_inicio_producao = ? WHERE id = ?", (datetime.datetime.now().strftime("%d/%m/%Y"), id_lote_db))
                        if "Porcentagem já produzido" in mudancas:
                            cursor.execute("UPDATE lotes_gerais SET porcentagem_pronta = ? WHERE id = ?", (int(mudancas["Porcentagem já produzido"].replace("%", "")), id_lote_db))
                        if "Prioridade" in mudancas:
                            cursor.execute("UPDATE lotes_gerais SET prioridade = ? WHERE id = ?", (mudancas["Prioridade"], id_lote_db))
                    conn.commit(); conn.close(); st.rerun()

                # --- LIXEIRA DE O.F NO RODAPÉ ---
                st.markdown("<br>", unsafe_allow_html=True)
                lista_ofs_excluir = [str(linha["Nº do O.F"]) for linha in linhas_tabela_manual]
                of_selecionada_excluir = st.selectbox("🗑️ Selecione O.F para excluir:", ["Selecionar..."] + lista_ofs_excluir, key=f"lix_of_manual_f_{periodo_ativo_chave}")
                
                if of_selecionada_excluir != "Selecionar...":
                    st.warning(f"⚠️ Deseja apagar permanentemente a O.F {of_selecionada_excluir}?")
                    c_del_s, c_del_n = st.columns(2)
                    with c_del_s:
                        if st.button("✅ Sim, excluir definitivo", key="btn_del_of_manual_AP"):
                            conn = sqlite3.connect("dlr_confecoes_v3.db"); cursor = conn.cursor()
                            cursor.execute("DELETE FROM lotes_gerais WHERE of = ?", (of_selecionada_excluir.strip(),))
                            conn.commit(); conn.close(); st.success("Deletado!"); st.rerun()
                    with c_del_n:
                        if st.button("❌ Não, cancelar", key="btn_cancel_del_of_manual_AP"): st.rerun()
            else:
                st.info("💡 Nenhum lote de produção ativo localizado para este período no Chão de Fábrica.")

                # ⏱️ RECONECTOR MASTER DLR — PROCESSO DE LANÇAMENTO DE HORA EM HORA
# ==============================================================================
# Encostado na parede esquerda (zero espaços)! Força o Python a ler a aba sem travas!
if st.session_state.sistema_autorizado and st.session_state.perfil_usuario == "Manual":
    menu_manual_verificar = st.session_state.pagina_manual_atual
    
    if menu_manual_verificar == "⏱️ Produção de Hora em Hora":
        st.title("⏱️ Eficiência Horária — Produção de Hora em Hora")
        st.markdown(f"📊 Registre os ciclos de produção de hoje no período de: **{mes_ativo_txt} de {ano_ativo_txt}**")
        st.markdown("<br>", unsafe_allow_html=True)

        # --- GAVETA DE MEMÓRIA DO COFRE PARA AUTO-LIMPEZA HORÁRIA ---
        if "phh_costureira_clean" not in st.session_state: st.session_state.phh_costureira_clean = ""
        if "phh_operacao_clean" not in st.session_state: st.session_state.phh_operacao_clean = "Escolha uma operação..."
        if "phh_qtd_clean" not in st.session_state: st.session_state.phh_qtd_clean = 1

        # --- MOTOR DE PUXADA DINÂMICA DAS OPERAÇÕES DA ADMINISTRAÇÃO ---
        conn = sqlite3.connect("dlr_confecoes_v3.db")
        cursor = conn.cursor()
        
        # Preventivo: Garante a criação da tabela de operações para não dar erro de leitura
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operacoes_frente (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nome_operacao TEXT UNIQUE, preco_peca REAL
            )
        """)
        cursor.execute("SELECT nome_operacao FROM operacoes_frente ORDER BY nome_operacao ASC")
        lista_ops_db = [row[0] for row in cursor.fetchall()]
        
        # --- MOTOR DE PUXADA DINÂMICA FILTRANDO POR MARCAÇÃO DA LISTA (NOMES LIMPOS) ---
        conn = sqlite3.connect("dlr_confecoes_v3.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT nome_operacao FROM operacoes_frente ORDER BY nome_operacao ASC")
        lista_ops_db = [row[0] for row in cursor.fetchall()]
        
        # 🚀 FILTRO SECO: Busca os nomes da tabela onde o status_cadastro foi marcado como 'Sim'
        cursor.execute("SELECT nome FROM funcionarios WHERE status_cadastro = 'Sim'")
        # O row[0] limpa os parênteses (,) e aspas trazendo o nome puro em texto!
        lista_funcs_phh = [row[0] for row in cursor.fetchall()]
        conn.close()

        # --- 🎨 FORMULÁRIO DE LANÇAMENTO DA EFICIÊNCIA HORÁRIA ---
        with st.form(key="form_producao_hora_hora_clean", clear_on_submit=True):
            col_ph1, col_ph2, col_ph3 = st.columns([2, 2, 1.2])
            
            with col_ph1:
                cost_phh_sel = st.selectbox(
                    "Selecionar Costureira Horista", 
                    lista_funcs_phh if lista_funcs_phh else ["Nenhuma cadastrada"],
                    key="phh_costureira_clean"
                )
            with col_ph2:
                operacao_phh_sel = st.selectbox(
                    "Selecionar Tipo de Operação",
                    ["Escolha uma operação..."] + lista_ops_db,
                    key="phh_operacao_clean"
                )
            with col_ph3:
                qtd_phh_input = st.number_input(
                    "Quantidade de Peças", 
                    min_value=1, 
                    step=1, 
                    key="phh_qtd_clean"
                )
                
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            btn_registrar_phh = st.form_submit_button("⚡ Registrar Ciclo Horário", use_container_width=True)

        # --- ⚙️ MOTOR DE VALORIZAÇÃO FINANCEIRA INTEGRADO COM PREÇOS DO ADMIN ---
        if btn_registrar_phh:
            if operacao_phh_sel == "Escolha uma operação..." or cost_phh_sel == "Nenhuma cadastrada":
                st.error("❌ Operação Recusada! Selecione uma Costureira e uma Operação válida!")
            elif qtd_phh_input <= 0:
                st.error("❌ Operação Recusada! A quantidade deve ser maior que zero!")
            else:
                conn = sqlite3.connect("dlr_confecoes_v3.db")
                cursor = conn.cursor()
                cursor.execute("SELECT preco_peca FROM operacoes_frente WHERE nome_operacao = ?", (operacao_phh_sel,))
                res_preco = cursor.fetchone()
                
                # 🚀 CORREÇÃO DE OURO: Adicionado [0] para extrair o preço limpo de dentro da tupla!
                preco_unitario_op = float(res_preco[0]) if res_preco else 0.0
                valor_total_calculado = preco_unitario_op * qtd_phh_input
                data_hoje_txt = datetime.datetime.now().strftime("%d/%m/%Y")
                
                cursor.execute("""
                    INSERT INTO producao_hora_hora (mes_ano, data_lancamento, costureira, operacao, qtd_pecas, valor_unitario, valor_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (periodo_ativo_chave, data_hoje_txt, cost_phh_sel, operacao_phh_sel, qtd_phh_input, preco_unitario_op, valor_total_calculado))
                conn.commit()
                conn.close()
                
                # 🎉 CORREÇÃO DE OURO: Removidas as linhas problemáticas de session_state!
                # O clear_on_submit=True já esvazia as caixas de forma nativa e segura!
                st.success(f"🎉 Sucesso! {qtd_phh_input} peças de {operacao_phh_sel} lançadas para {cost_phh_sel}!")
                st.rerun()

                # --- 📊 SEÇÃO INFERIOR RECALIBRADA: PLANILHA CONSOLIDADA COM DATA ---
        st.markdown("<br><hr style='margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid #424242;'>", unsafe_allow_html=True)
        st.markdown("##### 📈 Resumo de Produção Acumulada das Colaboradoras")
        st.write("Abaixo estão listados os lançamentos de eficiência horária e o volume de peças produzidas:")
        st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
        
        conn = sqlite3.connect("dlr_confecoes_v3.db")
        # Puxa o ID e a Data do banco para permitir a auditoria e a exclusão exata
        df_producao_geral = pd.read_sql_query(f"SELECT id, data_lancamento, costureira, operacao, qtd_pecas FROM producao_hora_hora WHERE mes_ano = '{periodo_ativo_chave}' ORDER BY id DESC", conn)
        conn.close()
        
        if not df_producao_geral.empty:
            df_tabela_visao = df_producao_geral.copy()
            df_tabela_visao.columns = ["ID_H", "Data", "Nome da Costureira", "Tipo de Operação", "Total de Peças"]
            
            # Renderiza a tabela ultra compacta espremida em pixels com a data inclusa
            st.data_editor(
                df_tabela_visao,
                column_config={
                    "ID_H": None, # Oculta o ID técnico
                    "Data": st.column_config.TextColumn("Data", width=85, disabled=True),
                    "Nome da Costureira": st.column_config.TextColumn("Nome da Costureira", width=220, disabled=True),
                    "Tipo de Operação": st.column_config.TextColumn("Tipo de Operação", width=150, disabled=True),
                    "Total de Peças": st.column_config.NumberColumn("Total de Peças", format="%d pçs", width=110, disabled=True)
                },
                hide_index=True,
                use_container_width=True,
                key=f"tabela_rendimento_hora_hora_audit_{periodo_ativo_chave}"
            )
        
            # --- 🗑️ SEÇÃO DE REMOÇÃO SELETIVA DE LANÇAMENTOS NO RODAPÉ ---
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            
            # Cria uma lista de opções inteligente combinando o ID, Nome e Operação para o usuário selecionar sem erro
            lista_opcoes_excluir = [
                f"ID: {reg['id']} | {reg['costureira']} - {reg['operacao']} ({reg['data_lancamento']})" 
                for _, reg in df_producao_geral.iterrows()
            ]
            
            registro_selecionado_excluir = st.selectbox(
                "🗑️ Selecione um lançamento para excluir:", 
                ["Selecionar..."] + lista_opcoes_excluir, 
                key=f"lixeira_eficiencia_hora_{periodo_ativo_chave}"
            )
            
            if registro_selecionado_excluir != "Selecionar...":
                # Extrai o ID numérico puro que está no início do texto selecionado
                id_puro_excluir = int(registro_selecionado_excluir.split("|")[0].replace("ID: ", "").strip())
                
                st.warning(f"⚠️ **Aviso de Segurança:** Tem certeza que deseja apagar permanentemente este ciclo de produção do histórico?")
                col_del_h1, col_del_h2 = st.columns(2)
                
                with col_del_h1:
                    if st.button("✅ Sim, apagar registro", use_container_width=True, type="primary", key="btn_confirma_del_hh"):
                        conn = sqlite3.connect("dlr_confecoes_v3.db")
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM producao_hora_hora WHERE id = ?", (id_puro_excluir,))
                        conn.commit()
                        conn.close()
                        
                        # 🧼 LIMPEZA DE CHOQUE: Remove a chave do estado para forçar o selectbox a voltar para o "Selecionar..."
                        if f"lixeira_eficiencia_hora_{periodo_ativo_chave}" in st.session_state:
                            st.session_state.pop(f"lixeira_eficiencia_hora_{periodo_ativo_chave}")
                            
                        st.success("🎉 Lançamento removido do histórico com sucesso!")
                        st.rerun()
                        
                with col_del_h2:
                    # 🚀 CORREÇÃO DE OURO INDESTRUTÍVEL: O comando .pop() deleta a seleção antiga da memória interna do Streamlit!
                    if st.button("❌ Não, manter registro", use_container_width=True, key="btn_cancela_del_hh"):
                        if f"lixeira_eficiencia_hora_{periodo_ativo_chave}" in st.session_state:
                            st.session_state.pop(f"lixeira_eficiencia_hora_{periodo_ativo_chave}")
                        st.rerun()
        else:
            st.info("💡 Nenhum ciclo de produção horária foi lançado para as colaboradoras neste mês ainda.")

            # 📈 RECONECTOR MASTER DLR — PROCESSO DE PROGRESSO DE LOTES (CONFERÊNCIA CENTRADA)
# ==============================================================================
# Encostado 100% na parede esquerda (zero espaços)! Força a abertura no meio da tela!
if st.session_state.sistema_autorizado and st.session_state.perfil_usuario == "Conferencia":
    menu_conf_verificar = st.session_state.pagina_conf_atual
    
    if menu_conf_verificar == "📈 Progresso de Lotes":
        st.title("📈 Progresso e Auditoria de Entrega de Lotes (Conferência)")
        st.markdown(f"📋 Monitore e finalize as ordens de fabricação referentes ao período de: **{mes_ativo_txt} de {ano_ativo_txt}**")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- SELETORES GERAIS DE FILTRO NA PARTE SUPERIOR ---
        col_conf_f1, col_conf_f2 = st.columns(2)
        with col_conf_f1:
            mes_ext_sel = st.selectbox("Filtrar por Mês:", lista_meses_sistema, index=lista_meses_sistema.index(st.session_state.calendario_master_mes), key="filtro_mes_conf_prog_final_v19")
        with col_conf_f2:
            ano_ext_sel = st.selectbox("Filtrar por Ano:", lista_anos_sistema, index=lista_anos_sistema.index(st.session_state.calendario_master_ano), key="filtro_ano_conf_prog_final_v19")
            
        if mes_ext_sel != st.session_state.calendario_master_mes or ano_ext_sel != st.session_state.calendario_master_ano:
            st.session_state.calendario_master_mes = mes_ext_sel
            st.session_state.calendario_master_ano = ano_ext_sel
            st.rerun()

        # --- MOTOR DE CÁLCULO DOS CARDS LIMITADO RIGOROSAMENTE AO MÊS DE CADASTRO ---
        qtd_pendentes = 0; qtd_em_producao = 0; qtd_vencidos = 0; qtd_concluidos = 0; data_hoje_dt = datetime.date.today()
        
        conn = sqlite3.connect("dlr_confecoes_v3.db")
        cursor = conn.cursor()
        cursor.execute("SELECT status, data_entrega, prioridade, data_cadastro, mes_ano_cadastro FROM lotes_gerais")
        todos_lotes_db = cursor.fetchall()
        conn.close()
        
        for lote_db in todos_lotes_db:
            status_lote, dt_ent_db, prio_db, dt_cad_db, mes_ano_cad_db = lote_db[0], lote_db[1], lote_db[2], lote_db[3], lote_db[4]
            chave_conferencia = mes_ano_cad_db if (mes_ano_cad_db and mes_ano_cad_db != '') else f"{dt_cad_db[3:5]}/{dt_cad_db[6:10]}"
            
            if chave_conferencia == periodo_ativo_chave:
                try: dt_entrega_dt = dt_class.strptime(dt_ent_db, "%d/%m/%Y").date()
                except: dt_entrega_dt = None
                
                if status_lote == "Pendente": qtd_pendentes += 1
                elif status_lote == "Em produção": qtd_em_producao += 1
                elif status_lote == "Concluído": qtd_concluidos += 1
                
                try:
                    if dt_entrega_dt and data_hoje_dt > dt_entrega_dt and status_lote != "Concluído":
                        qtd_vencidos += 1
                except: pass

        # --- CARDS COMPACTOS COM AS MEDIDAS EXATAS DE 120PX DE ALTURA E FONTES DE 30PX ---
        st.markdown(f"""
            <div style='width: 100%; display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 10px; margin-bottom: 10px;'>
                <div style='background-color: #EF6C00; padding: 10px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center; height: 120px;'>
                    <div style='font-size: 18px; font-weight: normal; color: #FFE0B2; opacity: 0.9;'>Lotes Pendentes</div>
                    <h4 style='margin-top: 4px; margin-bottom: 0px; color: white; font-size: 30px; font-weight: bold;'>{qtd_pendentes}</h4>
                </div>
                <div style='background-color: #2E7D32; padding: 10px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center; height: 120px;'>
                    <div style='font-size: 18px; font-weight: normal; color: #E8F5E9; opacity: 0.9;'>Em Produção</div>
                    <h4 style='margin-top: 4px; margin-bottom: 0px; color: white; font-size: 30px; font-weight: bold;'>{qtd_em_producao}</h4>
                </div>
                <div style='background-color: #C62828; padding: 10px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center; height: 120px;'>
                    <div style='font-size: 18px; font-weight: normal; color: #FFEBEE; opacity: 0.9;'>Lotes Vencidos</div>
                    <h4 style='margin-top: 4px; margin-bottom: 0px; color: white; font-size: 30px; font-weight: bold;'>{qtd_vencidos}</h4>
                </div>
                <div style='background-color: #1565C0; padding: 10px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center; height: 120px;'>
                    <div style='font-size: 18px; font-weight: normal; color: #E3F2FD; opacity: 0.9;'>Concluídos</div>
                    <h4 style='margin-top: 4px; margin-bottom: 0px; color: white; font-size: 30px; font-weight: bold;'>{qtd_concluidos}</h4>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='margin-top: 15px; margin-bottom: 10px; border: 0; border-top: 1px solid #424242;'>", unsafe_allow_html=True)
        st.write("📋 **Controle da Conferência:** Atualize o status para 'Concluído' e digite as peças prontas reais!")
        # --- MONTAGEM DA PLANILHA DO PROGRESSO NO CENTRO PRINCIPAL CORRIGIDA ---
        linhas_tabela_conferencia = []
        conn = sqlite3.connect("dlr_confecoes_v3.db")
        df_lotes_brutos = pd.read_sql_query("SELECT id, data_cadastro, data_inicio_producao, data_entrega, fornecedor, of, referencia, qtd_prevista, preco, status, porcentagem_pronta, qtd_pronta, prioridade, mes_ano_cadastro FROM lotes_gerais", conn)
        conn.close()

        if not df_lotes_brutos.empty:
            data_hoje_dt = datetime.date.today()
            
            for idx, row in df_lotes_brutos.iterrows():
                dt_cad = row["data_cadastro"]; status_at = row["status"]; prio_at = row["prioridade"]
                dt_ent = row["data_entrega"]; m_a_cad = row["mes_ano_cadastro"]
                
                chave_conferencia_tabela = m_a_cad if (m_a_cad and m_a_cad != '') else f"{dt_cad[3:5]}/{dt_cad[6:10]}"
                
                if chave_conferencia_tabela == periodo_ativo_chave:
                    try: dt_chegada_dt = dt_class.strptime(dt_cad, "%d/%m/%Y").date()
                    except: dt_chegada_dt = data_hoje_dt
                    # --- ⚙️ MOTOR DE PRAZOS DO ADMINISTRATIVO BLINDADO ---
                    if status_at == "Concluído":
                        dias_pendente = 0
                    else:
                        dias_pendente = (data_hoje_dt - dt_chegada_dt).days
                        if dias_pendente < 0: dias_pendente = 0

                    if status_at == "Pendente": cor_bola = "🟠"
                    elif status_at == "Em produção": cor_bola = "🟢"
                    else: cor_bola = "🔵"
                    
                    try:
                        dt_entrega_dt = dt_class.strptime(dt_ent, "%d/%m/%Y").date()
                        if dt_entrega_dt and data_hoje_dt > dt_entrega_dt and status_at != "Concluído": cor_bola = "🔴"
                    except: pass
                    
                    signal_final = f"{cor_bola} {cor_bola}" if prio_at == "Sim" else cor_bola
                    linhas_tabela_conferencia.append({"ID_T": int(row["id"]), "🚨 Alerta": signal_final, "Nome do fornecedor": row["fornecedor"], "Nº do O.F": row["of"], "Referência": row["referencia"], "Quantidade Total de Peças na Nota": int(row["qtd_prevista"]), "Dias pendente": int(dias_pendente), "Data chegada": dt_cad, "Data para entrega": dt_ent, "Preço Unitário": float(row["preco"]), "Status": status_at, "Porcentagem já produzido": f"{row['porcentagem_pronta']}%", "Peças Prontas Reais": int(row["qtd_pronta"]), "Prioridade": prio_at})

        if linhas_tabela_conferencia:
            df_conf_visao = pd.DataFrame(linhas_tabela_conferencia)
            chave_editor_conf_lotes = f"tabela_esteira_conferencia_DL_{periodo_ativo_chave}"
            
            tabela_editada_conf = st.data_editor(
                df_conf_visao,
                column_config={
                    "ID_T": None,
                    "🚨 Alerta": st.column_config.TextColumn("🚨 Alerta", width=55, disabled=True),
                    "Nome do fornecedor": st.column_config.TextColumn("Nome do fornecedor", width=110, disabled=True),
                    "Nº do O.F": st.column_config.TextColumn("Nº do O.F", width=75, disabled=True),
                    "Referência": st.column_config.TextColumn("Referência", width=75, disabled=True),
                    "Quantidade Total de Peças na Nota": st.column_config.NumberColumn("Qtd Nota", width=75, disabled=True),
                    "Dias pendente": st.column_config.NumberColumn("Dias Pend", width=65, disabled=True),
                    "Data chegada": st.column_config.TextColumn("Chegada", width=85, disabled=True),
                    "Data para entrega": st.column_config.TextColumn("Entrega", width=85, disabled=True),
                    "Preço Unitário": st.column_config.NumberColumn("Preço Un", format="R$ %.2f", width=80, disabled=True),
                    "Status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Em produção", "Concluído"], required=True, width=105),
                    "Porcentagem já produzido": st.column_config.SelectboxColumn("Porcent", options=["0%", "10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%"], required=True, width=75),
                    # 🚀 CONFERÊNCIA: Peças Reais livre para digitação numérica!
                    "Peças Prontas Reais": st.column_config.NumberColumn("Pçs Reais", format="%d", min_value=0, step=1, width=85),
                    "Prioridade": st.column_config.SelectboxColumn("Prioridade", options=["Não", "Sim"], required=True, width=75)
                },
                hide_index=True, use_container_width=True, key=chave_editor_conf_lotes
            )
            
            if chave_editor_conf_lotes in st.session_state and st.session_state[chave_editor_conf_lotes]["edited_rows"]:
                conn = sqlite3.connect("dlr_confecoes_v3.db"); cursor = conn.cursor()
                for idx_s, mudancas in st.session_state[chave_editor_conf_lotes]["edited_rows"].items():
                    id_lote_db = int(df_conf_visao.iloc[int(idx_s)]["ID_T"])
                    if "Status" in mudancas:
                        cursor.execute("UPDATE lotes_gerais SET status = ? WHERE id = ?", (mudancas["Status"], id_lote_db))
                        # 🚀 CONFERÊNCIA BLINDADA: Garante a data real de fechamento para o Dashboard ler!
                        if mudancas["Status"] == "Concluído":
                            cursor.execute("UPDATE lotes_gerais SET data_inicio_producao = ? WHERE id = ?", (datetime.datetime.now().strftime("%d/%m/%Y"), id_lote_db))
                    if "Porcentagem já produzido" in mudancas:
                        cursor.execute("UPDATE lotes_gerais SET porcentagem_pronta = ? WHERE id = ?", (int(mudancas["Porcentagem já produzido"].replace("%", "")), id_lote_db))
                    if "Peças Prontas Reais" in mudancas:
                        cursor.execute("UPDATE lotes_gerais SET qtd_pronta = ? WHERE id = ?", (int(mudancas["Peças Prontas Reais"]), id_lote_db))
                    if "Prioridade" in mudancas:
                        cursor.execute("UPDATE lotes_gerais SET prioridade = ? WHERE id = ?", (mudancas["Prioridade"], id_lote_db))
                conn.commit(); conn.close(); st.rerun()
        else:
            st.info("💡 Nenhum lote de produção ativo localizado para este período na Conferência.")

            # 📋 RECONECTOR MASTER DLR — LOTES EM ANDAMENTO (ADMINISTRAÇÃO ESPELHO PURO)
# ==============================================================================
# Encostado 100% na parede esquerda (zero espaços)! Tela travada apenas para leitura do dono!
if st.session_state.sistema_autorizado and st.session_state.perfil_usuario == "Admin":
    menu_admin_verificar = st.session_state.pagina_admin_atual
    
    if menu_admin_verificar == "📋 Lotes em Andamento":
        st.title("📋 Lotes em Andamento — Espelho de Monitoramento (Admin)")
        st.markdown(f"📊 Painel de auditoria visual referente ao período de: **{mes_ativo_txt} de {ano_ativo_txt}**")
        st.markdown("<br>", unsafe_allow_html=True)
        
        
        # --- MOTOR DE CÁLCULO DOS CARDS LIMITADO AO MÊS DE CADASTRO V3 (CORRIGIDO) ---
        qtd_pendentes = 0
        qtd_em_producao = 0
        qtd_vencidos = 0
        qtd_concluidos = 0
        data_hoje_dt = datetime.date.today()
        
        conn = sqlite3.connect("dlr_confecoes_v3.db")
        cursor = conn.cursor()
        cursor.execute("SELECT status, data_entrega, prioridade, data_cadastro, mes_ano_cadastro FROM lotes_gerais")
        todos_lotes_db = cursor.fetchall()
        conn.close()
        
        for lote_db in todos_lotes_db:
            # 🚀 CORREÇÃO DE OURO: Desempacota os índices exatos da busca SQL para alimentar o robô!
            status_lote = str(lote_db[0]).strip()
            dt_ent_db = str(lote_db[1]).strip()
            prio_db = str(lote_db[2]).strip()
            dt_cad_db = str(lote_db[3]).strip()
            mes_ano_cad_db = str(lote_db[4]).strip() if lote_db[4] is not None else ""
            
            # Aplica a trava restrita por mês de entrada
            chave_conferencia = mes_ano_cad_db if (mes_ano_cad_db and mes_ano_cad_db != '') else f"{dt_cad_db[3:5]}/{dt_cad_db[6:10]}"
            
            if chave_conferencia == periodo_ativo_chave:
                try: dt_entrega_dt = dt_class.strptime(dt_ent_db, "%d/%m/%Y").date()
                except: dt_entrega_dt = None
                
                # Computa os estados baseados nas células reais
                if status_lote == "Pendente": 
                    qtd_pendentes += 1
                elif status_lote == "Em produção": 
                    qtd_em_producao += 1
                elif status_lote == "Concluído": 
                    qtd_concluidos += 1
                
                try:
                    if dt_entrega_dt and data_hoje_dt > dt_entrega_dt and status_lote != "Concluído":
                        qtd_vencidos += 1
                except: pass

        # --- CARDS COMPACTOS FIÉIS AO ESPELHO: LARGURA CHEIA, 120PX DE ALTURA E FONTES DE 30PX ---
        st.markdown(f"""
            <div style='width: 100%; display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 10px; margin-bottom: 10px;'>
                <div style='background-color: #EF6C00; padding: 10px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center; height: 120px;'>
                    <div style='font-size: 18px; font-weight: normal; color: #FFE0B2; opacity: 0.9;'>Lotes Pendentes</div>
                    <h4 style='margin-top: 4px; margin-bottom: 0px; color: white; font-size: 30px; font-weight: bold;'>{qtd_pendentes}</h4>
                </div>
                <div style='background-color: #2E7D32; padding: 10px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center; height: 120px;'>
                    <div style='font-size: 18px; font-weight: normal; color: #E8F5E9; opacity: 0.9;'>Em Produção</div>
                    <h4 style='margin-top: 4px; margin-bottom: 0px; color: white; font-size: 30px; font-weight: bold;'>{qtd_em_producao}</h4>
                </div>
                <div style='background-color: #C62828; padding: 10px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center; height: 120px;'>
                    <div style='font-size: 18px; font-weight: normal; color: #FFEBEE; opacity: 0.9;'>Lotes Vencidos</div>
                    <h4 style='margin-top: 4px; margin-bottom: 0px; color: white; font-size: 30px; font-weight: bold;'>{qtd_vencidos}</h4>
                </div>
                <div style='background-color: #1565C0; padding: 10px 5px; border-radius: 8px; color: white; text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.15); display: flex; flex-direction: column; justify-content: center; align-items: center; height: 120px;'>
                    <div style='font-size: 18px; font-weight: normal; color: #E3F2FD; opacity: 0.9;'>Concluídos</div>
                    <h4 style='margin-top: 4px; margin-bottom: 0px; color: white; font-size: 30px; font-weight: bold;'>{qtd_concluidos}</h4>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='margin-top: 15px; margin-bottom: 10px; border: 0; border-top: 1px solid #424242;'>", unsafe_allow_html=True)
        st.write("📋 **Visualização de Auditoria:** Painel travado apenas para leitura dos dados enviados de fábrica e conferência.")
        # --- MONTAGEM DA PLANILHA DO ESPELHO CENTRALIZADO NO ADMIN ---
        linhas_tabela_adm_lotes = []
        conn = sqlite3.connect("dlr_confecoes_v3.db")
        df_lotes_brutos = pd.read_sql_query("SELECT id, data_cadastro, data_inicio_producao, data_entrega, fornecedor, of, referencia, qtd_prevista, preco, status, porcentagem_pronta, qtd_pronta, prioridade, mes_ano_cadastro FROM lotes_gerais", conn)
        conn.close()

        if not df_lotes_brutos.empty:
            data_hoje_dt = datetime.date.today()
            for idx, row in df_lotes_brutos.iterrows():
                dt_cad = row["data_cadastro"]; status_at = row["status"]; prio_at = row["prioridade"]
                dt_ent = row["data_entrega"]; m_a_cad = row["mes_ano_cadastro"]
                
                chave_conferencia_tabela = m_a_cad if (m_a_cad and m_a_cad != '') else f"{dt_cad[3:5]}/{dt_cad[6:10]}"
                
                if chave_conferencia_tabela == periodo_ativo_chave:
                    try: dt_chegada_dt = dt_class.strptime(dt_cad, "%d/%m/%Y").date()
                    except: dt_chegada_dt = data_hoje_dt
                    # --- ⚙️ MOTOR DE PRAZOS DO ADMINISTRATIVO BLINDADO ---
                    if status_at == "Concluído":
                        dias_pendente = 0
                    else:
                        dias_pendente = (data_hoje_dt - dt_chegada_dt).days
                        if dias_pendente < 0: dias_pendente = 0

                    if status_at == "Pendente": cor_bola = "🟠"
                    elif status_at == "Em produção": cor_bola = "🟢"
                    else: cor_bola = "🔵"
                    
                    try:
                        dt_entrega_dt = dt_class.strptime(dt_ent, "%d/%m/%Y").date()
                        if dt_entrega_dt and data_hoje_dt > dt_entrega_dt and status_at != "Concluído": cor_bola = "🔴"
                    except: pass
                    
                    signal_final = f"{cor_bola} {cor_bola}" if prio_at == "Sim" else cor_bola
                    linhas_tabela_adm_lotes.append({"ID_T": int(row["id"]), "🚨 Alerta": signal_final, "Nome do fornecedor": row["fornecedor"], "Nº do O.F": row["of"], "Referência": row["referencia"], "Quantidade Total de Peças na Nota": int(row["qtd_prevista"]), "Dias pendente": int(dias_pendente), "Data chegada": dt_cad, "Data para entrega": dt_ent, "Preço Unitário": float(row["preco"]), "Status": status_at, "Porcentagem já produzido": f"{row['porcentagem_pronta']}%", "Peças Prontas Reais": int(row["qtd_pronta"]), "Prioridade": prio_at})

        if linhas_tabela_adm_lotes:
            df_adm_visao = pd.DataFrame(linhas_tabela_adm_lotes)
            chave_editor_adm_lotes = f"tabela_esteira_admin_DL_{periodo_ativo_chave}"
            
            # 🚀 TRAVA DE LEITURA COMPLETA: Todas as colunas estão com disabled=True
            tabela_editada_adm = st.data_editor(
                df_adm_visao,
                column_config={
                    "ID_T": None,
                    "🚨 Alerta": st.column_config.TextColumn("🚨 Alerta", width=55, disabled=True),
                    "Nome do fornecedor": st.column_config.TextColumn("Nome do fornecedor", width=110, disabled=True),
                    "Nº do O.F": st.column_config.TextColumn("Nº do O.F", width=75, disabled=True),
                    "Referência": st.column_config.TextColumn("Referência", width=75, disabled=True),
                    "Quantidade Total de Peças na Nota": st.column_config.NumberColumn("Qtd Nota", width=75, disabled=True),
                    "Dias pendente": st.column_config.NumberColumn("Dias Pend", width=65, disabled=True),
                    "Data chegada": st.column_config.TextColumn("Chegada", width=85, disabled=True),
                    "Data para entrega": st.column_config.TextColumn("Entrega", width=85, disabled=True),
                    "Preço Unitário": st.column_config.NumberColumn("Preço Un", format="R$ %.2f", width=80, disabled=True),
                    "Status": st.column_config.TextColumn("Status", width=105, disabled=True),
                    "Porcentagem já produzido": st.column_config.TextColumn("Porcent", width=75, disabled=True),
                    "Peças Prontas Reais": st.column_config.NumberColumn("Pçs Reais", format="%d", width=85, disabled=True),
                    "Prioridade": st.column_config.TextColumn("Prioridade", width=75, disabled=True)
                },
                hide_index=True, use_container_width=True, key=chave_editor_adm_lotes
            )
        else:
            st.info("💡 Nenhum lote de produção ativo localizado para este período na Administração.")

            # 📥 RECONECTOR MASTER DLR — IMPORTAR PONTO MANUAIS (LARGURA E FILTROS BLINDADOS)
# ==============================================================================
# Encostado 100% na parede esquerda (zero espaços)! Destrava o ponto na tela cheia!
if st.session_state.sistema_autorizado and st.session_state.perfil_usuario == "Conferencia":
    menu_conf_verificar = st.session_state.pagina_conf_atual
    
    if menu_conf_verificar == "📥 Importar Ponto":
        # 🚀 INJEÇÃO MÁGICA: Quebra a caixinha de 400px e liberta o formulário para ocupar a largura cheia do monitor!
        st.markdown("""
            <style>
                div[data-testid="stForm"] {
                    max-width: 100% !important;
                    margin: 0px !important;
                    padding: 20px !important;
                }
            </style>
        """, unsafe_allow_html=True)

        st.title("📥 Registro Manual de Ponto — Costureiras Horistas")
        st.markdown(f"⏱️ Lance o total de horas trabalhadas pelas colaboradoras na competência: **{mes_ativo_txt} de {ano_ativo_txt}**")
        st.markdown("<br>", unsafe_allow_html=True)

        # --- MOTOR DE PUXADA DINÂMICA MASTER GERENCIAL: EXTRAÇÃO CIRÚRGICA DE TEXTO ---
        conn = sqlite3.connect("dlr_confecoes_v3.db")
        cursor = conn.cursor()
        
        # Garante preventivamente a existência da tabela de ponto no HD
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registro_ponto_horistas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, mes_ano TEXT, data_registro TEXT, costureira TEXT, horas_totais REAL
            )
        """)
        
        # Garante que a tabela geral de funcionários exista no banco de dados resetado
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funcionarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, tipo_pagamento TEXT, valor_base REAL, chave_pix TEXT, externo TEXT, status_cadastro TEXT
            )
        """)
        
        # 🚀 BUSCA TOTAL: Captura o nome de todos os colaboradores ativos sem nenhuma trava de cargo ou pagamento
        cursor.execute("SELECT nome FROM funcionarios WHERE status_cadastro != 'Demitido' ORDER BY nome ASC")
        
        # 🚀 CORREÇÃO DE OURO INDESTRUTÍVEL: O row[0] captura o texto puro do nome e limpa os parênteses (,) e aspas!
        lista_horistas_ponto = [str(row[0]).strip() for row in cursor.fetchall() if row and row[0] is not None]
        conn.close()

        # --- 🎨 FORMULÁRIO DE LANÇAMENTO EXPANDIDO DE PAREDE A PAREDE ---
        with st.form(key="form_importar_ponto_manual_dlr", clear_on_submit=True):
            col_pt1, col_ph2 = st.columns(2)
            with col_pt1:
                cost_ponto_sel = st.selectbox(
                    "Selecionar Costureira Horista Ativa",
                    lista_horistas_ponto if lista_horistas_ponto else ["Nenhuma costureira horista habilitada no sistema"],
                    key="pt_costureira_master"
                )
            with col_ph2:
                horas_ponto_input = st.number_input(
                    "Total de Horas Trabalhadas no Mês",
                    min_value=0.0,
                    step=1.0,
                    format="%.2f",
                    key="pt_horas_master"
                )
                
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            btn_salvar_ponto = st.form_submit_button("📥 Registrar Total de Horas no Ponto", use_container_width=True)

        # --- MOTOR DE GRAVAÇÃO NO COFRE V3 ---
        if btn_salvar_ponto:
            if cost_ponto_sel == "Nenhuma costureira horista habilitada no sistema":
                st.error("❌ Operação Recusada! Vá na Ficha L.F da Administração e mude 'Lançar no Manual' para 'Sim' nas funcionárias!")
            elif horas_ponto_input <= 0:
                st.error("❌ Operação Recusada! O total de horas deve ser maior que zero!")
            else:
                conn = sqlite3.connect("dlr_confecoes_v3.db"); cursor = conn.cursor()
                
                # Se já tiver um ponto lançado para ela neste mesmo mês, atualiza! Senão, faz um novo insert!
                cursor.execute("SELECT id FROM registro_ponto_horistas WHERE costureira = ? AND mes_ano = ?", (cost_ponto_sel, periodo_ativo_chave))
                existe_ponto = cursor.fetchone()
                
                data_hoje_txt = datetime.datetime.now().strftime("%d/%m/%Y")
                
                if existe_ponto:
                    cursor.execute("UPDATE registro_ponto_horistas SET horas_totais = ?, data_registro = ? WHERE id = ?", (horas_ponto_input, data_hoje_txt, existe_ponto[0]))
                else:
                    cursor.execute("""
                        INSERT INTO registro_ponto_horistas (mes_ano, data_registro, costureira, horas_totais)
                        VALUES (?, ?, ?, ?)
                    """, (periodo_ativo_chave, data_hoje_txt, cost_ponto_sel, horas_ponto_input))
                    
                conn.commit(); conn.close()
                st.success(f"🎉 Sucesso! Registrado {horas_ponto_input:.2f} horas para a colaboradora {cost_ponto_sel}!")
                st.rerun()

        # --- 📊 PLANILHA DE HISTÓRICO DE HORAS LANÇADAS NO MÊS ---
        st.markdown("<br><hr style='margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid #424242;'>", unsafe_allow_html=True)
        st.markdown("##### 📈 Espelho de Horas Acumuladas no Mês")
        
        conn = sqlite3.connect("dlr_confecoes_v3.db")
        df_ponto_mes = pd.read_sql_query(f"SELECT id, data_registro, costureira, horas_totais FROM registro_ponto_horistas WHERE mes_ano = '{periodo_ativo_chave}' ORDER BY costureira ASC", conn)
        conn.close()
        
        if not df_ponto_mes.empty:
            df_pt_visao = df_ponto_mes.copy()
            df_pt_visao.columns = ["ID_P", "Data do Lançamento", "Nome da Costureira", "Horas Totais Registradas"]
            
            st.data_editor(
                df_pt_visao,
                column_config={
                    "ID_P": None,
                    "Data do Lançamento": st.column_config.TextColumn("Data de Registro", width=140, disabled=True),
                    "Nome da Costureira": st.column_config.TextColumn("Nome da Costureira", width=300, disabled=True),
                    "Horas Totais Registradas": st.column_config.NumberColumn("Horas Acumuladas", format="%.2f hrs", width=160, disabled=True)
                },
                hide_index=True, use_container_width=True, key=f"tabela_ponto_horistas_audit_{periodo_ativo_chave}"
            )
            
            # --- 🗑️ BOTÃO DE EXCLUSÃO SELETIVA NO RODAPÉ ---
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            lista_p_excluir = [f"ID: {r['id']} | {r['costureira']} ({r['horas_totais']:.2f} hrs)" for _, r in df_ponto_mes.iterrows()]
            pt_selecionado_excluir = st.selectbox("🗑️ Selecione um lançamento para remover do ponto:", ["Selecionar..."] + lista_p_excluir, key=f"lix_ponto_{periodo_ativo_chave}")
            
            if pt_selecionado_excluir != "Selecionar...":
                id_pt_del = int(pt_selecionado_excluir.split("|")[0].replace("ID: ", "").strip())
                st.warning("⚠️ **Aviso de Exclusão:** Tem certeza que deseja apagar permanentemente essas horas do histórico?")
                c_d_p1, c_del_p2 = st.columns(2)
                with c_d_p1:
                    if st.button("✅ Sim, apagar horas", use_container_width=True, type="primary", key="btn_conf_del_pt"):
                        conn = sqlite3.connect("dlr_confecoes_v3.db"); cursor = conn.cursor()
                        cursor.execute("DELETE FROM registro_ponto_horistas WHERE id = ?", (id_pt_del,))
                        conn.commit(); conn.close()
                        if f"lix_ponto_{periodo_ativo_chave}" in st.session_state:
                            st.session_state.pop(f"lix_ponto_{periodo_ativo_chave}")
                        st.success("Removido!"); st.rerun()
                with c_del_p2:
                    if st.button("❌ Não, manter", use_container_width=True, key="btn_canc_del_pt"):
                        if f"lix_ponto_{periodo_ativo_chave}" in st.session_state:
                            st.session_state.pop(f"lix_ponto_{periodo_ativo_chave}")
                        st.rerun()
        else:
            st.info("💡 Nenhuma hora de ponto foi registrada para este mês ainda na conferência.")