import streamlit as st
from datetime import datetime
# Configuração da página para um visual moderno e amplo
st.set_page_config(page_title="Sistema DLR - Confecção", layout="wide", page_icon="🧵")

# Estilização básica para um visual mais limpo e profissional
st.markdown("""
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1 {color: #1E3A8A; font-weight: 700;}
    h2 {color: #2563EB; font-weight: 600;}
    
    /* --- ESTILIZAÇÃO DOS BOTÕES COM COR DE AÇAÍ --- */
    div.stButton > button {
        background-color: #4A154B !important; /* Cor de Açaí predominante */
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #6B206B !important; /* Açaí um pouco mais claro no mouse */
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

import sqlite3

def inicializar_banco_dados_sqlite():
    """
    Cria o arquivo de banco de dados e as tabelas permanentes da DLR Confecções no HD.
    """
    conexao = sqlite3.connect("dlr_confecoes.db")
    cursor = conexao.cursor()
    
    # 1. Tabela permanente de Funcionários e Chaves PIX
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            cargo TEXT,
            pagamento TEXT,
            valor_hora REAL,
            chave_pix TEXT
        )
    """)
    
    # 2. Tabela permanente para registrar os Vales e Adiantamentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adiantamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            data TEXT,
            tipo TEXT,
            valor_bruto REAL,
            valor_parcela REAL,
            status_vale TEXT
        )
    """)
    
    # 3. Tabela permanente para registrar as Horas Acumuladas do Relógio FA05H
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registro_ponto (
            nome TEXT,
            mes_ano TEXT,
            total_horas REAL,
            PRIMARY KEY (nome, mes_ano)
        )
    """)
    
    conexao.commit()
    conexao.close()

import sqlite3
import json

def inicializar_super_cofre_hd():
    """
    Cria as tabelas físicas permanentes no HD para guardar os dados da empresa 
    sem interferir em nenhuma linha do código visual das telas.
    """
    conn = sqlite3.connect("dlr_confecoes.db")
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE IF NOT EXISTS super_lotes (id INTEGER PRIMARY KEY AUTOINCREMENT, dados_json TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS super_caixa (id INTEGER PRIMARY KEY AUTOINCREMENT, dados_json TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS super_funcionarios (id INTEGER PRIMARY KEY AUTOINCREMENT, dados_json TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS super_producao_geral (id INTEGER PRIMARY KEY AUTOINCREMENT, hist_json TEXT, prod_json TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS super_banco_producao (id INTEGER PRIMARY KEY AUTOINCREMENT, dados_json TEXT)")
    
    # 6. GAVETA ADICIONADA: Tranca permanentemente o histórico e controle de Serviços Externos no HD
    cursor.execute("CREATE TABLE IF NOT EXISTS super_servicos_externos (id INTEGER PRIMARY KEY AUTOINCREMENT, dados_json TEXT)")
    
    conn.commit()
    conn.close()

def super_robo_carregar_hd_para_memoria():
    """
    [ROBÔ INVISÍVEL - LEITURA]
    Executado apenas 1 vez quando o sistema liga. Resgata os históricos do arquivo físico
    do HD e abastece as gavetas vivas de todas as telas.
    """
    try:
        conn = sqlite3.connect("dlr_confecoes.db")
        cursor = conn.cursor()
        
        # 1. Lotes Gerais
        cursor.execute("SELECT dados_json FROM super_lotes ORDER BY id DESC LIMIT 1")
        row_lotes = cursor.fetchone()
        if row_lotes and "lotes_gerais" not in st.session_state:
            st.session_state.lotes_gerais = json.loads(row_lotes[0])
            
        # 2. Livro Caixa e Vales
        cursor.execute("SELECT dados_json FROM super_caixa ORDER BY id DESC LIMIT 1")
        row_caixa = cursor.fetchone()
        if row_caixa and "movimentacoes_caixa" not in st.session_state:
            st.session_state.movimentacoes_caixa = json.loads(row_caixa[0])
            
        # 3. Cadastro de Funcionários
        cursor.execute("SELECT dados_json FROM super_funcionarios ORDER BY id DESC LIMIT 1")
        row_func = cursor.fetchone()
        if row_func and "funcionarios" not in st.session_state:
            st.session_state.funcionarios = json.loads(row_func[0])
            
        # 4. Produção de Hora em Hora e Gráfico Individual
        cursor.execute("SELECT hist_json, prod_json FROM super_producao_geral ORDER BY id DESC LIMIT 1")
        row_prod = cursor.fetchone()
        if row_prod:
            if "historico_producao_hora" not in st.session_state:
                st.session_state.historico_producao_hora = json.loads(row_prod[0])
            if "producao_hora" not in st.session_state:
                st.session_state.producao_hora = json.loads(row_prod[1])
                
        # 5. Resgata o histórico real de Fechamento por Dia do HD
        cursor.execute("SELECT dados_json FROM super_banco_producao ORDER BY id DESC LIMIT 1")
        row_banco_prod = cursor.fetchone()
        if row_banco_prod:
            st.session_state.banco_producao_diaria = json.loads(row_banco_prod[0])
            
        # 6. PONTE ADICIONADA: Resgata a tabela legítima de Lotes Externos do HD ao iniciar
        cursor.execute("SELECT dados_json FROM super_servicos_externos ORDER BY id DESC LIMIT 1")
        row_ext = cursor.fetchone()
        if row_ext:
            st.session_state.lotes_externos = json.loads(row_ext[0])
            
        conn.close()
    except Exception as e:
        print(f"Aviso do Super Robô (Leitura): Gavetas iniciando limpas. {e}")

def super_robo_trancar_memoria_para_hd():
    """
    [ROBÔ INVISÍVEL - GRAVAÇÃO VITALÍCIA]
    Varre as gavetas vivas e tranca direto no arquivo .db de forma blindada.
    """
    try:
        conn = sqlite3.connect("dlr_confecoes.db")
        cursor = conn.cursor()
        
        # 1. Tranca os Lotes Internos
        if "lotes_gerais" in st.session_state and st.session_state.lotes_gerais:
            cursor.execute("DELETE FROM super_lotes")
            cursor.execute("INSERT INTO super_lotes (dados_json) VALUES (?)", (json.dumps(st.session_state.lotes_gerais, ensure_ascii=False),))
            
        # 2. Tranca o Livro Caixa e Vales
        if "movimentacoes_caixa" in st.session_state and st.session_state.movimentacoes_caixa:
            cursor.execute("DELETE FROM super_caixa")
            cursor.execute("INSERT INTO super_caixa (dados_json) VALUES (?)", (json.dumps(st.session_state.movimentacoes_caixa, ensure_ascii=False),))
            
        # 3. Tranca as Costureiras e Chaves PIX
        if "funcionarios" in st.session_state and st.session_state.funcionarios:
            cursor.execute("DELETE FROM super_funcionarios")
            cursor.execute("INSERT INTO super_funcionarios (dados_json) VALUES (?)", (json.dumps(st.session_state.funcionarios, ensure_ascii=False),))
            
        # 4. Tranca a Produção de Hora em Hora
        hist_viva = st.session_state.get("historico_producao_hora", [])
        prod_viva = st.session_state.get("producao_hora", [])
        if hist_viva or prod_viva:
            cursor.execute("DELETE FROM super_producao_geral")
            cursor.execute("INSERT INTO super_producao_geral (hist_json, prod_json) VALUES (?, ?)", (
                json.dumps(hist_viva, ensure_ascii=False),
                json.dumps(prod_viva, ensure_ascii=False)
            ))
            
        # 5. Tranca a gaveta de faturamento diário
        if "banco_producao_diaria" in st.session_state and st.session_state.banco_producao_diaria:
            cursor.execute("DELETE FROM super_banco_producao")
            cursor.execute("INSERT INTO super_banco_producao (dados_json) VALUES (?)", (json.dumps(st.session_state.banco_producao_diaria, ensure_ascii=False),))
            
        # 6. PONTE ADICIONADA: Captura a gaveta de Serviços Externos e tranca de forma vitalícia no HD
        if "lotes_externos" in st.session_state and st.session_state.lotes_externos:
            cursor.execute("DELETE FROM super_servicos_externos")
            cursor.execute("INSERT INTO super_servicos_externos (dados_json) VALUES (?)", (json.dumps(st.session_state.lotes_externos, ensure_ascii=False),))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro do Super Robô ao salvar lotes_externos no HD: {e}")

# Executa as leituras automáticas na abertura do programa
inicializar_super_cofre_hd()
super_robo_carregar_hd_para_memoria()


# Executa a ativação do cofre no HD assim que o programa inicia
inicializar_banco_dados_sqlite()
def carregar_dados_do_banco_para_memoria():
    """
    Busca tudo o que está salvo no HD (SQLite) e alimenta o st.session_state 
    para que as telas do sistema exibam os dados na inicialização.
    """
    # 1. Carrega os Funcionários cadastrados
    conn = sqlite3.connect("dlr_confecoes.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT nome, cargo, pagamento, valor_hora, chave_pix FROM funcionarios")
    st.session_state.funcionarios = [dict(row) for row in cursor.fetchall()]
    
    # 2. Carrega o Histórico de Vales e Adiantamentos
    cursor.execute("SELECT nome, data, tipo, valor_bruto, valor_parcela, status_vale FROM adiantamentos")
    st.session_state.adiantamentos = [dict(row) for row in cursor.fetchall()]
    
    # 3. Carrega o Histórico de Horas do Relógio de Ponto FA05H
    cursor.execute("SELECT nome, mes_ano, total_horas FROM registro_ponto")
    st.session_state.banco_horas_permanente = [dict(row) for row in cursor.fetchall()]
    
    conn.close()

def db_salvar_funcionario(nome, cargo, pagamento, valor_hora, chave_pix):
    """Grava um novo colaborador diretamente no banco de dados permanente."""
    try:
        conn = sqlite3.connect("dlr_confecoes.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO funcionarios (nome, cargo, pagamento, valor_hora, chave_pix)
            VALUES (?, ?, ?, ?, ?)
        """, (nome.strip(), cargo, pagamento, float(valor_hora), chave_pix.strip()))
        conn.commit()
        conn.close()
        carregar_dados_do_banco_para_memoria() # Atualiza as planilhas na hora
        return True
    except Exception as e:
        print(f"Erro ao salvar funcionário no DB: {e}")
        return False

def db_salvar_vale(nome, data, tipo, valor_bruto, valor_parcela, status_vale="Ativo"):
    """Grava um novo adiantamento ou vale no banco de dados permanente."""
    conn = sqlite3.connect("dlr_confecoes.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO adiantamentos (nome, data, tipo, valor_bruto, valor_parcela, status_vale)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nome.strip(), data.strip(), tipo, float(valor_bruto), float(valor_parcela), status_vale))
    conn.commit()
    conn.close()
    carregar_dados_do_banco_para_memoria()

def db_salvar_ponto_horas(nome, mes_ano, total_horas):
    """Grava as horas calculadas do Pen Drive do FA05H no banco de dados permanente."""
    conn = sqlite3.connect("dlr_confecoes.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO registro_ponto (nome, mes_ano, total_horas)
        VALUES (?, ?, ?)
    """, (nome.strip().title(), mes_ano.strip(), float(total_horas)))
    conn.commit()
    conn.close()
    carregar_dados_do_banco_para_memoria()

def processar_arquivo_ponto_fa05h(df_ponto):
    """
    Motor Avançado e Preciso para a aba 'Resumo de atend.' do FA05H.
    Decifra a contagem de horas e minutos em valores decimais reais.
    """
    horas_acumuladas = {}
    
    try:
        # Força todas as colunas a limparem os nomes e espaços de cabeçalho
        df_ponto.columns = [str(c).strip() for c in df_ponto.columns]
        
        # Localiza as colunas ideais ignorando maiúsculas e minúsculas
        col_nome = next((c for c in df_ponto.columns if "nome" in c.lower() or "unnamed: 1" in c.lower()), None)
        col_hora_real = next((c for c in df_ponto.columns if "real" in c.lower() or "unnamed: 4" in c.lower()), None)
        
        if col_nome and col_hora_real:
            for idx, linha in df_ponto.iterrows():
                nome_cru = str(linha[col_nome]).strip()
                tempo_str = str(linha[col_hora_real]).strip()
                
                # Filtra cabeçalhos e linhas em branco do Excel
                if nome_cru and nome_cru.lower() != "nan" and nome_cru.lower() != "nome" and tempo_str.lower() != "nan":
                    total_horas_dec = 0.0
                    
                    if ":" in tempo_str:
                        try:
                            partes = tempo_str.split(":")
                            # CORREÇÃO CRÍTICA DO MISTÉRIO: Captura as posições [0] e [1] da string
                            horas_puras = float(partes[0])
                            minutos_puros = float(partes[1])
                            # Converte minutos em frações de hora com exatidão decimal
                            total_horas_dec = horas_puras + (minutos_puros / 60.0)
                        except Exception as err_partes:
                            total_horas_dec = 0.0
                    else:
                        try:
                            total_horas_dec = float(tempo_str.replace(",", "."))
                        except:
                            total_horas_dec = 0.0
                    
                    if total_horas_dec > 0:
                        # Carimba o nome com as primeiras letras maiúsculas para sincronismo
                        nome_chave = nome_cru.title().strip()
                        horas_acumuladas[nome_chave] = total_horas_dec
                        
    except Exception as e:
        print(f"Erro ao processar folha resumida do FA05H: {e}")
        
    return horas_acumuladas

# --- INICIALIZAÇÃO DE SEGURANÇA DOS DADOS NO TOPO ---
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.perfil_atual = None
    st.session_state.usuario_nome = ""

if "movimentacoes_caixa" not in st.session_state:
    st.session_state.movimentacoes_caixa = []    

if "pagina_admin_atual" not in st.session_state:
    st.session_state.pagina_admin_atual = "🏠 Dashboard Inicial"

if "lotes_gerais" not in st.session_state:
    st.session_state.lotes_gerais = []

if "presencas" not in st.session_state:
    st.session_state.presencas = []

if "lotes_externos" not in st.session_state:
    st.session_state.lotes_externos = []

if "adiantamentos" not in st.session_state:
    st.session_state.adiantamentos = []

if "banco_horas_permanente" not in st.session_state:
    st.session_state.banco_horas_permanente = []

if "presencas_ponto" not in st.session_state:
    st.session_state.presencas_ponto = {}

if "status_folha_pagamento" not in st.session_state:
    st.session_state.status_folha_pagamento = {}

# Dicionário mestre de meses posicionado de forma segura no topo
MESES_NUM_GLOBAL = {
    "Janeiro": "01", "Fevereiro": "02", "Março": "03", "Abril": "04",
    "Maio": "05", "Junho": "06", "Julho": "07", "Agosto": "08",
    "Setembro": "09", "Outubro": "10", "Novembro": "11", "Dezembro": "12"
}

# --- CADASTRO E RECONHECIMENTO DE FUNCIONÁRIOS DA DLR CONFECÇÕES ---
if "funcionarios" not in st.session_state:
    st.session_state.funcionarios = [
        {"nome": "Maria Silva", "cargo": "Costureira", "pagamento": "Por hora", "valor_hora": 12.00, "externo": "Não", "status_pagamento_mes": "Pendente"},
        {"nome": "Ana Oliveira", "cargo": "Costureira", "pagamento": "Por operação (peça)", "valor_hora": 0.00, "externo": "Sim", "status_pagamento_mes": "Pendente"},
        {"nome": "João Santos", "cargo": "Entregador", "pagamento": "Por hora", "valor_hora": 14.00, "externo": "Não", "status_pagamento_mes": "Pendente"}
    ]

# --- SISTEMA DE LOGIN: USUÁRIOS E SENHAS ---
USUARIOS = {
    "admin": {"senha": "204060", "perfil": "admin", "nome": "Administrador"},
    "conf": {"senha": "2026", "perfil": "conferente", "nome": "Setor de Conferência"},
    "pro": {"senha": "2233", "perfil": "manual", "nome": "Setor Manual / Production"}
}

if "producao_hora" not in st.session_state:
    st.session_state.producao_hora = [
        {"Costureira": "Maria Silva", "9H": 12, "10H": 15, "11H": 14, "12H": 10, "14H": 15, "15H": 16, "16H": 14, "17H": 11},
        {"Costureira": "Juana Costa", "9H": 10, "10H": 12, "11H": 11, "12H": 9, "14H": 13, "15H": 14, "16H": 12, "17H": 10}
    ]

# Dispara a busca automática e sincronização do cofre físico de forma blindada
try:
    # 1. Carrega dados estruturais tradicionais
    carregar_dados_do_banco_para_memoria()
    
    # 2. Carrega dados compactos do Super Robô (Sobrepõe e mantém os dados reais do HD)
    super_robo_carregar_hd_para_memoria()
    
    # Sincroniza as horas gravadas no DB com a gaveta ativa do ponto do mês selecionado
    if "banco_horas_permanente" in st.session_state:
        for reg_h in st.session_state.banco_horas_permanente:
            m_atual_conf = MESES_NUM_GLOBAL.get(st.session_state.get("dash_ref_mes_v30", "Setembro"), "09")
            a_atual_conf = st.session_state.get("dash_ref_ano_v30", "2026")
            chave_periodo_ponto = f"{m_atual_conf}/{a_atual_conf}"
            
            if reg_h.get("mes_ano") == chave_periodo_ponto:
                nome_chave_p = reg_h.get("nome", "").strip().title()
                st.session_state.presencas_ponto[nome_chave_p] = float(reg_h.get("total_horas", 0.0))
except Exception as e:
    pass
# Configuração da página para um visual moderno e amplo
st.set_page_config(
    page_title="Sistema DLR - Confecção", 
    layout="wide", 
    page_icon="🧵"
)

# Estilização básica para um visual mais limpo e profissional
st.markdown("""
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    h1 {color: #1E3A8A; font-weight: 700;}
    h2 {color: #2563EB; font-weight: 600;}
    </style>
""", unsafe_allow_html=True)




# --- TELA DE LOGIN CENTRALIZADA ---
if not st.session_state.logado:
    # Ajustamos a proporção das colunas para centralizar o conteúdo perfeitamente no meio
    col_esq, col_centro, col_dir = st.columns(3)
    
    with col_centro:
        # NOVO: Injeta o comando CSS para forçar a imagem a ficar centralizada no meio da coluna
        st.markdown("""
            <style>
            div[data-testid="stImage"] {
                display: flex;
                justify-content: center;
            }
            </style>
        """, unsafe_allow_html=True)

        # Mantém a exibição da logo com o tamanho perfeito de 200 pixels que você aprovou
        try:
            st.image("logo_dlr.png.png", width=300)
        except Exception:
            st.markdown("<h2 style='text-align: center; color: #4A154B;'>🧵 Confecção DLR</h2>", unsafe_allow_html=True)
            
        st.markdown("<p style='text-align: center; color: #6B7280; font-size: 0.9rem; margin-top: -10px;'>Sistema Integrado de Gestão e Produção</p>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #9CA3AF; margin-top: 20px;'>🔑 Controle de Acesso</p>", unsafe_allow_html=True)
        
        with st.form("form_login", clear_on_submit=False):
            usuario_input = st.text_input("Usuário").strip()
            senha_input = st.text_input("Senha", type="password")
            botao_entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if botao_entrar:
                if usuario_input in USUARIOS and USUARIOS[usuario_input]["senha"] == senha_input:
                    st.session_state.logado = True
                    st.session_state.perfil_atual = USUARIOS[usuario_input]["perfil"]
                    st.session_state.usuario_nome = USUARIOS[usuario_input]["nome"]
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos. Tente novamente.")
                    
    st.stop()

    # --- SISTEMA LOGADO (ATUALIZAÇÃO: TUDO NO LADO ESQUERDO) ---
with st.sidebar:
    st.markdown("### ⚙️ Sessão Ativa")
    st.markdown(f"👤 **Usuário:**\n_{st.session_state.usuario_nome}_")
    # APAGADO: O texto da Área e as linhas divisórias extras saíram daqui
    
        

# Garante que um perfil padrão esteja selecionado ao abrir
if "perfil_atual" not in st.session_state:
    st.session_state.perfil_atual = "admin"


# --- LÓGICA DA ÁREA 1: ADMINISTRAÇÃO ---
if st.session_state.perfil_atual == "admin":
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🗂️ Menu de Páginas")
        
        paginas_admin = {
            "🏠 Dashboard Inicial": "🏠 Dashboard Inicial",
            "👤 Cadastrar Funcionário": "👤 Cadastrar Funcionário",
            "📋 Lotes em Andamento": "📋 Lotes em Andamento",
            "🚚 Serviços Externos": "🚚 Serviços Externos",
            "💰 Financeiro Geral": "💰 Financeiro Geral",
            "📅 Extrato do Mês": "📅 Extrato do Mês"
        }
        
        for label, pagina_id in paginas_admin.items():
            if st.session_state.pagina_admin_atual == pagina_id:
                st.markdown(f"""
                    <div style='background-color: #FFFFFF; color: #000000; padding: 10px 15px; border-radius: 6px; font-weight: bold; text-align: center; border: 2px solid #4A154B; margin-bottom: 8px;'>
                        {label}
                    </div>
                """, unsafe_allow_html=True)
            else:
                if st.button(label, use_container_width=True, key=f"btn_sid_{pagina_id}"):
                    st.session_state.pagina_admin_atual = pagina_id
                    st.rerun()

        # --- DEVOLVENDO O BOTÃO DE SAIR NO FINAL DA BARRA ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
        
        if st.button("🚪 Sair do Sistema", use_container_width=True, type="secondary", key="btn_sair_admin_recuperado"):
            st.session_state.logado = False
            st.session_state.perfil_atual = None
            st.rerun()

                       
    # --- SUB-PÁGINA 1: CADASTRO DE FUNCIONÁRIOS ---
    if st.session_state.pagina_admin_atual == "👤 Cadastrar Funcionário":
        st.subheader("👤 Gestão de Colaboradores — DLR")
        
        if "tipo_tela_func" not in st.session_state:
            st.session_state.tipo_tela_func = "R.F"

        # Seção de botões horizontais
        st.markdown("<br>", unsafe_allow_html=True)
        col_f1, col_f2, col_f_espaco = st.columns(3)
        
        with col_f1:
            tipo_rf = "primary" if st.session_state.tipo_tela_func == "R.F" else "secondary"
            if st.button("📝 Registrar Funcionário (R.F)", use_container_width=True, type=tipo_rf):
                st.session_state.tipo_tela_func = "R.F"
                st.rerun()
                
        with col_f2:
            tipo_lf = "primary" if st.session_state.tipo_tela_func == "L.F" else "secondary"
            if st.button("📋 Lista de Funcionários (L.F)", use_container_width=True, type=tipo_lf):
                st.session_state.tipo_tela_func = "L.F"
                st.rerun()

        st.markdown("---")

        # --- TELA 1: FORMULÁRIO DE CADASTRO (R.F) ---
        if st.session_state.tipo_tela_func == "R.F":
            if "contador_form_func" not in st.session_state:
                st.session_state.contador_form_func = 0
                
            with st.form(key=f"form_cad_{st.session_state.contador_form_func}", clear_on_submit=False):
                nome = st.text_input("Nome Completo")
                cargo = st.selectbox("Cargo", ["Costureira", "Manual", "Revisora", "Conferente", "Supervisor(a)", "Entregador"])
                forma_pagamento = st.selectbox("Forma Pagamento", ["Por hora", "Por operação (peça)", "Fixo"])
                valor_dinheiro = st.number_input("Valor R$", min_value=0.0, format="%.2f")
                
                # REQUISITO EXIGIDO: Novo campo de Chave PIX no formulário de cadastro
                pix_input = st.text_input("Chave PIX para Pagamento (CPF, Celular, Aleatória...)")
                
                externo = st.radio("Externo?", ["Não", "Sim"], horizontal=True)
                
                pre_salvar = st.form_submit_button("💾 Salvar Funcionário")
                
                if pre_salvar:
                    if not nome.strip():
                        st.error("❌ O campo 'Nome Completo' é obrigatório!")
                    elif forma_pagamento in ["Por hora", "Fixo"] and valor_dinheiro <= 0:
                        st.error(f"❌ Para contratos '{forma_pagamento}', o campo 'Valor R$' deve ser maior que R$ 0,00.")
                    else:
                        st.session_state.aguardando_confirmacao_func = {
                            "nome": nome, "cargo": cargo, "pagamento": forma_pagamento, 
                            "valor_hora": valor_dinheiro, "externo": externo, "chave_pix": pix_input.strip()
                        }

            # Confirmação Segura
            if "aguardando_confirmacao_func" in st.session_state and st.session_state.aguardando_confirmacao_func:
                dados_novos = st.session_state.aguardando_confirmacao_func
                st.warning(f"⚠️ **Confirmação de Cadastro:** Tem certeza que deseja salvar o(a) funcionário(a) **{dados_novos['nome']}**?")
                
                col_sim, col_nao = st.columns(2)
                col_sim, col_nao = st.columns(2)
                with col_sim:
                    if st.button("✅ Sim, tenho certeza", use_container_width=True, type="primary"):
                        # CORREÇÃO DE OURO: Todo este bloco agora está perfeitamente embutido dentro do clique do botão!
                        sucesso_db = db_salvar_funcionario(
                            nome=dados_novos["nome"],
                            cargo=dados_novos["cargo"],
                            pagamento=dados_novos["pagamento"],
                            valor_hora=dados_novos["valor_hora"],
                            chave_pix=dados_novos["chave_pix"]
                        )
                        
                        if sucesso_db:
                            st.success(f"🎉 Excelente! **{dados_novos['nome']}** foi registrado permanentemente no HD da empresa!")
                            st.session_state.aguardando_confirmacao_func = None
                            st.session_state.contador_form_func += 1
                            st.rerun()
                        else:
                            st.error("❌ Falha técnica ao tentar gravar o funcionário no banco de dados.")
                            st.session_state.aguardando_confirmacao_func = None
                            st.rerun()
                            
                with col_nao:
                    if st.button("❌ Não, cancelar", use_container_width=True):
                        st.info("Cadastro cancelado.")
                        st.session_state.aguardando_confirmacao_func = None
                        st.rerun()

        # --- TELA 2: LISTA DE FUNCIONÁRIOS (L.F) ---
        elif st.session_state.tipo_tela_func == "L.F":
            st.write("📝 **Dica do Chefe:** Altere os dados ou apague linhas livremente na tabela abaixo. Após terminar, clique em **Confirmar Alterações Feitas** para salvar em definitivo no HD!")
            
            if "funcionarios" not in st.session_state:
                st.session_state.funcionarios = []
                
            # Garante a inicialização da versão dinâmica para controle do cache da tabela
            if "versao_editor_func" not in st.session_state:
                st.session_state.versao_editor_func = 0
                
            chave_tabela_func = f"editor_func_global_v29_v{st.session_state.versao_editor_func}"
            
                    
            # TABELA DO ADMINISTRADOR CONECTADA AO COFRE SQLITE
            funcionarios_atualizados = st.data_editor(
                st.session_state.funcionarios,
                column_config={
                    "nome": st.column_config.TextColumn("👤 Nome Completo"),
                    "cargo": st.column_config.SelectboxColumn("💼 Cargo / Função", options=["Costureira", "Manual", "Revisora", "Conferente", "Supervisor(a)", "Entregador"]),
                    "pagamento": st.column_config.SelectboxColumn("💳 Tipo de Pagamento", options=["Por hora", "Por operação (peça)", "Fixo"]),
                    "valor_hora": st.column_config.NumberColumn("💰 Valor R$", format="R$ %.2f", min_value=0.0),
                    "chave_pix": st.column_config.TextColumn("🔑 Chave PIX")
                },
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic", # Permite adicionar e deletar linhas livremente na tela
                key=chave_tabela_func
            )
            
            # Identifica se o usuário mexeu na estrutura da planilha (editou, apagou ou adicionou)
            dados_mudaram_lf = False
            if chave_tabela_func in st.session_state:
                estado_tabela = st.session_state[chave_tabela_func]
                if estado_tabela["edited_rows"] or estado_tabela["deleted_rows"] or estado_tabela["added_rows"]:
                    dados_mudaram_lf = True
            
            if dados_mudaram_lf:
                st.markdown("<br>", unsafe_allow_html=True)
                st.warning("⚠️ **Aviso de Alteração:** Você modificou dados ou removeu colaboradores!")
                
                col_conf_salvar, col_conf_cancelar = st.columns(2)
                with col_conf_salvar:
                    if st.button("📝 Confirmar Alterações Feitas", use_container_width=True, type="primary", key="btn_salvar_mudancas_lf_db"):
                        try:
                            # 1. Abre o cofre do banco para fazer a limpeza e atualização
                            conn = sqlite3.connect("dlr_confecoes.db")
                            cursor = conn.cursor()
                            
                            # 2. Limpa a tabela antiga para reinjetar a nova lista atualizada da tela
                            cursor.execute("DELETE FROM funcionarios")
                            
                            # 3. Varre a tabela que está na tela e grava linha por linha no HD
                            for linha_f in funcionarios_atualizados:
                                nome_salvar = str(linha_f.get("nome", "")).strip()
                                if nome_salvar: # Só grava se o nome não estiver em branco
                                    cursor.execute("""
                                        INSERT INTO funcionarios (nome, cargo, pagamento, valor_hora, chave_pix)
                                        VALUES (?, ?, ?, ?, ?)
                                    """, (
                                        nome_salvar,
                                        linha_f.get("cargo", "Costureira"),
                                        linha_f.get("pagamento", "Por hora"),
                                        float(linha_f.get("valor_hora", 0.0)),
                                        str(linha_f.get("chave_pix", "")).strip()
                                    ))
                                    
                            conn.commit()
                            conn.close()
                            
                            # 4. Atualiza a memória viva do sistema e recarrega a página limpa
                            carregar_dados_do_banco_para_memoria()
                            st.success("🎉 Sucesso! A lista de funcionários foi atualizada e salva permanentemente no HD!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao tentar salvar as alterações no banco de dados: {e}")
                            
                with col_conf_cancelar:
                    if st.button("❌ Descartar Mudanças e Voltar", use_container_width=True, key="btn_cancelar_mudancas_lf_db"):
                        # Limpa o cache limpando a chave da tabela e forçando o recarregamento dos dados do DB
                        if chave_tabela_func in st.session_state:
                            del st.session_state[chave_tabela_func]
                        st.session_state.versao_editor_func += 1
                        st.rerun()        
        

                 # --- SUB-PÁGINA: DASHBOARD INICIAL (Cards + Tabela + Gráficos juntos) ---
    if st.session_state.pagina_admin_atual == "🏠 Dashboard Inicial":
        st.subheader("🏠 Painel Executivo — Indicadores de Desempenho e Faturamento")
        
        # Filtros Globais de Mês e Ano no topo do Dashboard
        col_m_dash, col_a_dash, col_esp_dash = st.columns(3)
        with col_m_dash:
            mes_sel = st.selectbox("Mês de Referência:", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=8, key="dash_ref_mes_v30")
        with col_a_dash:
            ano_sel = st.selectbox("Ano de Referência:", ["2026", "2027", "2028", "2029", "2030"], index=0, key="dash_ref_ano_v30")
            
        st.markdown(f"Exibindo balanço consolidado de: **{mes_sel} de {ano_sel}**")
        st.markdown("<br>", unsafe_allow_html=True)
        
        meses_num = {"Janeiro":"01", "Fevereiro":"02", "Março":"03", "Abril":"04", "Maio":"05", "Junho":"06", "Julho":"07", "Agosto":"08", "Setembro":"09", "Outubro":"10", "Novembro":"11", "Dezembro":"12"}
        mes_procurado = meses_num[mes_sel]

        # --- MOTOR MATEMÁTICO AVANÇADO UNIFICADO ---
        entradas_livro_caixa = 0.0
        total_saidas_eg = 0.0
        
        # 1. Varre o Livro Caixa Geral para somar as Entradas e Saídas do mês
        if "movimentacoes_caixa" in st.session_state and st.session_state.movimentacoes_caixa:
            for mov in st.session_state.movimentacoes_caixa:
                data_mov = mov.get("Data", "")
                if f"/{mes_procurado}/{ano_sel}" in data_mov or data_mov == "":
                    v_total = mov.get("Valor Total", 0.0)
                    if mov.get("Tipo", "Saída") == "Entrada":
                        entradas_livro_caixa += v_total
                    else:
                        total_saidas_eg += v_total

        # 2. REQUISITO EXIGIDO: Faturamento real blindado (Preço Unitário × Peças Prontas Reais do Conferente)
        faturamento_lotes_concluidos = 0.0
        if "lotes_gerais" in st.session_state and st.session_state.lotes_gerais:
            for item in st.session_state.lotes_gerais:
                data_cad_str = item.get("data_cadastro", "")
                status_atual = str(item.get("status", "Pendente")).strip()
                
                # O faturamento continua filtrado pelo mês/ano selecionado no topo do Dashboard
                if f"/{mes_procurado}/{ano_sel}" in data_cad_str and status_atual == "Concluído":
                    try:
                        # Puxa o preço e a produção física real digitada
                        preco_unitario = float(item.get("preco_unitario", item.get("preco", 0.0)))
                        pecas_reais_produzidas = int(item.get("qtd_pronta", 0))
                        
                        # BLINDAGEM DE ENGENHARIA: Se o manual resetou para 0, busca a quantidade cadastrada original
                        if pecas_reais_produzidas == 0:
                            pecas_reais_produzidas = int(item.get("qtd_prevista", item.get("qtd", 0)))
                        
                        faturamento_lotes_concluidos += (preco_unitario * pecas_reais_produzidas)
                    except Exception as e:
                        pass

        # TOTALIZADOR DA ENTRADA DE CAIXA LEGÍTIMO DA DLR
        total_entradas_eg = entradas_livro_caixa + faturamento_lotes_concluidos

       
        # 3. Varre a Folha Interna calculando os valores líquidos com vales ativos
        total_folha_interna = 0.0
        if "funcionarios" in st.session_state:
            # Inicializa o banco de horas se o pen drive não tiver sido lido ainda
            if "presencas_ponto" not in st.session_state:
                st.session_state.presencas_ponto = {}
                
            for f in st.session_state.funcionarios:
                bruto_colaborador = 0.0
                nome_f = f["nome"]
                nome_f_chave = nome_f.strip().title() # Padroniza para cruzar com o ponto
                tipo_pag = f.get("pagamento", "Fixo")
                valor_base = float(f.get("valor_hora", 0.0)) # Seu campo de salário ou valor/h
                
                # --- REGRA DE OURO OPERACIONAL EXIGIDA ---
                if tipo_pag == "Fixo":
                    # REGRA 1: Pagamento Fixo puxa o salário cheio direto
                    bruto_colaborador = valor_base
                elif tipo_pag == "Por operação":
                    # REGRA 2: Quem trabalha por Operação (Lotes) fica zerado na folha interna
                    bruto_colaborador = 0.0
                elif tipo_pag == "Por hora":
                        horas_relogio = 0.0
                        
                        # Captura as variáveis de data de forma dinâmica
                        v_mes_tela = mes_sel if 'mes_sel' in locals() else (mes_prod_sel if 'mes_prod_sel' in locals() else "Setembro")
                        v_ano_tela = ano_sel if 'ano_sel' in locals() else (ano_prod_sel if 'ano_prod_sel' in locals() else "2026")
                        
                        m_f_c = meses_num.get(v_mes_tela, "09")
                        chave_periodo_pesquisa = f"{m_f_c}/{v_ano_tela}"
                        
                        # BARREIRA DE PROTEÇÃO ÚNICA: Varre o DB comparando em letras minúsculas
                        if "banco_horas_permanente" in st.session_state:
                            for reg_h in st.session_state.banco_horas_permanente:
                                if reg_h.get("mes_ano") == chave_periodo_pesquisa:
                                    if str(reg_h.get("nome")).strip().lower() == str(nome_f).strip().lower():
                                        horas_relogio = float(reg_h.get("total_horas", 0.0))
                                        break
                                        
                        bruto_colaborador = horas_relogio * valor_base
                    
                # Deduz os vales parcelados ativos do mês atual
                total_descontos_mes = 0.0
                if "adiantamentos" in st.session_state:
                    for ad in st.session_state.adiantamentos:
                        if ad.get("nome") == nome_f and ad.get("status_vale", "Ativo") != "Cancelado":
                            try:
                                dt_v = datetime.strptime(ad.get("data", ""), "%d/%m/%Y")
                                m_origem = dt_v.month; a_origem = dt_v.year
                            except:
                                m_origem = int(mes_procurado); a_origem = int(ano_sel)
                            
                            texto_t = ad.get("tipo", "1x")
                            q_parc = 1
                            for x in range(1, 4):
                                if f"{x}x" in texto_t: q_parc = x; break
                                
                            m_corrido = m_origem; a_corrido = a_origem; m_cobrancas = []
                            for _ in range(q_parc):
                                m_cobrancas.append(f"{m_corrido:02d}/{a_corrido}")
                                m_corrido += 1
                                if m_corrido > 12: m_corrido = 1; a_corrido += 1
                                
                            if f"{mes_procurado}/{ano_sel}" in m_cobrancas:
                                total_descontos_mes += ad.get("valor_parcela", 0.0)
                                
                liquido_a_receber = max(0.0, bruto_colaborador - total_descontos_mes)
                total_folha_interna += liquido_a_receber

        # --- MOTOR DE GASTOS DO PAINEL EXECUTIVO COM AS CHAVES REAIS DA DLR (5 COLUNAS) ---
        
        # 1. CÁLCULO DA FOLHA EXTERNA (Lê as chaves exatas: "Valor por peça", "QTD de Peças" e "Status")
        total_folha_externa = 0.0
        if "lotes_externos" in st.session_state and st.session_state.lotes_externos:
            chave_periodo_externo = f"/{mes_procurado}/{ano_sel}" # Ex: /09/2026
            
            for item_ext in st.session_state.lotes_externos:
                data_ext = str(item_ext.get("Data", "")).strip()
                status_ext = str(item_ext.get("Status", "Em andamento")).strip().lower()
                
                # FILTRO DE SEGURANÇA: Bate o mês/ano selecionado E exige o Status "Concluído"
                if ((chave_periodo_externo in data_ext) or (data_ext == "")) and (status_ext == "concluído"):
                    try:
                        v_peca = float(item_ext.get("Valor por peça", 0.0))
                        qtd_pecas = int(item_ext.get("QTD de Peças", 0))
                        desconto_lote = float(item_ext.get("Desconto", 0.0)) # Puxa o desconto do lote
                        
                        # A MATEMÁTICA CORRETA: Soma o total já batido o desconto!
                        total_folha_externa += ((v_peca * qtd_pecas) - desconto_lote)
                    except Exception as e:
                        pass

        # --- CÁLCULO MATEMÁTICO DO SALDO LÍQUIDO RECALIBRADO ---
        saldo_liquido_final = total_entradas_eg - total_saidas_eg - total_folha_interna - total_folha_externa

        # 3. RENDERIZAÇÃO FORMATADA DOS 5 CARDS LADO A LADO NA TELA
        col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)

        with col_c1:
            st.markdown(f"""
                <div style='background-color: #2E7D32; padding: 15px; border-radius: 8px; color: white; text-align: center; height: 110px;'>
                    <span style='font-size: 14px;'>💵 Entrada Caixa</span><br>
                    <span style='font-size: 20px; font-weight: bold;'>R$ {total_entradas_eg:,.2f}</span>
                </div>
            """, unsafe_allow_html=True)

        with col_c2:
            st.markdown(f"""
                <div style='background-color: #E65100; padding: 15px; border-radius: 8px; color: white; text-align: center; height: 110px;'>
                    <span style='font-size: 14px;'>📦 Saídas Gerais</span><br>
                    <span style='font-size: 20px; font-weight: bold;'>R$ {total_saidas_eg:,.2f}</span>
                </div>
            """, unsafe_allow_html=True)

        with col_c3:
            st.markdown(f"""
                <div style='background-color: #C62828; padding: 15px; border-radius: 8px; color: white; text-align: center; height: 110px;'>
                    <span style='font-size: 14px;'>🧱 Folha Interna</span><br>
                    <span style='font-size: 20px; font-weight: bold;'>R$ {total_folha_interna:,.2f}</span>
                </div>
            """, unsafe_allow_html=True)

        with col_c4:
            st.markdown(f"""
                <div style='background-color: #B71C1C; padding: 15px; border-radius: 8px; color: white; text-align: center; height: 110px;'>
                    <span style='font-size: 14px;'>🧵 Folha Externo</span><br>
                    <span style='font-size: 20px; font-weight: bold;'>R$ {total_folha_externa:,.2f}</span>
                </div>
            """, unsafe_allow_html=True)

        with col_c5:
            # Cor do saldo muda dinamicamente: Azul se positivo, Vermelho escuro se negativo
            cor_saldo_box = "#1565C0" if saldo_liquido_final >= 0 else "#811C1C"
            st.markdown(f"""
                <div style='background-color: {cor_saldo_box}; padding: 15px; border-radius: 8px; color: white; text-align: center; height: 110px;'>
                    <span style='font-size: 14px;'>💰 Saldo Líquido</span><br>
                    <span style='font-size: 20px; font-weight: bold;'>R$ {saldo_liquido_final:,.2f}</span>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br><hr>", unsafe_allow_html=True)

        # --- ESPELHAMENTO DO GRÁFICO DE RENDIMENTO BRUTO DIÁRIO ---
        st.markdown(f"#### 📈 Gráfico de Rendimento Global: {mes_sel} de {ano_sel}")
        st.write("Acompanhe o volume total de peças prontas faturadas e acumuladas no dia a dia da fábrica:")

        if "banco_producao_diaria" not in st.session_state:
            st.session_state.banco_producao_diaria = {}

        dados_grafico_dash_bruto = []
        
        # Identifica a quantidade de dias correta do mês selecionado
        if mes_procurado in ["01", "03", "05", "07", "08", "10", "12"]: 
            dias_no_mes_dash = 31
        elif mes_procurado in ["04", "06", "09", "11"]: 
            dias_no_mes_dash = 30
        else: 
            dias_no_mes_dash = 28

        # Loop estruturado para montar o gráfico com todos os dias sequenciais
        for d_painel in range(1, dias_no_mes_dash + 1):
            data_chave_painel = f"{d_painel:02d}/{mes_procurado}/{ano_sel}"
            total_pecas_da_data = st.session_state.banco_producao_diaria.get(data_chave_painel, 0)
            
            dados_grafico_dash_bruto.append({
                "Dia do Mês": f"Dia {d_painel:02d}",
                "Peças Prontas (Total Fábrica)": total_pecas_da_data
            })

        # Desenha o gráfico de barras espelhado no painel principal
        st.bar_chart(
            data=dados_grafico_dash_bruto, 
            x="Dia do Mês", 
            y="Peças Prontas (Total Fábrica)", 
            use_container_width=True, 
            height=340
        )
        
        # Resumo final informativo abaixo do gráfico
        soma_acumulada_dash = sum([item_g["Peças Prontas (Total Fábrica)"] for item_g in dados_grafico_dash_bruto])
        st.info(f"📊 **Totalizadores do Período:** O volume total acumulado produzido em {mes_sel} somou **{soma_acumulada_dash} peças prontas** na esteira!")
    
    if st.session_state.pagina_admin_atual == "🚚 Serviços Externos":
        st.subheader("🚚 Gerenciamento de Serviços Externos")
        
        if "lotes_externos" not in st.session_state:
            st.session_state.lotes_externos = []
            
        if "contador_form_externo" not in st.session_state:
            st.session_state.contador_form_externo = 0
            
        # --- COLETA AUTOMÁTICA DE OFs E REFERÊNCIAS DA ESTEIRA GERAL ---
        lista_ofs_cadastrados = []
        mapa_of_para_referencia = {}
        
        if "lotes_gerais" in st.session_state and st.session_state.lotes_gerais:
            for lote in st.session_state.lotes_gerais:
                v_of = str(lote.get("of", lote.get("O.F.", ""))).strip()
                v_ref = str(lote.get("referencia", lote.get("Referência", ""))).strip()
                if v_of and v_of not in lista_ofs_cadastrados:
                    lista_ofs_cadastrados.append(v_of)
                    mapa_of_para_referencia[v_of] = v_ref
                    
        chave_reset_ext = st.session_state.contador_form_externo
        todos_funcs = [f["nome"] for f in st.session_state.funcionarios] if "funcionarios" in st.session_state else []

        # --- DESENHO DOS CAMPOS LIVRES DINÂMICOS NA TELA ---
        col_ex1, col_ex2, col_ex3 = st.columns(3)
        with col_ex1:
            costureira_sel = st.selectbox("Selecionar Costureira", todos_funcs if todos_funcs else ["Nenhum funcionário cadastrado"], key=f"ext_cost_sel_{chave_reset_ext}")
            
            if lista_ofs_cadastrados:
                of_input = st.selectbox("Selecionar Número do OF", ["Escolha um OF..."] + lista_ofs_cadastrados, key=f"ext_of_sel_{chave_reset_ext}")
            else:
                st.warning("⚠️ Nenhum lote ativo na esteira para puxar OF.")
                of_input = "Escolha um OF..."
                
        with col_ex2:
            # AUTOMAÇÃO EM TEMPO REAL: Atualiza a referência no exato milissegundo do clique do OF
            if of_input != "Escolha um OF..." and of_input in mapa_of_para_referencia:
                ref_sugerida = mapa_of_para_referencia[of_input]
                ref_input = st.selectbox("Referência da Peça (Puxada do Lote)", [ref_sugerida], index=0, disabled=True, key=f"ext_ref_sel_{chave_reset_ext}")
            else:
                ref_input = st.selectbox("Referência da Peça", ["Aguardando OF..."], index=0, disabled=True, key=f"ext_ref_sel_{chave_reset_ext}")
                
            nome_peca_input = st.text_input("Nome da Peça (ex: Camiseta, Bermuda)", key=f"ext_nome_p_{chave_reset_ext}")
            
        with col_ex3:
            valor_peca_input = st.number_input("Valor por Peça (R$)", min_value=0.0, format="%.2f", step=0.10, key=f"ext_v_p_{chave_reset_ext}")
            qtd_input = st.number_input("Quantidade de Peças", min_value=1, step=50, value=1, key=f"ext_qtd_p_{chave_reset_ext}")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botão clássico cinza posicionado perfeitamente na tela
        registrar_ext = st.button("🚚 Registrar Lote Externo", use_container_width=True, key=f"btn_registrar_ext_fixo_{chave_reset_ext}")
            
        # --- MOTOR DE VALIDAÇÃO E GRAVAÇÃO COMPACTA NO HD ---
        if registrar_ext:
            if not todos_funcs:
                st.error("❌ Cadastre primeiro um funcionário para registrar um serviço externo.")
            elif of_input == "Escolha um OF..." or not nome_peca_input.strip():
                st.error("❌ Selecione um OF válido e preencha o Nome da Peça para registrar!")
            elif valor_peca_input <= 0:
                st.error("❌ O valor por peça deve ser maior que R$ 0,00.")
            else:
                data_hoje = datetime.now().strftime("%d/%m/%Y")
                
                st.session_state.lotes_externos.append({
                    "Data": data_hoje,
                    "Nome": costureira_sel,
                    "Número OF": of_input.strip(),
                    "Referência da Peça": ref_input.strip(),
                    "Nome da peça": nome_peca_input.strip(),
                    "Valor por peça": valor_peca_input,
                    "Desconto": 0.0,
                    "QTD de Peças": int(qtd_input),
                    "Status": "Em andamento",
                    "Situação de Pagamento": "Pendente",
                    "Chave PIX Customizada": ""
                })
                
                # Tranca as informações no banco de dados do HD na mesma hora pelo robô
                super_robo_trancar_memoria_para_hd()
                
                st.success("🎉 Lote externo cadastrado com sucesso de faturamento!")
                st.session_state.contador_form_externo += 1
                st.rerun()
        
        # --- REQUISITO EXIGIDO: FILTROS DE MÊS, ANO E BUSCA POR OF ---
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.markdown("### 📋 Histórico de Lançamentos e Controle de Serviços Externos")
        
        col_m_ext, col_a_ext, col_busca_combinada = st.columns(3)
        with col_m_ext:
            mes_ext_sel = st.selectbox("Filtrar por Mês:", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=8, key="filtro_mes_externo_final_v12")
        with col_a_ext:
            ano_ext_sel = st.selectbox("Filtrar por Ano:", ["2026", "2027", "2028", "2029", "2030"], index=0, key="filtro_ano_externo_final_v12")
        with col_busca_combinada:
            pesquisa_texto = st.text_input("🔍 Pesquisar por Nome ou OF:", key="busca_combinada_externo_input_v12").strip().lower()

        st.write(f"Exibindo lotes ativos ou lançados em: **{mes_ext_sel} de {ano_ext_sel}**")
        st.write("📝 **Dica do Chefe:** Dê dois cliques em **Status**, **Situação de Pagamento**, **Valor por peça** ou **QTD** para editar! A Chave PIX agora muda automática com a Lista de Funcionários.")

        if "lotes_externos" in st.session_state and st.session_state.lotes_externos:
            linhas_tabela_externos = []
            meses_num = {"Janeiro":"01", "Fevereiro":"02", "Março":"03", "Abril":"04", "Maio":"05", "Junho":"06", "Julho":"07", "Agosto":"08", "Setembro":"09", "Outubro":"10", "Novembro":"11", "Dezembro":"12"}
            mes_procurado = meses_num[mes_ext_sel]
            
            # CHAVE DA SOLUÇÃO: Dicionário atualizado em tempo real que lê o PIX direto da ficha oficial de funcionários
            pix_funcionarios = {f["nome"]: f.get("chave_pix", "") for f in st.session_state.get("funcionarios", [])}
            
            for index, item in enumerate(st.session_state.lotes_externos):
                data_lote = item.get("Data", "")
                status_atual = item.get("Status", "Em andamento")
                of_lote = item.get("Número OF", "")
                nome_costureira = item.get("Nome", "")
                
                pertence_ao_mes = f"/{mes_procurado}/{ano_ext_sel}" in data_lote
                continua_pendente = (status_atual == "Em andamento")
                
                if pertence_ao_mes or continua_pendente:
                    if pesquisa_texto:
                        if pesquisa_texto not in nome_costureira.lower() and pesquisa_texto not in of_lote.lower():
                            continue
                        
                    v_peca = float(item.get("Valor por peça", 0.0))
                    qtd = int(item.get("QTD de Peças", 0))
                    desconto_lote = float(item.get("Desconto", 0.0)) # Puxa o desconto salvo no HD
                    
                    # VINCULAÇÃO REAL COM A GAVETA DE PIX
                    chave_pix_viva = pix_funcionarios.get(nome_costureira, "Não cadastrado")
                    
                    # MATEMÁTICA REAL EXIGIDA: (Valor por peça × QTD) - Desconto
                    valor_total_calculado = (v_peca * qtd) - desconto_lote
                    
                    linhas_tabela_externos.append({
                        "ID_Original": index,
                        "Data": data_lote,
                        "Nome": nome_costureira,
                        "Número OF": of_lote,
                        "Referência da Peça": item.get("Referência da Peça", ""),
                        "Nome da peça": item.get("Nome da peça", ""),
                        "Valor por peça": v_peca,
                        "QTD de Peças": qtd,
                        "Desconto": desconto_lote, # Injeta na tabela visual
                        "Valor total": valor_total_calculado, # Aplica a subtração na tela!
                        "Status": status_atual,
                        "Chave PIX": chave_pix_viva,
                        "Situação de Pagamento": item.get("Situação de Pagamento", "Pendente")
                    })
            
            if linhas_tabela_externos:
                if "versao_editor_ext" not in st.session_state:
                    st.session_state.versao_editor_ext = 0
                    
                chave_tabela_ext = f"editor_ext_v14_{mes_ext_sel}_{ano_ext_sel}_{pesquisa_texto}_v{st.session_state.versao_editor_ext}"
                
                tabela_ext_editada = st.data_editor(
                    linhas_tabela_externos,
                    column_config={
                        "ID_Original": None,
                        "Data": st.column_config.TextColumn("Data", disabled=True),
                        "Nome": st.column_config.TextColumn("Nome", disabled=True),
                        "Número OF": st.column_config.TextColumn("Número OF", disabled=True),
                        "Referência da Peça": st.column_config.TextColumn("Referência da Peça", disabled=True),
                        "Nome da peça": st.column_config.TextColumn("Nome da peça", disabled=True),
                        "Valor por peça": st.column_config.NumberColumn("Valor por peça", format="R$ %.2f", min_value=0.0),
                        "QTD de Peças": st.column_config.NumberColumn("QTD de Peças", min_value=1, step=1),
                        "Desconto": st.column_config.NumberColumn("📉 Desconto (R$)", format="R$ %.2f", min_value=0.0), # Editável
                        "Valor total": st.column_config.NumberColumn("Valor total", format="R$ %.2f", disabled=True), # Travado com o cálculo
                        "Status": st.column_config.SelectboxColumn("Status", options=["Em andamento", "Cancelado", "Concluído"], required=True),
                        "Chave PIX": st.column_config.TextColumn("🔑 Chave PIX", disabled=True),
                        "Situação de Pagamento": st.column_config.SelectboxColumn("💳 Situação de Pagamento", options=["Pendente", "Pago"], required=True)
                    },
                    hide_index=True, use_container_width=True, key=chave_tabela_ext
                )
                
                # MONITOR DE MUDANÇAS ATUALIZADO: Inclui a coluna 'Desconto' na varredura técnica
                dados_mudaram = False
                for linha in tabela_ext_editada:
                    idx_global = linha["ID_Original"]
                    original = st.session_state.lotes_externos[idx_global]
                    
                    if (float(linha["Valor por peça"]) != float(original.get("Valor por peça", 0.0)) or 
                        int(linha["QTD de Peças"]) != int(original.get("QTD de Peças", 0)) or 
                        float(linha.get("Desconto", 0.0)) != float(original.get("Desconto", 0.0)) or # <=== MONITOR DO DESCONTO ATIVADO!
                        str(linha["Status"]).strip() != str(original.get("Status", "")).strip() or 
                        str(linha["Situação de Pagamento"]).strip() != str(original.get("Situação de Pagamento", "Pendente")).strip()):
                        dados_mudaram = True
                        break
                
                # Exibe a trava amarela de segurança se houver mudanças digitadas
                if dados_mudaram:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.warning("⚠️ **Aviso de Alteração de Lotes:** Você modificou dados desta folha! Salve para computar os novos descontos e totais.")
                    
                    col_salvar_ext, col_cancelar_ext = st.columns(2)
                    with col_salvar_ext:
                        if st.button("💾 Confirmar Alterações do Lote Externo", use_container_width=True, type="primary", key="btn_salvar_ext_v14_f"):
                            for linha in tabela_ext_editada:
                                idx_global = linha["ID_Original"]
                                
                                st.session_state.lotes_externos[idx_global]["Valor por peça"] = float(linha["Valor por peça"])
                                st.session_state.lotes_externos[idx_global]["QTD de Peças"] = int(linha["QTD de Peças"])
                                st.session_state.lotes_externos[idx_global]["Desconto"] = float(linha.get("Desconto", 0.0)) # <=== GRAVA O DESCONTO NO COFRE!
                                st.session_state.lotes_externos[idx_global]["Status"] = str(linha["Status"]).strip()
                                st.session_state.lotes_externos[idx_global]["Situação de Pagamento"] = str(linha["Situação de Pagamento"]).strip()
                            
                            # Limpa o cache visual e tranca direto no arquivo .db do HD
                            if chave_tabela_ext in st.session_state:
                                del st.session_state[chave_tabela_ext]
                            st.session_state.versao_editor_ext += 1
                            
                            super_robo_trancar_memoria_para_hd()
                            st.success("🎉 Excelente! Todas as edições e descontos foram salvos com sucesso absoluto no HD!")
                            st.rerun()
                            
                    with col_cancelar_ext:
                        if st.button("❌ Descartar Mudanças e Voltar", use_container_width=True, key="btn_descartar_ext_v14_f"):
                            if chave_tabela_ext in st.session_state:
                                del st.session_state[chave_tabela_ext]
                            st.session_state.versao_editor_ext += 1
                            st.rerun()
            else:
                st.info("💡 Nenhum lote encontrado para os filtros selecionados.")
        else:
            st.info("💡 Nenhum lote de serviço externo registrado até o momento.")
          

    
             # Sub-aba: Financeiro Geral
    elif st.session_state.pagina_admin_atual == "💰 Financeiro Geral":
        st.subheader("💰 Fluxo de Caixa Dinâmico — Entradas e Saídas")
        
        # INTERRUPTOR INTELIGENTE: Atualiza a tela no mesmo instante!
        tipo_mov = st.selectbox(
            "Tipo de Movimentação", 
            ["Saída", "Entrada", "Saída (Vale de Funcionário)"],
            key="fc_tipo_mov_v32"
        )
        
        # Inicializa as variáveis de controle de fluxo e reset se não existirem
        if "versao_form_caixa" not in st.session_state:
            st.session_state.versao_form_caixa = 0
        if "clicou_registrar_fc" not in st.session_state:
            st.session_state.clicou_registrar_fc = False
            
        chave_reset_fc = st.session_state.versao_form_caixa

        # --- CAMPOS DINÂMICOS LIVRES DE ALTA PERFORMANCE ---
        if tipo_mov == "Saída (Vale de Funcionário)":
            todos_funcs = [f["nome"] for f in st.session_state.funcionarios] if "funcionarios" in st.session_state else []
            
            if not todos_funcs:
                st.warning("⚠️ Cadastre primeiro um funcionário na aba 'Cadastrar Funcionário' para liberar a lista.")
                func_vale = "Nenhum cadastrado"
            else:
                func_vale = st.selectbox("Selecione o Funcionário que pediu o Vale", todos_funcs, key=f"fc_func_sel_{chave_reset_fc}")
            
            valor_mov = st.number_input("Valor do Vale (R$)", min_value=0.0, format="%.2f", step=10.0, key=f"fc_val_vale_{chave_reset_fc}")
            parcelas = st.selectbox("Parcelar em quantas vezes? (Limite de 3x para Vales)", [1, 2, 3], index=0, key=f"fc_parc_vale_{chave_reset_fc}")
            descricao_mov = f"Vale para {func_vale}"
            
        else:
            func_vale = None
            descricao_mov = st.text_input("Descrição / Motivo da Movimentação (Linha, Luz, Combustível, etc.)", key=f"fc_desc_geral_{chave_reset_fc}")
            valor_mov = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f", step=50.0, key=f"fc_val_geral_{chave_reset_fc}")
            
            # CORREÇÃO CRÍTICA DA FIÇÃO: Adicionado a lista de parcelas de 1 a 12 corrigida
            lista_opcoes_parcelas = list(range(1, 13))
            parcelas = st.selectbox("Quantidade de parcelas (Se houver)", options=lista_opcoes_parcelas, index=0, key=f"fc_parc_geral_{chave_reset_fc}")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BOTÃO CLÁSSICO DE DISPARO INICIAL (FIXO NO LOCAL QUE VOCÊ CIRCULOU) ---
        if not st.session_state.clicou_registrar_fc:
            if st.button("💾 Registrar no Caixa", use_container_width=True, key=f"btn_disparo_inicial_fc_{chave_reset_fc}"):
                # Valida os campos obrigatórios antes de abrir o aviso de confirmação
                if valor_mov <= 0:
                    st.error("❌ Por favor, digite um valor maior que R$ 0,00.")
                elif tipo_mov != "Saída (Vale de Funcionário)" and not descricao_mov.strip():
                    st.error("❌ Por favor, preencha a descrição do motivo desta movimentação.")
                else:
                    st.session_state.clicou_registrar_fc = True
                    st.rerun()

        # --- CONTROLADOR DO AVISO AMARELO (SÓ ABRE APÓS O CLIQUE NO BOTÃO ACIMA) ---
        if st.session_state.clicou_registrar_fc:
            st.warning(f"⚠️ **Aviso de Alteração de Caixa:** Tem certeza que deseja salvar o lançamento de **R$ {valor_mov:.2f}** como **{tipo_mov}**?")
            
            col_salvar_fc, col_cancelar_fc = st.columns(2)
            
            with col_salvar_fc:
                if st.button("✅ Sim, confirmar e salvar", use_container_width=True, type="primary", key="btn_confirmar_caixa_v32"):
                    data_hoje = datetime.now().strftime("%d/%m/%Y")
                    
                    if "movimentacoes_caixa" not in st.session_state:
                        st.session_state.movimentacoes_caixa = []
                        
                    # Insere no Livro Caixa Geral da fábrica
                    st.session_state.movimentacoes_caixa.append({
                        "Data": data_hoje,
                        "Tipo": "Saída" if "Saída" in tipo_mov else "Entrada",
                        "Detalhe / Categoria": "Vale de Funcionário" if "Vale" in tipo_mov else "Geral",
                        "Descrição": descricao_mov,
                        "Valor Total": valor_mov,
                        "Parcelas": parcelas
                    })

                    # Se for vale, cria o espelho automático para o desconto em folha
                    if tipo_mov == "Saída (Vale de Funcionário)":
                        tipo_registro = f"Adiantamento Parcelado de {parcelas}x" if parcelas > 1 else "Adiantamento Parcelado de 1x"
                        if "adiantamentos" not in st.session_state:
                            st.session_state.adiantamentos = []
                            
                        st.session_state.adiantamentos.append({
                            "nome": func_vale, 
                            "valor_bruto": valor_mov,
                            "valor_parcela": valor_mov / parcelas,
                            "tipo": tipo_registro,
                            "data": data_hoje
                        })
                        
                    # Tranca tudo direto no arquivo .db do HD em definitivo
                    super_robo_trancar_memoria_para_hd()
                    
                    # Reseta os estados e limpa os campos da tela
                    st.session_state.clicou_registrar_fc = False
                    st.session_state.versao_form_caixa += 1
                    
                    st.success(f"🎉 Sucesso! {tipo_mov} de R$ {valor_mov:.2f} gravado com segurança absoluta no HD!")
                    st.rerun()
                    
            with col_cancelar_fc:
                if st.button("❌ Não, cancelar", use_container_width=True, key="btn_cancelar_caixa_v32"):
                    st.session_state.clicou_registrar_fc = False
                    st.rerun()

    elif st.session_state.pagina_admin_atual == "📅 Extrato do Mês":
        st.subheader("📅 Livro Caixa — Extrato de Todas as Movimentações")
        
        # Filtros de mês e ano retroativos
        col_mes, col_ano, col_vazia = st.columns(3)
        with col_mes:
            mes_sel = st.selectbox(
                "Selecionar Mês:",
                ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
                index=8
            )
        with col_ano:
            ano_sel = st.selectbox(
                "Selecionar Ano:",
                ["2026", "2027", "2028", "2029", "2030"],
                index=0
            )
            
        st.write(f"Exibindo movimentações cronológicas referentes a: **{mes_sel} de {ano_sel}**")
        
        if "tipo_extrato_ativo" not in st.session_state:
            st.session_state.tipo_extrato_ativo = "E.G"

        # Seção dos três botões alinhados (E.G, E.V e F.P)
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2, col_btn3, col_espaco = st.columns(4)
        
        with col_btn1:
            if st.session_state.tipo_extrato_ativo == "E.G":
                st.markdown("<style>button[key='btn_ext_geral'] { background-color: #FFFFFF !important; color: #000000 !important; font-weight: bold !important; border: 2px solid #4A154B !important; }</style>", unsafe_allow_html=True)
            if st.button("📊 Extrato Geral (E.G)", use_container_width=True, key="btn_ext_geral"):
                st.session_state.tipo_extrato_ativo = "E.G"
                st.rerun()
                
        with col_btn2:
            if st.session_state.tipo_extrato_ativo == "E.V":
                st.markdown("<style>button[key='btn_ext_vale'] { background-color: #FFFFFF !important; color: #000000 !important; font-weight: bold !important; border: 2px solid #4A154B !important; }</style>", unsafe_allow_html=True)
            if st.button("💸 Extrato de Vale (E.V)", use_container_width=True, key="btn_ext_vale"):
                st.session_state.tipo_extrato_ativo = "E.V"
                st.rerun()

        with col_btn3:
            if st.session_state.tipo_extrato_ativo == "F.P":
                st.markdown("<style>button[key='btn_folha_pag'] { background-color: #FFFFFF !important; color: #000000 !important; font-weight: bold !important; border: 2px solid #4A154B !important; }</style>", unsafe_allow_html=True)
            if st.button("📝 Folha de Pag. (F.P)", use_container_width=True, key="btn_folha_pag"):
                st.session_state.tipo_extrato_ativo = "F.P"
                st.rerun()

        st.markdown("---")

        meses_num = {"Janeiro":"01", "Fevereiro":"02", "Março":"03", "Abril":"04", "Maio":"05", "Junho":"06", "Julho":"07", "Agosto":"08", "Setembro":"09", "Outubro":"10", "Novembro":"11", "Dezembro":"12"}
        mes_procurado = meses_num[mes_sel]

        # --- TELA DO EXTRATO GERAL (E.G) ---
        if st.session_state.tipo_extrato_ativo == "E.G":
            st.markdown(f"#### 📂 Visualizando: Extrato Geral ({mes_sel}/{ano_sel})")
            if "movimentacoes_caixa" in st.session_state and st.session_state.movimentacoes_caixa:
                linhas_tabela_eg = []
                saldo_acumulado = 0.0
                for mov in st.session_state.movimentacoes_caixa:
                    data_mov = mov.get("Data", "")
                    if f"/{mes_procurado}/{ano_sel}" in data_mov or data_mov == "":
                        v_total = mov.get("Valor Total", 0.0)
                        tipo_m = mov.get("Tipo", "Saída")
                        valor_final = -v_total if tipo_m == "Saída" else v_total
                        saldo_acumulado += valor_final
                        linhas_tabela_eg.append({"Data": data_mov, "Descrição": mov.get("Descrição", ""), "Valor": valor_final})
                
                if linhas_tabela_eg:
                    linhas_tabela_eg.append({"Data": "", "Descrição": "📊 SALDO TOTAL DO CAIXA", "Valor": saldo_acumulado})
                    st.dataframe(linhas_tabela_eg, column_config={"Data": st.column_config.TextColumn("Data", width="small"), "Descrição": st.column_config.TextColumn("Descrição"), "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")}, hide_index=True, use_container_width=True)
                    if saldo_acumulado < 0:
                        st.error(f"🔴 Caixa Negativo: Saldo em **R$ {saldo_acumulado:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
                    else:
                        st.success(f"🟢 Caixa Positivo: Saldo em **R$ {saldo_acumulado:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
                else:
                    st.info(f"💡 Nenhuma movimentação em {mes_sel}/{ano_sel}.")
            else:
                st.info("💡 Nenhuma movimentação geral registrada.")
                
        # --- LÓGICA DO EXTRATO DE VALE (E.V) ---
        elif st.session_state.tipo_extrato_ativo == "E.V":
            st.markdown(f"#### 📂 Visualizando: Controle Individual de Vales e Histórico ({mes_sel}/{ano_sel})")
            
            todos_funcs = [f["nome"] for f in st.session_state.funcionarios] if "funcionarios" in st.session_state else []
            
            if not todos_funcs:
                st.warning("⚠️ Cadastre funcionários no sistema para liberar laudos de históricos.")
            else:
                func_selecionado = st.selectbox("Pesquisar Funcionário para Histórico:", ["Escolha um funcionário..."] + todos_funcs, key="busca_hist_vales_v33_def_sinc")
                
                if func_selecionado != "Escolha um funcionário...":
                    linhas_tabela_ev = []
                    desconto_do_mes_selecionado = 0.0
                    
                    m_f_c = meses_num.get(mes_sel, "09")
                    mes_tela_num = int(m_f_c)
                    ano_tela_num = int(ano_sel)
                    chave_tela_atual = f"{mes_tela_num:02d}/{ano_tela_num}"

                    # 1. VARREDURA 1: Coleta vales registrados na tabela de Adiantamentos (E.V)
                    if "adiantamentos" in st.session_state:
                        for index, ad in enumerate(st.session_state.adiantamentos):
                            if str(ad.get("nome")).strip().lower() == str(func_selecionado).strip().lower() and ad.get("status_vale", "Ativo") != "Cancelado":
                                data_ad = ad.get("data", "")
                                v_bruto = float(ad.get("valor_bruto", 0.0))
                                v_parcela = float(ad.get("valor_parcela", v_bruto))
                                
                                try: dt_v = datetime.strptime(data_ad, "%d/%m/%Y"); m_orig = dt_v.month; a_orig = dt_v.year
                                except: m_orig = mes_tela_num; a_orig = ano_tela_num
                                
                                texto_t = ad.get("tipo", "1x")
                                q_parc = 1
                                for x in range(1, 4):
                                    if f"{x}x" in texto_t: q_parc = x; break
                                    
                                m_cobrancas = []
                                m_corrido = m_orig; a_corrido = a_orig
                                for _ in range(q_parc):
                                    m_cobrancas.append(f"{m_corrido:02d}/{a_corrido}")
                                    m_corrido += 1
                                    if m_corrido > 12: m_corrido = 1; a_corrido += 1
                                    
                                if chave_tela_atual in m_cobrancas:
                                    num_parcela_atual = m_cobrancas.index(chave_tela_atual) + 1
                                    desconto_do_mes_selecionado += v_parcela
                                    linhas_tabela_ev.append({
                                        "ID_Original": f"ADV_{index}",
                                        "Data Lançamento": data_ad,
                                        "Origem / Descrição": f"Vale Parcelado ({num_parcela_atual}/{q_parc})",
                                        "Valor Total Emprestado": v_bruto,
                                        "Valor Parcela deste Mês": v_parcela,
                                        "Status": f"Ativo ({num_parcela_atual}/{q_parc})",
                                        "Dar Baixa / Excluir": False
                                    })

                    # 2. VARREDURA 2: Coleta vales registrados no Fluxo de Caixa Dinâmico (Financeiro Geral)
                    if "movimentacoes_caixa" in st.session_state and st.session_state.movimentacoes_caixa:
                        for index, mov in enumerate(st.session_state.movimentacoes_caixa):
                            data_mov = mov.get("Data", "")
                            descricao_mov = str(mov.get("Descrição", "")).strip().lower()
                            
                            if ("vale" in descricao_mov or "adiantamento" in descricao_mov) and (str(func_selecionado).lower() in descricao_mov):
                                try: dt_m = datetime.strptime(data_mov, "%d/%m/%Y"); m_orig = dt_m.month; a_orig = dt_m.year
                                except: m_orig = mes_tela_num; a_orig = ano_tela_num
                                
                                try: q_parc_caixa = int(mov.get("Parcelas", mov.get("Quantidade de parcelas", 1)))
                                except: q_parc_caixa = 1
                                
                                v_bruto_caixa = float(mov.get("Valor Total", 0.0))
                                v_parcela_caixa = v_bruto_caixa / q_parc_caixa
                                
                                m_cobrancas_caixa = []
                                m_corrido = m_orig; a_corrido = a_orig
                                for _ in range(q_parc_caixa):
                                    m_cobrancas_caixa.append(f"{m_corrido:02d}/{a_corrido}")
                                    m_corrido += 1
                                    if m_corrido > 12: m_corrido = 1; a_corrido += 1
                                    
                                if chave_tela_atual in m_cobrancas_caixa:
                                    num_parcela_atual = m_cobrancas_caixa.index(chave_tela_atual) + 1
                                    desconto_do_mes_selecionado += v_parcela_caixa
                                    linhas_tabela_ev.append({
                                        "ID_Original": f"CX_{index}",
                                        "Data Lançamento": data_mov,
                                        "Origem / Descrição": f"Fluxo de Caixa — Vale ({num_parcela_atual}/{q_parc_caixa})",
                                        "Valor Total Emprestado": v_bruto_caixa,
                                        "Valor Parcela deste Mês": v_parcela_caixa,
                                        "Status": f"Ativo ({num_parcela_atual}/{q_parc_caixa})",
                                        "Dar Baixa / Excluir": False
                                    })
                    
                    # --- DESENHO DA TELA ATUALIZADA ---
                    st.markdown(f"### 📋 Histórico de Vales: **{func_selecionado}**")
                    
                    # Atualiza o Card Vermelho com a soma real de todas as parcelas do mês
                    desc_mes_br = f"{desconto_do_mes_selecionado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    st.markdown(f"<div style='background-color: #B71C1C; padding: 12px; border-radius: 6px; color: white; text-align: center; max-width: 400px; margin-bottom: 20px;'><b>Desconto Ativo em {mes_sel}/{ano_sel}</b><br><h3>R$ {desc_mes_br}</h3></div>", unsafe_allow_html=True)
                    
                    if linhas_tabela_ev:
                        # DESENHO DA PLANILHA DO ADMIN COM A COLUNA DE EXCLUSÃO ATIVADA
                        ev_editado = st.data_editor(
                            linhas_tabela_ev,
                            column_config={
                                "ID_Original": None,
                                "Data Lançamento": st.column_config.TextColumn("📅 Data Lançamento", disabled=True),
                                "Origem / Descrição": st.column_config.TextColumn("📝 Origem / Descrição", disabled=True),
                                "Valor Total Emprestado": st.column_config.NumberColumn("💰 Total Emprestado", format="R$ %.2f", disabled=True),
                                "Valor Parcela deste Mês": st.column_config.NumberColumn("📉 Parcela do Mês", format="R$ %.2f", disabled=True),
                                "Status": st.column_config.TextColumn("📌 Status", disabled=True),
                                "Dar Baixa / Excluir": st.column_config.CheckboxColumn("🗑️ Dar Baixa / Excluir")
                            },
                            hide_index=True, use_container_width=True, key=f"tab_ev_individual_admin_v36_{func_selecionado}"
                        )
                        
                        # VERIFICAÇÃO DE EXCLUSÃO BLINDADA DO ADMIN
                        algum_vale_marcado = any(linha.get("Dar Baixa / Excluir", False) for linha in ev_editado)
                        
                        if algum_vale_marcado:
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.warning(f"⚠️ **Confirmação de Baixa:** Deseja remover permanentemente o(s) vale(s) selecionado(s) de {func_selecionado}?")
                            
                            if st.button("🗑️ Confirmar Remoção do Vale Selecionado", use_container_width=True, type="primary", key="btn_remover_vale_caixa_admin_v36"):
                                novas_movimentacoes = []
                                for idx_cx, mov_cx in enumerate(st.session_state.movimentacoes_caixa):
                                    foi_deletado = False
                                    for linha_tela in ev_editado:
                                        if linha_tela.get("Dar Baixa / Excluir") and linha_tela.get("ID_Original") == f"CX_{idx_cx}":
                                            foi_deletado = True
                                            break
                                    if not foi_deletado:
                                        novas_movimentacoes.append(mov_cx)
                                
                                st.session_state.movimentacoes_caixa = novas_movimentacoes
                                st.success("🎉 Sucesso! O vale foi removido dos lançamentos e a folha recalculada!")
                                st.rerun()
                    else:
                        st.info(f"💡 Nenhum vale ativo ou cobrança de parcela para {func_selecionado}.")

        # --- TELA DA FOLHA DE PAGAMENTO (F.P) ---
        elif st.session_state.tipo_extrato_ativo == "F.P":
            st.markdown(f"#### 📂 Visualizando: Folha de Pagamento Completa")
            if "funcionarios" in st.session_state and st.session_state.funcionarios:
                if "status_folha_pagamento" not in st.session_state:
                    st.session_state.status_folha_pagamento = {}
                
                linhas_fp = []
                for f in st.session_state.funcionarios:
                    nome_f = f["nome"]
                    tipo_pag = f.get("pagamento", "Fixo")
                    valor_base = float(f.get("valor_hora", 0.0))
                    chave_pix_f = f.get("chave_pix", "Não cadastrada")
                    
                    # --- MOTOR FINANCEIRO INTEGRADO AO BANCO DE DADOS DA DLR ---
                    if tipo_pag == "Fixo":
                        bruto_colaborador = valor_base
                    elif tipo_pag == "Por operação":
                        bruto_colaborador = 0.0
                    elif tipo_pag == "Por hora":
                        horas_relogio = 0.0
                        
                        m_f_c = meses_num.get(mes_sel, "09")
                        chave_periodo_pesquisa = f"{m_f_c}/{ano_sel}"
                        
                        if "banco_horas_permanente" in st.session_state:
                            for reg_h in st.session_state.banco_horas_permanente:
                                if reg_h.get("mes_ano") == chave_periodo_pesquisa:
                                    if str(reg_h.get("nome")).strip().lower() == str(nome_f).strip().lower():
                                        horas_relogio = float(reg_h.get("total_horas", 0.0))
                                        break
                                        
                        bruto_colaborador = horas_relogio * valor_base
                    else:
                        bruto_colaborador = 0.0

                    # --- CONTROLE DE DESCONTOS DE VALES PARCELADOS ---
                    total_descontos_mes = 0.0
                    
                    # 1. Busca vales oficiais registrados na tabela de Adiantamentos (E.V)
                    if "adiantamentos" in st.session_state:
                        for ad in st.session_state.adiantamentos:
                            if str(ad.get("nome")).strip().lower() == str(nome_f).strip().lower() and ad.get("status_vale", "Ativo") != "Cancelado":
                                try:
                                    dt_v = datetime.strptime(ad.get("data", ""), "%d/%m/%Y")
                                    m_origem = dt_v.month; a_origem = dt_v.year
                                except:
                                    m_origem = int(meses_num.get(mes_sel, "09")); a_origem = int(ano_sel)
                                
                                texto_t = ad.get("tipo", "1x")
                                q_parc = 1
                                for x in range(1, 4):
                                    if f"{x}x" in texto_t: q_parc = x; break
                                    
                                m_corrido = m_origem; a_corrido = a_origem; m_cobrancas = []
                                for _ in range(q_parc):
                                    m_cobrancas.append(f"{m_corrido:02d}/{a_corrido}")
                                    m_corrido += 1
                                    if m_corrido > 12: m_corrido = 1; a_corrido += 1
                                    
                                if f"{meses_num.get(mes_sel, '09')}/{ano_sel}" in m_cobrancas:
                                    total_descontos_mes += ad.get("valor_parcela", 0.0)

                    # 2. PONTE AUTOMÁTICA EXIGIDA: Varre o Extrato Geral procurando menções textuais de vales lançados
                    if "movimentacoes_caixa" in st.session_state and st.session_state.movimentacoes_caixa:
                        m_f_c = meses_num.get(mes_sel, "09")
                        mes_tela_num = int(m_f_c)
                        ano_tela_num = int(ano_sel)
                        
                        for mov in st.session_state.movimentacoes_caixa:
                            data_mov = mov.get("Data", "")
                            descricao_mov = str(mov.get("Descrição", "")).strip().lower()
                            
                            # Verifica se o lançamento é um vale ou adiantamento para esta funcionária específica
                            if ("vale" in descricao_mov or "adiantamento" in descricao_mov) and (str(nome_f).lower() in descricao_mov):
                                try:
                                    dt_mov = datetime.strptime(data_mov, "%d/%m/%Y")
                                    mes_origem = dt_mov.month
                                    ano_origem = dt_mov.year
                                except:
                                    mes_origem = mes_tela_num; ano_origem = ano_tela_num
                                
                                # Captura quantas parcelas foram registradas no formulário (ex: 1, 2, 3)
                                try: q_parc_caixa = int(mov.get("Parcelas", mov.get("Quantidade de parcelas", 1)))
                                except: q_parc_caixa = 1
                                
                                v_bruto_caixa = float(mov.get("Valor Total", 0.0))
                                v_parcela_caixa = v_bruto_caixa / q_parc_caixa
                                
                                # MOTOR CRONOLÓGICO: Gera os meses em que esse vale do Financeiro Geral deve cobrar
                                m_cobrancas_caixa = []
                                m_corrido = mes_origem; a_corrido = ano_origem
                                for _ in range(q_parc_caixa):
                                    m_cobrancas_caixa.append(f"{m_corrido:02d}/{a_corrido}")
                                    m_corrido += 1
                                    if m_corrido > 12: m_corrido = 1; a_corrido += 1
                                
                                # Se o mês que o chefe está olhando na tela for um dos meses de cobrança da parcela
                                chave_mes_atual_tela = f"{mes_tela_num:02d}/{ano_tela_num}"
                                if chave_mes_atual_tela in m_cobrancas_caixa:
                                    # Desconta apenas o valor da parcela fracionada!
                                    total_descontos_mes += v_parcela_caixa
                    
                    liquido_a_receber = max(0.0, bruto_colaborador - total_descontos_mes)
                    texto_desconto = f"-R$ {total_descontos_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if total_descontos_mes > 0 else ""
                    chave_status = f"{nome_f}_{mes_sel}_{ano_sel}"
                    
                    # 1. Puxa primeiro o status que o seu super robô trancou na ficha real do funcionário
                    status_ficha_real = f.get("status_pagamento_mes", "Pendente")
                    if status_ficha_real not in ["Pendente", "Pago"]:
                        status_ficha_real = "Pendente"
                        
                    # 2. Mantém a compatibilidade com a gaveta de meses da tela sem resetar o valor
                    if status_ficha_real == "Pago":
                        st.session_state.status_folha_pagamento[chave_status] = "Pago"
                    elif chave_status not in st.session_state.status_folha_pagamento: 
                        st.session_state.status_folha_pagamento[chave_status] = "Pendente"
                    
                    linhas_fp.append({
                        "Funcionário": nome_f,
                        "Chave PIX": chave_pix_f, 
                        "Desconto de Vale": texto_desconto,
                        "Valor a receber": liquido_a_receber,
                        "Status": st.session_state.status_folha_pagamento[chave_status]
                    })
                
                # --- SOLUÇÃO DO COMPORTAMENTO VAZIO: RENDERIZADOR DA PLANILHA ---
                if linhas_fp:
                    folha_editada = st.data_editor(
                        linhas_fp,
                        column_config={
                            "Funcionário": st.column_config.TextColumn("Funcionário", disabled=True),
                            "Chave PIX": st.column_config.TextColumn("🔑 Chave PIX", disabled=True),
                            "Desconto de Vale": st.column_config.TextColumn("Desconto de Vale", disabled=True),
                            "Valor a receber": st.column_config.NumberColumn("Valor a receber", format="R$ %.2f", disabled=True),
                            "Status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Pago"], required=True)
                        },
                        hide_index=True, use_container_width=True, key=f"editor_folha_admin_v30_{mes_sel}_{ano_sel}"
                    )
                    for item in folha_editada: 
                        st.session_state.status_folha_pagamento[f"{item['Funcionário']}_{mes_sel}_{ano_sel}"] = item["Status"]
            else: 
                st.warning("⚠️ Nenhum funcionário localizado na base permanente do banco de dados.")
                    

    # 3. CONFERENTE: PROGRESSO DE LOTES
    elif st.session_state.pagina_admin_atual == "📋 Lotes em Andamento":
        st.subheader("📋 Painel de Monitoramento — Lotes em Andamento")
        
        # Filtros de Mês e Ano adicionados no topo do Admin para gerenciar o período de auditoria
        col_m_prod_a, col_a_prod_a, col_espaco_prod_a = st.columns(3)
        with col_m_prod_a:
            mes_prod_sel = st.selectbox("Filtrar por Mês:", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=8, key="filtro_mes_esteira_ap_admin_v25")
        with col_a_prod_a:
            ano_prod_sel = st.selectbox("Filtrar por Ano:", ["2026", "2027", "2028", "2029", "2030"], index=0, key="filtro_ano_esteira_ap_admin_v25")
            
        st.markdown("<br>", unsafe_allow_html=True)

        if "lotes_gerais" in st.session_state and st.session_state.lotes_gerais:
            # --- MOTOR DE CÁLCULO DOS 4 CARDS NO ADMIN ---
            qtd_pendentes = 0
            qtd_em_producao = 0
            qtd_vencidos = 0
            qtd_concluidos = 0
            data_hoje_dt = datetime.now().date()
            
            meses_num = {"Janeiro":"01", "Fevereiro":"02", "Março":"03", "Abril":"04", "Maio":"05", "Junho":"06", "Julho":"07", "Agosto":"08", "Setembro":"09", "Outubro":"10", "Novembro":"11", "Dezembro":"12"}
            mes_procurado = meses_num[mes_prod_sel]
            chave_mes_ano_filtro = f"/{mes_procurado}/{ano_prod_sel}"
            
            for item in st.session_state.lotes_gerais:
                data_cad_str = item.get("data_cadastro", datetime.now().strftime("%d/%m/%Y"))
                data_ent_str = item.get("data_entrega", "")
                status_atual = item.get("status", "Pendente")
                
                # Regra idêntica de rolagem viva para contagem precisa dos cards do chefe
                if (chave_mes_ano_filtro in data_cad_str) or (status_atual in ["Pendente", "Em produção", "Em production"]):
                    try: data_entrega_dt = datetime.strptime(data_ent_str, "%d/%m/%Y").date()
                    except: data_entrega_dt = None
                    
                    if status_atual == "Pendente":
                        qtd_pendentes += 1
                    elif status_atual in ["Em produção", "Em production"]:
                        qtd_em_producao += 1
                    elif status_atual == "Concluído":
                        qtd_concluidos += 1
                        
                    if data_entrega_dt and status_atual != "Concluído" and data_hoje_dt > data_entrega_dt:
                        qtd_vencidos += 1

            # --- DESENHO DOS 4 CARDS COLORIDOS HORIZONTAIS NO ADMIN ---
            card_a1, card_a2, card_a3, card_a4 = st.columns(4)
            with card_a1:
                st.markdown(f"<div style='background-color: #EF6C00; padding: 15px; border-radius: 8px; color: white; text-align: center;'><b>Lotes Pendentes</b><br><h2>{qtd_pendentes}</h2></div>", unsafe_allow_html=True)
            with card_a2:
                st.markdown(f"<div style='background-color: #2E7D32; padding: 15px; border-radius: 8px; color: white; text-align: center;'><b>Em Produção</b><br><h2>{qtd_em_producao}</h2></div>", unsafe_allow_html=True)
            with card_a3:
                st.markdown(f"<div style='background-color: #C62828; padding: 15px; border-radius: 8px; color: white; text-align: center;'><b>Lotes Vencidos</b><br><h2>{qtd_vencidos}</h2></div>", unsafe_allow_html=True)
            with card_a4:
                st.markdown(f"<div style='background-color: #1565C0; padding: 15px; border-radius: 8px; color: white; text-align: center;'><b>Concluídos</b><br><h2>{qtd_concluidos}</h2></div>", unsafe_allow_html=True)
                
            st.markdown("<br><hr>", unsafe_allow_html=True)
            st.info("🔒 **Espelho de Auditoria:** Visão geral da esteira ativa em tempo real. Edições bloqueadas para o perfil Administrador.")

            linhas_tabela_ap = []
            for index, item in enumerate(st.session_state.lotes_gerais):
                    data_cad_str = item.get("data_cadastro", datetime.now().strftime("%d/%m/%Y"))
                    data_ini_str = item.get("data_inicio_producao", "")
                    data_ent_str = item.get("data_entrega", "")
                    status_atual = item.get("status", "Pendente")
                    prioridade_atual = item.get("prioridade", "Não")
                    
                    pertence_ao_mes_do_filtro = (chave_mes_ano_filtro in data_cad_str)
                    ativo_para_rolagem = (status_atual in ["Pendente", "Em produção", "Em production"])
                    
                    if pertence_ao_mes_do_filtro or ativo_para_rolagem:
                        try: data_chegada_dt = datetime.strptime(data_cad_str, "%d/%m/%Y").date()
                        except: data_chegada_dt = data_hoje_dt
                        
                        try: data_entrega_dt = datetime.strptime(data_ent_str, "%d/%m/%Y").date()
                        except: data_entrega_dt = None
                        
                        if status_atual == "Pendente":
                            dias_pendencia = (data_hoje_dt - data_chegada_dt).days; dias_producao = 0
                        elif status_atual in ["Em production", "Em produção"]:
                            try: data_inicio_dt = datetime.strptime(data_ini_str, "%d/%m/%Y").date()
                            except: data_inicio_dt = data_hoje_dt
                            dias_pendencia = (data_inicio_dt - data_chegada_dt).days
                            dias_producao = (data_hoje_dt - data_inicio_dt).days
                        else:
                            dias_pendencia = 0; dias_producao = 0
                            
                        if dias_pendencia < 0: dias_pendencia = 0
                        if dias_producao < 0: dias_producao = 0
                        
                        if status_atual == "Concluído":
                            sinalizacao_final = "🔵"
                        else:
                            if data_entrega_dt and data_hoje_dt > data_entrega_dt: bolinha_status = "🔴"
                            elif status_atual == "Pendente": bolinha_status = "🟠"
                            else: bolinha_status = "🟢"
                                
                            if prioridade_atual == "Sim": sinalizacao_final = f"{bolinha_status} {bolinha_status}"
                            else: sinalizacao_final = bolinha_status
                        
                        linhas_tabela_ap.append({
                            "🚨 Alerta": sinalizacao_final,
                            "Nome do fornecedor / Marca": item.get("fornecedor", ""),
                            "Número da O.F (Ordem de Fabricação)": item.get("of", ""),
                            "Referência do Modelo (Peça)": item.get("referencia", ""),
                            "Quantidade Total de Peças na Nota": item.get("qtd_prevista", 0),
                            "Dias em pendência": int(dias_pendencia), "Dias em produção": int(dias_producao),
                            "Data chegada": data_cad_str, "Data para entrega": data_ent_str,
                            "Preço Unitário": item.get("preco", 0.0), 
                            "Status": status_atual,
                            # AS DUAS NOVAS COLUNAS INTEGRADAS NO SEU PAINEL CHEFE:
                            "Porcentagem já produzido": f"{item.get('porcentagem_pronta', 0)}%",
                            "✅ Peças Prontas Reais": int(item.get("qtd_pronta", 0)),
                            "prioridade": item.get("prioridade", "Não")
                        })
                        
            # Desenha a planilha do Administrador 100% TRAVADA para auditoria segura
            if linhas_tabela_ap:
                st.data_editor(
                    linhas_tabela_ap,
                    column_config={
                        "🚨 Alerta": st.column_config.TextColumn("🚨 Alerta", disabled=True),
                        "Nome do fornecedor / Marca": st.column_config.TextColumn("Nome do fornecedor / Marca", disabled=True),
                        "Número da O.F (Ordem de Fabricação)": st.column_config.TextColumn("Número da O.F (Ordem de Fabricação)", disabled=True),
                        "Referência do Modelo (Peça)": st.column_config.TextColumn("Referência do Modelo (Peça)", disabled=True),
                        "Quantidade Total de Peças na Nota": st.column_config.NumberColumn("Quantidade Total de Peças na Nota", disabled=True),
                        "Dias em pendência": st.column_config.NumberColumn("Dias em pendência", disabled=True),
                        "Dias em produção": st.column_config.NumberColumn("Dias em produção", disabled=True),
                        "Data chegada": st.column_config.TextColumn("Data chegada", disabled=True),
                        "Data para entrega": st.column_config.TextColumn("Data para entrega", disabled=True),
                        "Preço Unitário": st.column_config.NumberColumn("Preço Unitário", format="R$ %.2f", disabled=True),
                        "Status": st.column_config.TextColumn("Status", disabled=True),
                        # AS DUAS COLUNAS EXIBIDAS LADO A LADO EM MODO AUDITORIA NO SEU ESCRITÓRIO:
                        "Porcentagem já produzido": st.column_config.TextColumn("Porcentagem já produzido", disabled=True),
                        "✅ Peças Prontas Reais": st.column_config.NumberColumn("✅ Peças Prontas Reais", format="%d", disabled=True),
                        "prioridade": st.column_config.TextColumn("prioridade", disabled=True)
                    },
                    hide_index=True, use_container_width=True, key=f"tab_ap_admin_auditoria_faturamento_v27_{mes_prod_sel}_{ano_prod_sel}"
                )
            else: 
                st.info("💡 Nenhum lote em andamento ou ativo encontrado para o filtro selecionado.")
        else: 
            st.info("💡 Nenhum lote de produção cadastrado no sistema no momento.")

    
                
                                   
    # --- LÓGICA DA ÁREA 2: CONFERENTE / FINANCEIRO ---
elif st.session_state.perfil_atual == "conferente":
    import pandas as pd
    
    if "pagina_conf_atual" not in st.session_state or st.session_state.pagina_conf_atual in ["🔍 Extrato Individual", "📅 Presença Diária"]:
        st.session_state.pagina_conf_atual = "💰 Financeiro Geral"
        
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🗂️ Menu do Conferente")
        
        paginas_conf = {
            "💰 Financeiro Geral": "💰 Financeiro Geral",   
            "📅 Extrato do Mês": "📅 Extrato do Mês",       
            "📈 Progresso de Lotes": "📈 Progresso de Lotes",
            "📥 Importar Ponto": "📥 Importar Ponto"
        }
        
        for label, pagina_id in paginas_conf.items():
            if st.session_state.pagina_conf_atual == pagina_id:
                st.markdown(f"""
                    <div style='background-color: #FFFFFF; color: #000000; padding: 10px 15px; border-radius: 6px; font-weight: bold; text-align: center; border: 2px solid #4A154B; margin-bottom: 8px;'>
                        {label}
                    </div>
                """, unsafe_allow_html=True)
            else:
                if st.button(label, use_container_width=True, key=f"btn_conf_sinc_real_{pagina_id}"):
                    st.session_state.pagina_conf_atual = pagina_id
                    st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🚪 Sair do Sistema", use_container_width=True, type="secondary", key="btn_sair_conf_sinc_real"):
            st.session_state.logado = False
            st.session_state.perfil_atual = None
            st.rerun()

    # --- SUB-PÁGINA 1: FINANCEIRO GERAL COMPARTILHADO (ATUALIZADO E SEGURO) ---
    if st.session_state.pagina_conf_atual == "💰 Financeiro Geral":
        st.subheader("💰 Fluxo de Caixa Dinâmico — Entradas e Saídas")
        
        tipo_mov = st.selectbox(
            "Tipo de Movimentação", 
            ["Saída", "Entrada", "Saída (Vale de Funcionário)"], 
            key="conf_tipo_mov_sinc_real_v33"
        )
        
        # Inicializa as variáveis de controle de fluxo e reset específicas da Conferência
        if "versao_form_caixa_conf" not in st.session_state:
            st.session_state.versao_form_caixa_conf = 0
        if "clicou_registrar_fc_conf" not in st.session_state:
            st.session_state.clicou_registrar_fc_conf = False
            
        chave_reset_fc = st.session_state.versao_form_caixa_conf

        # --- CAMPOS DINÂMICOS LIVRES DE ALTA PERFORMANCE ---
        if tipo_mov == "Saída (Vale de Funcionário)":
            todos_funcs = [f["nome"] for f in st.session_state.get("funcionarios", [])]
            if not todos_funcs:
                st.warning("⚠️ Cadastre primeiro um funcionário na aba 'Cadastrar Funcionário'.")
                func_vale = "Nenhum cadastrado"
            else:
                func_vale = st.selectbox("Selecione o Funcionário que pediu o Vale", todos_funcs, key=f"fc_func_conf_{chave_reset_fc}")
            
            valor_mov = st.number_input("Valor do Vale (R$)", min_value=0.0, format="%.2f", step=10.0, key=f"fc_val_vale_conf_{chave_reset_fc}")
            parcelas = st.selectbox("Parcelar em quantas vezes? (Limite de 3x para Vales)", [1, 2, 3], index=0, key=f"fc_parc_vale_conf_{chave_reset_fc}")
            descricao_mov = f"Vale para {func_vale}"
        else:
            func_vale = None
            descricao_mov = st.text_input("Descrição / Motivo da Movimentação (Linha, Luz, Combustível, etc.)", key=f"fc_desc_geral_conf_{chave_reset_fc}")
            valor_mov = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f", step=50.0, key=f"fc_val_geral_conf_{chave_reset_fc}")
            
            lista_opcoes_parcelas = list(range(1, 13))
            parcelas = st.selectbox("Quantidade de parcelas (Se houver)", options=lista_opcoes_parcelas, index=0, key=f"fc_parc_geral_conf_{chave_reset_fc}")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BOTÃO CLÁSSICO DE DISPARO INICIAL (FIXO NO LOCAL QUE VOCÊ CIRCULOU) ---
        if not st.session_state.clicou_registrar_fc_conf:
            if st.button("💾 Registrar no Caixa", use_container_width=True, key=f"btn_disparo_conf_fc_{chave_reset_fc}"):
                if valor_mov <= 0:
                    st.error("❌ Por favor, digite um valor maior que R$ 0,00.")
                elif tipo_mov != "Saída (Vale de Funcionário)" and not descricao_mov.strip():
                    st.error("❌ Por favor, preencha a descrição do motivo desta movimentação.")
                else:
                    st.session_state.clicou_registrar_fc_conf = True
                    st.rerun()

        # --- CONTROLADOR DO AVISO AMARELO DE CONFIRMAÇÃO ---
        if st.session_state.clicou_registrar_fc_conf:
            st.warning(f"⚠️ **Aviso de Alteração de Caixa:** Tem certeza que deseja salvar o lançamento de **R$ {valor_mov:.2f}** como **{tipo_mov}**?")
            
            col_salvar_fc, col_cancelar_fc = st.columns(2)
            
            with col_salvar_fc:
                if st.button("✅ Sim, confirmar e salvar", use_container_width=True, type="primary", key="btn_conf_caixa_conf_v33"):
                    data_hoje = datetime.now().strftime("%d/%m/%Y")
                    
                    if "movimentacoes_caixa" not in st.session_state:
                        st.session_state.movimentacoes_caixa = []
                        
                    # Grava na gaveta de movimentações
                    st.session_state.movimentacoes_caixa.append({
                        "Data": data_hoje, 
                        "Tipo": "Saída" if "Saída" in tipo_mov else "Entrada", 
                        "Detalhe / Categoria": "Vale de Funcionário" if "Vale" in tipo_mov else "Geral", 
                        "Descrição": descricao_mov, 
                        "Valor Total": valor_mov, 
                        "Parcelas": parcelas
                    })
                    
                    # Se for vale, joga na gaveta de adiantamentos
                    if tipo_mov == "Saída (Vale de Funcionário)":
                        tipo_registro = f"Adiantamento Parcelado de {parcelas}x" if parcelas > 1 else "Adiantamento Parcelado de 1x"
                        if "adiantamentos" not in st.session_state:
                            st.session_state.adiantamentos = []
                        st.session_state.adiantamentos.append({
                            "nome": func_vale, 
                            "valor_bruto": valor_mov, 
                            "valor_parcela": valor_mov / parcelas, 
                            "tipo": tipo_registro, 
                            "data": data_hoje, 
                            "status_vale": "Ativo"
                        })
                        
                    # ORDEM DO ROBÔ: Salva direto no arquivo físico .db do HD na mesma hora
                    super_robo_trancar_memoria_para_hd()
                    
                    # Reseta o formulário limpando os campos
                    st.session_state.clicou_registrar_fc_conf = False
                    st.session_state.versao_form_caixa_conf += 1
                    
                    st.success(f"🎉 Sucesso! {tipo_mov} de R$ {valor_mov:.2f} gravado com segurança absoluta no HD!")
                    st.rerun()
                    
            with col_cancelar_fc:
                if st.button("❌ Não, cancelar", use_container_width=True, key="btn_cancela_caixa_conf_v33"):
                    st.session_state.clicou_registrar_fc_conf = False
                    st.rerun()
                    # SUB-PÁGINA 2 COMPARTILHADA: EXTRATO DO MÊS (FILTROS E BOTÕES)
    elif st.session_state.pagina_conf_atual == "📅 Extrato do Mês":
        st.subheader("📅 Livro Caixa — Extrato de Todas as Movimentações")
        
        # SINCRONIZAÇÃO DE DIRETRIZ: Filtros usando exatamente as mesmas chaves do Admin
        col_mes, col_ano, col_vazia = st.columns(3)
        with col_mes:
            mes_sel = st.selectbox("Selecionar Mês:", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=8, key="conf_selectbox_mes_global")
        with col_ano:
            ano_sel = st.selectbox("Selecionar Ano:", ["2026", "2027", "2028", "2029", "2030"], index=0, key="conf_selectbox_ano_global")
            
        st.write(f"Exibindo movimentações cronológicas referentes a: **{mes_sel} de {ano_sel}**")
        
        if "tipo_extrato_ativo" not in st.session_state:
            st.session_state.tipo_extrato_ativo = "E.G"

        # Seção dos três botões alinhados com CSS idêntico ao Admin
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2, col_btn3, col_espaco = st.columns(4)
        
        with col_btn1:
            if st.session_state.tipo_extrato_ativo == "E.G":
                st.markdown("<style>button[key='conf_btn_ext_geral'] { background-color: #FFFFFF !important; color: #000000 !important; font-weight: bold !important; border: 2px solid #4A154B !important; }</style>", unsafe_allow_html=True)
            if st.button("📊 Extrato Geral (E.G)", use_container_width=True, key="conf_btn_ext_geral"):
                st.session_state.tipo_extrato_ativo = "E.G"
                st.rerun()
                
        with col_btn2:
            if st.session_state.tipo_extrato_ativo == "E.V":
                st.markdown("<style>button[key='conf_btn_ext_vale'] { background-color: #FFFFFF !important; color: #000000 !important; font-weight: bold !important; border: 2px solid #4A154B !important; }</style>", unsafe_allow_html=True)
            if st.button("💸 Extrato de Vale (E.V)", use_container_width=True, key="conf_btn_ext_vale"):
                st.session_state.tipo_extrato_ativo = "E.V"
                st.rerun()

        with col_btn3:
            if st.session_state.tipo_extrato_ativo == "F.P":
                st.markdown("<style>button[key='conf_btn_folha_pag'] { background-color: #FFFFFF !important; color: #000000 !important; font-weight: bold !important; border: 2px solid #4A154B !important; }</style>", unsafe_allow_html=True)
            if st.button("📝 Folha de Pag. (F.P)", use_container_width=True, key="conf_btn_folha_pag"):
                st.session_state.tipo_extrato_ativo = "F.P"
                st.rerun()

        st.markdown("---")
        meses_num = {"Janeiro":"01", "Fevereiro":"02", "Março":"03", "Abril":"04", "Maio":"05", "Junho":"06", "Julho":"07", "Agosto":"08", "Setembro":"09", "Outubro":"10", "Novembro":"11", "Dezembro":"12"}
        mes_procurado = meses_num[mes_sel]
        # --- TELA DO EXTRATO GERAL (E.G) ---
        if st.session_state.tipo_extrato_ativo == "E.G":
            st.markdown(f"#### 📂 Visualizando: Extrato Geral ({mes_sel}/{ano_sel})")
            if "movimentacoes_caixa" in st.session_state and st.session_state.movimentacoes_caixa:
                linhas_tabela_eg = []
                saldo_acumulado = 0.0
                for mov in st.session_state.movimentacoes_caixa:
                    data_mov = mov.get("Data", "")
                    if f"/{mes_procurado}/{ano_sel}" in data_mov or data_mov == "":
                        v_total = mov.get("Valor Total", 0.0)
                        tipo_m = mov.get("Tipo", "Saída")
                        valor_final = -v_total if tipo_m == "Saída" else v_total
                        saldo_acumulado += valor_final
                        linhas_tabela_eg.append({"Data": data_mov, "Descrição": mov.get("Descrição", ""), "Valor": valor_final})
                
                if linhas_tabela_eg:
                    linhas_tabela_eg.append({"Data": "", "Descrição": "📊 SALDO TOTAL DO CAIXA", "Valor": saldo_acumulado})
                    st.dataframe(linhas_tabela_eg, column_config={"Data": st.column_config.TextColumn("Data", width="small"), "Descrição": st.column_config.TextColumn("Descrição"), "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")}, hide_index=True, use_container_width=True)
                    if saldo_acumulado < 0:
                        st.error(f"🔴 Caixa Negativo: Saldo em **R$ {saldo_acumulado:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
                    else:
                        st.success(f"🟢 Caixa Positivo: Saldo em **R$ {saldo_acumulado:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
                else:
                    st.info(f"💡 Nenhuma movimentação em {mes_sel}/{ano_sel}.")
            else:
                st.info("💡 Nenhuma movimentação geral registrada.")

        # --- TELA DO EXTRATO DE VALE (E.V) ---
        elif st.session_state.tipo_extrato_ativo == "E.V":
            # --- CAPTURA DE DATA INTELIGENTE E UNIFICADA PARA A CONFERÊNCIA ---
            v_mes_tela = mes_sel if 'mes_sel' in locals() else st.session_state.get("filtro_mes_esteira_ap_admin_v25", st.session_state.get("dash_ref_mes_v30", "Setembro"))
            v_ano_tela = ano_sel if 'ano_sel' in locals() else st.session_state.get("filtro_ano_esteira_ap_admin_v25", st.session_state.get("dash_ref_ano_v30", "2026"))
            
            st.markdown(f"#### 📂 Visualizando: Controle Individual de Vales e Histórico ({v_mes_tela}/{v_ano_tela})")
            
            todos_funcs = [f["nome"] for f in st.session_state.funcionarios] if "funcionarios" in st.session_state else []
            
            if not todos_funcs:
                st.warning("⚠️ Cadastre funcionários no sistema para liberar laudos de históricos.")
            else:
                # Modificado a key para o Conferente ter seu próprio seletor sem travar o do Admin
                func_selecionado = st.selectbox("Pesquisar Funcionário:", ["Escolha um funcionário..."] + todos_funcs, key="busca_hist_vales_conferente_v33")
                
                if func_selecionado != "Escolha um funcionário...":
                    linhas_tabela_ev = []
                    desconto_do_mes_selecionado = 0.0
                    
                    m_f_c = meses_num.get(v_mes_tela, "09")
                    mes_tela_num = int(m_f_c)
                    ano_tela_num = int(v_ano_tela)
                    chave_tela_atual = f"{mes_tela_num:02d}/{ano_tela_num}"

                    # 1. VARREDURA 1: Coleta vales registrados na tabela de Adiantamentos (E.V)
                    if "adiantamentos" in st.session_state:
                        for index, ad in enumerate(st.session_state.adiantamentos):
                            if str(ad.get("nome")).strip().lower() == str(func_selecionado).strip().lower() and ad.get("status_vale", "Ativo") != "Cancelado":
                                data_ad = ad.get("data", "")
                                v_bruto = float(ad.get("valor_bruto", 0.0))
                                v_parcela = float(ad.get("valor_parcela", v_bruto))
                                
                                try: dt_v = datetime.strptime(data_ad, "%d/%m/%Y"); m_orig = dt_v.month; a_orig = dt_v.year
                                except: m_orig = mes_tela_num; a_orig = ano_tela_num
                                
                                texto_t = ad.get("tipo", "1x")
                                q_parc = 1
                                for x in range(1, 4):
                                    if f"{x}x" in texto_t: q_parc = x; break
                                    
                                m_cobrancas = []
                                m_corrido = m_orig; a_corrido = a_orig
                                for _ in range(q_parc):
                                    m_cobrancas.append(f"{m_corrido:02d}/{a_corrido}")
                                    m_corrido += 1
                                    if m_corrido > 12: m_corrido = 1; a_corrido += 1
                                    
                                if chave_tela_atual in m_cobrancas:
                                    num_parcela_atual = m_cobrancas.index(chave_tela_atual) + 1
                                    desconto_do_mes_selecionado += v_parcela
                                    linhas_tabela_ev.append({
                                        "Data Lançamento": data_ad,
                                        "Origem / Descrição": f"Vale Parcelado ({num_parcela_atual}/{q_parc})",
                                        "Valor Total Emprestado": v_bruto,
                                        "Valor Parcela deste Mês": v_parcela,
                                        "Status": f"Ativo ({num_parcela_atual}/{q_parc})"
                                    })

                    # 2. VARREDURA 2: Coleta vales registrados no Fluxo de Caixa Dinâmico (Financeiro Geral)
                    if "movimentacoes_caixa" in st.session_state and st.session_state.movimentacoes_caixa:
                        for index, mov in enumerate(st.session_state.movimentacoes_caixa):
                            data_mov = mov.get("Data", "")
                            descricao_mov = str(mov.get("Descrição", "")).strip().lower()
                            
                            if ("vale" in descricao_mov or "adiantamento" in descricao_mov) and (str(func_selecionado).lower() in descricao_mov):
                                try: dt_m = datetime.strptime(data_mov, "%d/%m/%Y"); m_orig = dt_m.month; a_orig = dt_m.year
                                except: m_orig = mes_tela_num; a_orig = ano_tela_num
                                
                                try: q_parc_caixa = int(mov.get("Parcelas", mov.get("Quantidade de parcelas", 1)))
                                except: q_parc_caixa = 1
                                
                                v_bruto_caixa = float(mov.get("Valor Total", 0.0))
                                v_parcela_caixa = v_bruto_caixa / q_parc_caixa
                                
                                m_cobrancas_caixa = []
                                m_corrido = m_orig; a_corrido = a_orig
                                for _ in range(q_parc_caixa):
                                    m_cobrancas_caixa.append(f"{m_corrido:02d}/{a_corrido}")
                                    m_corrido += 1
                                    if m_corrido > 12: m_corrido = 1; a_corrido += 1
                                    
                                if chave_tela_atual in m_cobrancas_caixa:
                                    num_parcela_atual = m_cobrancas_caixa.index(chave_tela_atual) + 1
                                    desconto_do_mes_selecionado += v_parcela_caixa
                                    linhas_tabela_ev.append({
                                        "Data Lançamento": data_mov,
                                        "Origem / Descrição": f"Fluxo de Caixa — Vale ({num_parcela_atual}/{q_parc_caixa})",
                                        "Valor Total Emprestado": v_bruto_caixa,
                                        "Valor Parcela deste Mês": v_parcela_caixa,
                                        "Status": f"Ativo ({num_parcela_atual}/{q_parc_caixa})"
                                    })
                    
                    # --- DESENHO DA TELA ATUALIZADA NA CONFERÊNCIA ---
                    st.markdown(f"### 📋 Histórico de Vales: **{func_selecionado}**")
                    
                    desc_mes_br = f"{desconto_do_mes_selecionado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    st.markdown(f"<div style='background-color: #B71C1C; padding: 12px; border-radius: 6px; color: white; text-align: center; max-width: 400px; margin-bottom: 20px;'><b>Desconto Ativo em {v_mes_tela}/{v_ano_tela}</b><br><h3>R$ {desc_mes_br}</h3></div>", unsafe_allow_html=True)
                    
                    if linhas_tabela_ev:
                        # DESENHO DA PLANILHA ORIGINAL COM A COLUNA DE EXCLUSÃO ATIVADA
                        ev_editado_conf = st.data_editor(
                            linhas_tabela_ev,
                            column_config={
                                "ID_Original": None, # Mantém o ID oculto em silêncio
                                "Data Lançamento": st.column_config.TextColumn("📅 Data Lançamento", disabled=True),
                                "Origem / Descrição": st.column_config.TextColumn("📝 Origem / Descrição", disabled=True),
                                "Valor Total Emprestado": st.column_config.NumberColumn("💰 Total Emprestado", format="R$ %.2f", disabled=True),
                                "Valor Parcela deste Mês": st.column_config.NumberColumn("📉 Parcela do Mês", format="R$ %.2f", disabled=True),
                                "Status": st.column_config.TextColumn("📌 Status", disabled=True),
                                "Dar Baixa / Excluir": st.column_config.CheckboxColumn("🗑️ Dar Baixa / Excluir") # INJETA A COLUNA QUE FALTAVA!
                            },
                            hide_index=True, use_container_width=True, key=f"tab_ev_individual_conf_v36_{func_selecionado}"
                        )
                        
                        # VERIFICAÇÃO DE EXCLUSÃO BLINDADA
                        algum_vale_marcado_conf = any(linha.get("Dar Baixa / Excluir", False) for linha in ev_editado_conf)
                        
                        if algum_vale_marcado_conf:
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.warning(f"⚠️ **Confirmação de Baixa:** Deseja remover permanentemente o(s) vale(s) selecionado(s) de {func_selecionado}?")
                            
                            if st.button("🗑️ Confirmar Remoção do Vale Selecionado", use_container_width=True, type="primary", key="btn_remover_vale_caixa_conf_v36"):
                                novas_movimentacoes = []
                                for idx_cx, mov_cx in enumerate(st.session_state.movimentacoes_caixa):
                                    foi_deletado = False
                                    for linha_tela in ev_editado_conf:
                                        if linha_tela.get("Dar Baixa / Excluir") and linha_tela.get("ID_Original") == f"CX_{idx_cx}":
                                            foi_deletado = True
                                            break
                                    if not foi_deletado:
                                        novas_movimentacoes.append(mov_cx)
                                
                                st.session_state.movimentacoes_caixa = novas_movimentacoes
                                st.success("🎉 Sucesso! O vale foi removido dos lançamentos e a folha recalculada!")
                                st.rerun()
                    else:
                        st.info(f"💡 Nenhum vale ativo ou cobrança de parcela para {func_selecionado}.")
                        # --- TELA DA FOLHA DE PAGAMENTO (F.P) ---
        elif st.session_state.tipo_extrato_ativo == "F.P":
            st.markdown(f"#### 📂 Visualizando: Folha de Pagamento Completa")
            if "funcionarios" in st.session_state:
                if "status_folha_pagamento" not in st.session_state:
                    st.session_state.status_folha_pagamento = {}
                
                # Certifica que a gaveta do ponto existe para não dar erro de leitura
                if "presencas_ponto" not in st.session_state:
                    st.session_state.presencas_ponto = {}
                
                linhas_fp = []
                for f in st.session_state.funcionarios:
                    nome_f = f["nome"]
                    nome_f_chave = nome_f.strip().title() # Alinha com o padrão de leitura do relógio
                    tipo_pag = f.get("pagamento", "Fixo")
                    valor_base = float(f.get("valor_hora", 0.0))
                    chave_pix_f = f.get("chave_pix", "Não cadastrada")
                    
                    # --- REQUISITO OPERACIONAL EXIGIDO: CALCULO CRONOLÓGICO DO FA05H ---
                    if tipo_pag == "Fixo":
                        # REGRA 1: Pagamento fixo entra com o salário bruto cadastrado
                        bruto_colaborador = valor_base
                    elif tipo_pag == "Por operação":
                        # REGRA 2: Pagamento por operação (peça) fica zerado na folha interna
                        bruto_colaborador = 0.0
                    elif tipo_pag == "Por hora":
                        horas_relogio = 0.0
                        
                        # Captura as variáveis de data de forma dinâmica
                        v_mes_tela = mes_sel if 'mes_sel' in locals() else (mes_prod_sel if 'mes_prod_sel' in locals() else "Setembro")
                        v_ano_tela = ano_sel if 'ano_sel' in locals() else (ano_prod_sel if 'ano_prod_sel' in locals() else "2026")
                        
                        m_f_c = meses_num.get(v_mes_tela, "09")
                        chave_periodo_pesquisa = f"{m_f_c}/{v_ano_tela}"
                        
                        # BARREIRA DE PROTEÇÃO ÚNICA: Varre o DB comparando em letras minúsculas
                        if "banco_horas_permanente" in st.session_state:
                            for reg_h in st.session_state.banco_horas_permanente:
                                if reg_h.get("mes_ano") == chave_periodo_pesquisa:
                                    if str(reg_h.get("nome")).strip().lower() == str(nome_f).strip().lower():
                                        horas_relogio = float(reg_h.get("total_horas", 0.0))
                                        break
                                        
                        bruto_colaborador = horas_relogio * valor_base
                    
                    
                    # Motor de parcelas de vales integrado para dedução precisa no mês
                    total_descontos_mes = 0.0
                    
                    # 1. Busca vales oficiais registrados na tabela de Adiantamentos (E.V)
                    if "adiantamentos" in st.session_state:
                        for ad in st.session_state.adiantamentos:
                            if str(ad.get("nome")).strip().lower() == str(nome_f).strip().lower() and ad.get("status_vale", "Ativo") != "Cancelado":
                                try:
                                    dt_v = datetime.strptime(ad.get("data", ""), "%d/%m/%Y")
                                    m_origem = dt_v.month; a_origem = dt_v.year
                                except:
                                    m_origem = int(meses_num.get(mes_sel, "09")); a_origem = int(ano_sel)
                                
                                texto_t = ad.get("tipo", "1x")
                                q_parc = 1
                                for x in range(1, 4):
                                    if f"{x}x" in texto_t: q_parc = x; break
                                    
                                m_corrido = m_origem; a_corrido = a_origem; m_cobrancas = []
                                for _ in range(q_parc):
                                    m_cobrancas.append(f"{m_corrido:02d}/{a_corrido}")
                                    m_corrido += 1
                                    if m_corrido > 12: m_corrido = 1; a_corrido += 1
                                    
                                if f"{meses_num.get(mes_sel, '09')}/{ano_sel}" in m_cobrancas:
                                    total_descontos_mes += ad.get("valor_parcela", 0.0)

                    # 2. PONTE AUTOMÁTICA EXIGIDA: Varre o Extrato Geral procurando menções textuais de vales lançados
                    if "movimentacoes_caixa" in st.session_state and st.session_state.movimentacoes_caixa:
                        m_f_c = meses_num.get(mes_sel, "09")
                        mes_tela_num = int(m_f_c)
                        ano_tela_num = int(ano_sel)
                        
                        for mov in st.session_state.movimentacoes_caixa:
                            data_mov = mov.get("Data", "")
                            descricao_mov = str(mov.get("Descrição", "")).strip().lower()
                            
                            # Verifica se o lançamento é um vale ou adiantamento para esta funcionária específica
                            if ("vale" in descricao_mov or "adiantamento" in descricao_mov) and (str(nome_f).lower() in descricao_mov):
                                try:
                                    dt_mov = datetime.strptime(data_mov, "%d/%m/%Y")
                                    mes_origem = dt_mov.month
                                    ano_origem = dt_mov.year
                                except:
                                    mes_origem = mes_tela_num; ano_origem = ano_tela_num
                                
                                # Captura quantas parcelas foram registradas no formulário (ex: 1, 2, 3)
                                try: q_parc_caixa = int(mov.get("Parcelas", mov.get("Quantidade de parcelas", 1)))
                                except: q_parc_caixa = 1
                                
                                v_bruto_caixa = float(mov.get("Valor Total", 0.0))
                                v_parcela_caixa = v_bruto_caixa / q_parc_caixa
                                
                                # MOTOR CRONOLÓGICO: Gera os meses em que esse vale do Financeiro Geral deve cobrar
                                m_cobrancas_caixa = []
                                m_corrido = mes_origem; a_corrido = ano_origem
                                for _ in range(q_parc_caixa):
                                    m_cobrancas_caixa.append(f"{m_corrido:02d}/{a_corrido}")
                                    m_corrido += 1
                                    if m_corrido > 12: m_corrido = 1; a_corrido += 1
                                
                                # Se o mês que o chefe está olhando na tela for um dos meses de cobrança da parcela
                                chave_mes_atual_tela = f"{mes_tela_num:02d}/{ano_tela_num}"
                                if chave_mes_atual_tela in m_cobrancas_caixa:
                                    # Desconta apenas o valor da parcela fracionada!
                                    total_descontos_mes += v_parcela_caixa
                    
                    liquido_a_receber = max(0.0, bruto_colaborador - total_descontos_mes)
                    
                    texto_desconto = f"-R$ {total_descontos_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if total_descontos_mes > 0 else ""
                    chave_status = f"{nome_f}_{mes_sel}_{ano_sel}"
                    if chave_status not in st.session_state.status_folha_pagamento: 
                        st.session_state.status_folha_pagamento[chave_status] = "Pendente"
                    
                    linhas_fp.append({
                        "Funcionário": nome_f,
                        "Chave PIX": chave_pix_f,
                        "Desconto de Vale": texto_desconto,
                        "Valor a receber": liquido_a_receber,
                        "Status": st.session_state.status_folha_pagamento[chave_status]
                    })
                
                # SINCRO REAL: Usa a mesma estrutura de chaves estruturadas e chaves do editor do Admin
                folha_editada = st.data_editor(
                    linhas_fp,
                    column_config={
                        "Funcionário": st.column_config.TextColumn("Funcionário", disabled=True),
                        "Chave PIX": st.column_config.TextColumn("🔑 Chave PIX", disabled=True),
                        "Desconto de Vale": st.column_config.TextColumn("Desconto de Vale", disabled=True),
                        "Valor a receber": st.column_config.NumberColumn("Valor a receber", format="R$ %.2f", disabled=True),
                        "Status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Pago"], required=True)
                    },
                    hide_index=True, 
                    use_container_width=True, 
                    key=f"editor_folha_conf_v18_sinc_{mes_sel}_{ano_sel}"
                )
                for item in folha_editada: 
                    st.session_state.status_folha_pagamento[f"{item['Funcionário']}_{mes_sel}_{ano_sel}"] = item["Status"]
            else: 
                st.warning("⚠️ Nenhum funcionário cadastrado no sistema.")

    # 3. CONFERENTE: PROGRESSO DE LOTES GERAIS
    elif st.session_state.pagina_conf_atual == "📈 Progresso de Lotes":
        st.subheader("📈 Controle de Qualidade — Andamento e Conclusão de Lotes")
        
        # Filtros de Mês e Ano adicionados no topo da Conferente para gerenciar o período
        col_m_prod_c, col_a_prod_c, col_espaco_prod_c = st.columns(3)
        with col_m_prod_c:
            mes_prod_sel = st.selectbox("Filtrar por Mês:", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=8, key="filtro_mes_esteira_ap_conf_v25")
        with col_a_prod_c:
            ano_prod_sel = st.selectbox("Filtrar por Ano:", ["2026", "2027", "2028", "2029", "2030"], index=0, key="filtro_ano_esteira_ap_conf_v25")
            
        st.markdown("<br>", unsafe_allow_html=True)

        if "lotes_gerais" in st.session_state and st.session_state.lotes_gerais:
            # --- MOTOR DE CÁLCULO DOS 4 CARDS PARA A CONFERÊNCIA ---
            qtd_pendentes = 0
            qtd_em_producao = 0
            qtd_vencidos = 0
            qtd_concluidos = 0
            data_hoje_dt = datetime.now().date()
            
            meses_num = {"Janeiro":"01", "Fevereiro":"02", "Março":"03", "Abril":"04", "Maio":"05", "Junho":"06", "Julho":"07", "Agosto":"08", "Setembro":"09", "Outubro":"10", "Novembro":"11", "Dezembro":"12"}
            mes_procurado = meses_num[mes_prod_sel]
            chave_mes_ano_filtro = f"/{mes_procurado}/{ano_prod_sel}"
            
            for item in st.session_state.lotes_gerais:
                data_cad_str = item.get("data_cadastro", datetime.now().strftime("%d/%m/%Y"))
                data_ent_str = item.get("data_entrega", "")
                status_atual = item.get("status", "Pendente")
                
                # Regra idêntica de rolagem viva para contagem precisa dos cards
                if (chave_mes_ano_filtro in data_cad_str) or (status_atual in ["Pendente", "Em produção", "Em production"]):
                    try: data_entrega_dt = datetime.strptime(data_ent_str, "%d/%m/%Y").date()
                    except: data_entrega_dt = None
                    
                    if status_atual == "Pendente":
                        qtd_pendentes += 1
                    elif status_atual in ["Em produção", "Em production"]:
                        qtd_em_producao += 1
                    elif status_atual == "Concluído":
                        qtd_concluidos += 1
                        
                    if data_entrega_dt and status_atual != "Concluído" and data_hoje_dt > data_entrega_dt:
                        qtd_vencidos += 1

            # --- DESENHO DOS 4 CARDS COLORIDOS HORIZONTAIS NA CONFERÊNCIA ---
            card_c1, card_c2, card_c3, card_c4 = st.columns(4)
            with card_c1:
                st.markdown(f"<div style='background-color: #EF6C00; padding: 15px; border-radius: 8px; color: white; text-align: center;'><b>Lotes Pendentes</b><br><h2>{qtd_pendentes}</h2></div>", unsafe_allow_html=True)
            with card_c2:
                st.markdown(f"<div style='background-color: #2E7D32; padding: 15px; border-radius: 8px; color: white; text-align: center;'><b>Em Produção</b><br><h2>{qtd_em_producao}</h2></div>", unsafe_allow_html=True)
            with card_c3:
                st.markdown(f"<div style='background-color: #C62828; padding: 15px; border-radius: 8px; color: white; text-align: center;'><b>Lotes Vencidos</b><br><h2>{qtd_vencidos}</h2></div>", unsafe_allow_html=True)
            with card_c4:
                st.markdown(f"<div style='background-color: #1565C0; padding: 15px; border-radius: 8px; color: white; text-align: center;'><b>Concluídos</b><br><h2>{qtd_concluidos}</h2></div>", unsafe_allow_html=True)
                
            st.markdown("<br><hr>", unsafe_allow_html=True)
            st.write("📝 **Controle de Fluxo:** Avalie o progresso da fábrica. Somente a Conferência pode marcar os lotes como **Concluído**!")

            linhas_tabela_ap = []
            for index, item in enumerate(st.session_state.lotes_gerais):
                    data_cad_str = item.get("data_cadastro", datetime.now().strftime("%d/%m/%Y"))
                    data_ini_str = item.get("data_inicio_producao", "")
                    data_ent_str = item.get("data_entrega", "")
                    status_atual = item.get("status", "Pendente")
                    prioridade_atual = item.get("prioridade", "Não")
                    
                    pertence_ao_mes_do_filtro = (chave_mes_ano_filtro in data_cad_str)
                    ativo_para_rolagem = (status_atual in ["Pendente", "Em produção", "Em production"])
                    
                    if pertence_ao_mes_do_filtro or ativo_para_rolagem:
                        try: data_chegada_dt = datetime.strptime(data_cad_str, "%d/%m/%Y").date()
                        except: data_chegada_dt = data_hoje_dt
                        
                        try: data_entrega_dt = datetime.strptime(data_ent_str, "%d/%m/%Y").date()
                        except: data_entrega_dt = None
                        
                        if status_atual == "Pendente":
                            dias_pendencia = (data_hoje_dt - data_chegada_dt).days; dias_producao = 0
                        elif status_atual in ["Em production", "Em produção"]:
                            try: data_inicio_dt = datetime.strptime(data_ini_str, "%d/%m/%Y").date()
                            except: data_inicio_dt = data_hoje_dt
                            dias_pendencia = (data_inicio_dt - data_chegada_dt).days
                            dias_producao = (data_hoje_dt - data_inicio_dt).days
                        else:
                            dias_pendencia = 0; dias_producao = 0
                            
                        if dias_pendencia < 0: dias_pendencia = 0
                        if dias_producao < 0: dias_producao = 0
                        
                        if status_atual == "Concluído":
                            sinalizacao_final = "🔵"
                        else:
                            if data_entrega_dt and data_hoje_dt > data_entrega_dt: bolinha_status = "🔴"
                            elif status_atual == "Pendente": bolinha_status = "🟠"
                            else: bolinha_status = "🟢"
                                
                            if prioridade_atual == "Sim": sinalizacao_final = f"{bolinha_status} {bolinha_status}"
                            else: sinalizacao_final = bolinha_status
                        
                        linhas_tabela_ap.append({
                            "ID_Original": index, "🚨 Alerta": sinalizacao_final,
                            "Nome do fornecedor / Marca": item.get("fornecedor", ""),
                            "Número da O.F (Ordem de Fabricação)": item.get("of", ""),
                            "Referência do Modelo (Peça)": item.get("referencia", ""),
                            "Quantidade Total de Peças na Nota": item.get("qtd_prevista", 0),
                            "Dias em pendência": int(dias_pendencia), "Dias em produção": int(dias_producao),
                            "Data chegada": data_cad_str, "Data para entrega": data_ent_str,
                            "Preço Unitário": item.get("preco", 0.0), "Status": "Em produção" if status_atual == "Em production" else status_atual,
                            "Porcentagem já produzido": f"{item.get('porcentagem_pronta', 0)}%", "prioridade": prioridade_atual
                        })
                        
            # O EDITOR FICA FORA DO FOR — PREVENÇÃO DE DUPLICIDADE DE CHAVE
            if linhas_tabela_ap:
                if "versao_esteira_ap_conf" not in st.session_state: 
                    st.session_state.versao_esteira_ap_conf = 0
                chave_tabela_ap_conf = f"tab_ap_conf_v27_sinc_def_{mes_prod_sel}_{ano_prod_sel}_v{st.session_state.versao_esteira_ap_conf}"
                
                # Prepara os dados injetando a quantidade real vinda da gaveta oficial da fábrica
                for linha_fp in linhas_tabela_ap:
                    idx = linha_fp["ID_Original"]
                    linha_fp["✅ Peças Prontas Reais"] = int(st.session_state.lotes_gerais[idx].get("qtd_pronta", 0))

                tabela_ap_editada_conf = st.data_editor(
                    linhas_tabela_ap,
                    column_config={
                        "ID_Original": None,
                        "🚨 Alerta": st.column_config.TextColumn("🚨 Alerta", disabled=True),
                        "Nome do fornecedor / Marca": st.column_config.TextColumn("Nome do fornecedor / Marca", disabled=True),
                        "Número da O.F (Ordem de Fabricação)": st.column_config.TextColumn("Número da O.F (Ordem de Fabricação)", disabled=True),
                        "Referência do Modelo (Peça)": st.column_config.TextColumn("Referência do Modelo (Peça)", disabled=True),
                        "Quantidade Total de Peças na Nota": st.column_config.NumberColumn("Quantidade Total de Peças na Nota", disabled=True),
                        "Dias em pendência": st.column_config.NumberColumn("Dias em pendência", disabled=True),
                        "Dias em produção": st.column_config.NumberColumn("Dias em produção", disabled=True),
                        "Data chegada": st.column_config.TextColumn("Data chegada", disabled=True),
                        "Data para entrega": st.column_config.TextColumn("Data para entrega", disabled=True),
                        "Preço Unitário": st.column_config.NumberColumn("Preço Unitário", format="R$ %.2f", disabled=True),
                        "Status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Em produção", "Concluído"], required=True),
                        # AS DUAS COLUNAS LADO A LADO NA TELA DO CONTROLE DE QUALIDADE:
                        "Porcentagem já produzido": st.column_config.TextColumn("Porcentagem já produzido", disabled=True),
                        "✅ Peças Prontas Reais": st.column_config.NumberColumn("✅ Peças Prontas Reais", min_value=0, step=1), # Editável para conferência ajustar se necessário
                        "prioridade": st.column_config.SelectboxColumn("prioridade", options=["Não", "Sim"], disabled=True)
                    },
                    hide_index=True, use_container_width=True, key=chave_tabela_ap_conf
                )
                
                dados_mudaram_ap_conf = False
                if chave_tabela_ap_conf in st.session_state and st.session_state[chave_tabela_ap_conf]["edited_rows"]:
                    dados_mudaram_ap_conf = True
                    
                if dados_mudaram_ap_conf:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.warning("⚠️ **Aviso de Alteração:** Mudanças de status ou contagem real pendentes na Conferência!")
                    
                    col_salvar_ap_c, col_cancelar_ap_c = st.columns(2)
                    with col_salvar_ap_c:
                        if st.button("💾 Confirmar e Finalizar Lotes", use_container_width=True, type="primary", key="btn_salvar_conf_v27"):
                            for linha in tabela_ap_editada_conf:
                                idx_global = linha["ID_Original"]
                                status_novo = linha["Status"]
                                qtd_real_final = int(linha["✅ Peças Prontas Reais"])
                                
                                # Salva na memória do sistema as duas informações separadas
                                st.session_state.lotes_gerais[idx_global]["status"] = status_novo
                                st.session_state.lotes_gerais[idx_global]["qtd_pronta"] = qtd_real_final
                                
                                # Se foi concluído, força a porcentagem para 100% automaticamente
                                if status_novo == "Concluído":
                                    st.session_state.lotes_gerais[idx_global]["porcentagem_pronta"] = 100
                                    
                            st.success("🎉 Lotes faturados com as quantidades reais e porcentagens sincronizadas!"); st.rerun()
                            
                    with col_cancelar_ap_c:
                        if st.button("❌ Descartar e Voltar", use_container_width=True, key="btn_desc_conf_v27"):
                            if chave_tabela_ap_conf in st.session_state: del st.session_state[chave_tabela_ap_conf]
                            st.session_state.versao_esteira_ap_conf += 1; st.rerun()
                           
                            # REQUISITO EXIGIDO: NOVA SUB-PÁGINA DE IMPORTAÇÃO DE PONTO NA CONFERÊNCIA
        # REQUISITO EXIGIDO: NOVA SUB-PÁGINA DE IMPORTAÇÃO DE PONTO NA CONFERÊNCIA
    elif st.session_state.pagina_conf_atual == "📥 Importar Ponto":
        st.subheader("📥 Importar Relatório do Relógio de Ponto — FA05H")
        st.write("Insira o arquivo gerado no Pen Drive pelo aparelho para atualizar as horas trabalhadas acumuladas do mês:")
        
        # SOLUÇÃO DEFINITIVA: Pega o mês e o ano direto da data real do computador de forma automática!
        meses_num = {"Janeiro":"01", "Fevereiro":"02", "Março":"03", "Abril":"04", "Maio":"05", "Junho":"06", "Julho":"07", "Agosto":"08", "Setembro":"09", "Outubro":"10", "Novembro":"11", "Dezembro":"12"}
        
        # Cria as duas variáveis usando a data do sistema para a gravação permanente não se perder
        mes_prod_sel = datetime.now().strftime("%B").title() # Ex: 'Setembro'
        # Correção automática para português caso o Windows esteja em inglês
        traducao_meses = {"September": "Setembro", "October": "Outubro", "November": "Novembro", "December": "Dezembro"}
        mes_prod_sel = traducao_meses.get(mes_prod_sel, mes_prod_sel)
        
        ano_prod_sel = datetime.now().strftime("%Y") # Ex: '2026'
        
        # Cria a caixinha de upload de arquivos na tela
        arquivo_ponto = st.file_uploader("Arraste ou selecione o arquivo do Pen Drive (.xlsx ou .xls)", type=["xlsx", "xls"], key="uploader_ponto_conferente_fa05h_v29")
        
        if arquivo_ponto is not None:
            try:
                # Carrega o arquivo usando a biblioteca pandas
                df_ponto = pd.read_excel(arquivo_ponto, sheet_name="Resumo de atend.")
                st.success("📊 Arquivo do relógio de ponto lido com sucesso na memória da DLR!")
                
                # Roda o motor matemático avançado para decifrar a matriz horizontal do cartão
                banco_horas_calculado = processar_arquivo_ponto_fa05h(df_ponto)
                
                if banco_horas_calculado:
                    st.markdown("### 📋 Horas Acumuladas Detectadas no Período:")
                    
                    # Certifica que o dicionário de presenças temporárias existe
                    if "presencas_ponto" not in st.session_state:
                        st.session_state.presencas_ponto = {}
                        
                    # CRIA A CHAVE DE PERÍODO CRONOLÓGICA (Ex: 09/2026)
                    m_ponto_c = meses_num.get(mes_prod_sel, "09")
                    chave_periodo_ponto_db = f"{m_ponto_c}/{ano_prod_sel}"
                    
                    linhas_resumo = []
                    for nome_func, total_h in banco_horas_calculado.items():
                        nome_f_limpo = nome_func.strip().title()
                        
                        # 1. Salva na memória do navegador para exibição imediata
                        st.session_state.presencas_ponto[nome_f_limpo] = total_h
                        
                        # 2. GRAVAÇÃO DEFINITIVA NO HD: Salva no arquivo .db travado por período
                        db_salvar_ponto_horas(
                            nome=nome_f_limpo, 
                            mes_ano=chave_periodo_ponto_db, 
                            total_horas=total_h
                        )
                        
                        linhas_resumo.append({
                            "Funcionário": nome_f_limpo, 
                            "Total Horas Relógio": f"{total_h:.2f} hrs"
                        })
                        
                    st.dataframe(linhas_resumo, use_container_width=True, hide_index=True)
                    st.success("💾 Sucesso! As horas do relógio FA05H foram trancadas de forma permanente no HD da empresa!")
                else:
                    st.warning("⚠️ O arquivo foi lido, mas a estrutura de colunas do resumo do FA05H não foi localizada.")
                    
            except Exception as e:
                st.error(f"❌ Erro crítico ao processar o arquivo de ponto. Detalhe técnico: {e}")
        
        # --- 🪡 ÁREA 3: MANUAL / PRODUÇÃO — DLR ---
elif st.session_state.perfil_atual == "manual":
    
    # Inicializa a sub-página padrão da produção se não existir
    if "pagina_man_atual" not in st.session_state:
        st.session_state.pagina_man_atual = "⏱️ Produção de Hora em Hora"
        
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🗂️ Painel da Produção")
        
        # REQUISITO EXIGIDO: Adicionado a nova página 📅 P.D no menu lateral
        paginas_man = {
            "⏱️ Produção de Hora em Hora": "⏱️ Produção de Hora em Hora",
            "📦 Entrada de Lotes (Fornecedor)": "📦 Entrada de Lotes (Fornecedor)",
            "📅 Peças Produzidas por Dia (P.D)": "📅 Peças Produzidas por Dia (P.D)" # <-- NOVO BOTÃO P.D
        }
        
        # REGRA DE IDENTIDADE VISUAL: Página ativa fica BRANCA com letra PRETA
        for label, pagina_id in paginas_man.items():
            if st.session_state.pagina_man_atual == pagina_id:
                st.markdown(f"""
                    <div style='background-color: #FFFFFF; color: #000000; padding: 10px 15px; border-radius: 6px; font-weight: bold; text-align: center; border: 2px solid #4A154B; margin-bottom: 8px;'>
                        {label}
                    </div>
                """, unsafe_allow_html=True)
            else:
                if st.button(label, use_container_width=True, key=f"btn_man_v26_{pagina_id}"):
                    st.session_state.pagina_man_atual = pagina_id
                    st.rerun()

        # Botão de Sair isolado no rodapé da produção
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🚪 Sair do Sistema", use_container_width=True, type="secondary", key="btn_sair_manual_v26"):
            st.session_state.logado = False
            st.session_state.perfil_atual = None
            st.rerun()

    # --- CARREGAMENTO DAS TELAS DO SETOR MANUAL ---
    
    # TELA 1: TABELA DE PRODUÇÃO DIÁRIA DE HORA EM HORA
    if st.session_state.pagina_man_atual == "⏱️ Produção de Hora em Hora":
        st.subheader("⏱️ Controle de Eficiência — Produção de Hora em Hora")
        st.write("Selecione a colaboradora e registre a quantidade de peças prontas entregues no fechamento de cada hora:")
        
        # Puxa a lista oficial e viva de funcionários cadastrados no Administrador
        lista_costureiras = [f["nome"] for f in st.session_state.get("funcionarios", []) if f.get("cargo") == "Costureira"]
        
        if not lista_costureiras:
            st.warning("⚠️ Nenhuma funcionária com o cargo de 'Costureira' foi cadastrada no sistema pelo Administrador.")
        else:
            # Filtros horizontais de monitoramento
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                costureira_sel = st.selectbox("👤 Selecionar Costureira:", lista_costureiras, key="prod_hora_costureira_sel_v25")
            with col_h2:
                data_registro_prod = st.date_input("📅 Data do Acompanhamento:", value=datetime.now(), key="prod_hora_data_sel_v25")
                
            data_prod_txt = data_registro_prod.strftime("%d/%m/%Y")
            st.markdown("---")
            
            # Inicializa a gaveta global de registros horários se não existir
            if "historico_producao_hora" not in st.session_state:
                st.session_state.historico_producao_hora = []
                
            # Cria a chave única combinando a costureira e o dia para os dados não se misturarem
            chave_registro_dia = f"{costureira_sel}_{data_prod_txt}"
            
            # Busca se já existem dados salvos desse dia para essa costureira, senão cria uma jornada limpa
            jornada_atual = None
            for registro in st.session_state.historico_producao_hora:
                if registro.get("ID_Chave") == chave_registro_dia:
                    jornada_atual = registro.get("Tabela")
                    break
                    
            if jornada_atual is None:
                jornada_atual = [
                    {"Horário": "07:00 às 08:00", "Quantidade Produzida": 0, "Observações / Ocorrências": ""},
                    {"Horário": "08:00 às 09:00", "Quantidade Produzida": 0, "Observações / Ocorrências": ""},
                    {"Horário": "09:00 às 10:00", "Quantidade Produzida": 0, "Observações / Ocorrências": ""},
                    {"Horário": "10:00 às 11:00", "Quantidade Produzida": 0, "Observações / Ocorrências": ""},
                    {"Horário": "11:00 às 12:00", "Quantidade Produzida": 0, "Observações / Ocorrências": ""},
                    {"Horário": "13:00 às 14:00", "Quantidade Produzida": 0, "Observações / Ocorrências": ""},
                    {"Horário": "14:00 às 15:00", "Quantidade Produzida": 0, "Observações / Ocorrências": ""},
                    {"Horário": "15:00 às 16:00", "Quantidade Produzida": 0, "Observações / Ocorrências": ""},
                    {"Horário": "16:00 às 17:00", "Quantidade Produzida": 0, "Observações / Ocorrências": ""},
                ]
            
            st.markdown(f"### 📋 Folha Horária: **{costureira_sel}** — Dia {data_prod_txt}")
            
            if "versao_editor_hora" not in st.session_state:
                st.session_state.versao_editor_hora = 0
                
            chave_editor_hora = f"editor_hora_{costureira_sel}_{data_prod_txt}_v{st.session_state.versao_editor_hora}"
            
            # Desenha a planilha interativa na tela
            tabela_hora_editada = st.data_editor(
                jornada_atual,
                column_config={
                    "Horário": st.column_config.TextColumn("⏰ Período da Jornada", disabled=True),
                    "Quantidade Produzida": st.column_config.NumberColumn("🔢 Peças Concluídas", min_value=0, step=1),
                    "Observações / Ocorrências": st.column_config.TextColumn("💬 Motivo de Paradas / Notas (Falta de elástico, agulha quebrou...)")
                },
                hide_index=True,
                use_container_width=True,
                key=chave_editor_hora
            )
            
            # 1. Soma total automática do dia para monitorar a meta no topo
            total_pecas_costureira = sum([int(item.get("Quantidade Produzida", 0)) for item in tabela_hora_editada])
            st.success(f"📊 **Rendimento do Dia:** {costureira_sel} já produziu **{total_pecas_costureira} peças** na data de hoje!")

            # 2. INTELIGÊNCIA DE CHECAGEM CORRIGIDA: Detecta alteração tanto em linhas editadas quanto células soltas
            dados_mudaram_hora = False
            if chave_editor_hora in st.session_state:
                estado_h = st.session_state[chave_editor_hora]
                if estado_h["edited_rows"]:
                    dados_mudaram_hora = True

            if dados_mudaram_hora:
                st.markdown("<br>", unsafe_allow_html=True)
                st.warning(f"⚠️ **Aviso de Alteração:** Você modificou os lançamentos de hora em hora de **{costureira_sel}**! Salve para registrar de verdade.")
                
                col_salvar_h, col_cancelar_h = st.columns(2)
                with col_salvar_h:
                    if st.button("💾 Confirmar e Gravar Production Horária", use_container_width=True, type="primary", key="btn_salvar_hora_v25_fixed"):
                        # Atualiza ou adiciona o registro na gaveta do histórico geral
                        encontrou_registro = False
                        for registro in st.session_state.historico_producao_hora:
                            if registro.get("ID_Chave") == chave_registro_dia:
                                registro["Tabela"] = tabela_hora_editada
                                encontrou_registro = True
                                break
                        
                        if not encontrou_registro:
                            st.session_state.historico_producao_hora.append({
                                "ID_Chave": chave_registro_dia,
                                "Costureira": costureira_sel,
                                "Data": data_prod_txt,
                                "Tabela": tabela_hora_editada
                            })
                        
                        # --- SINCRONIZAÇÃO COMPLETA COM O GRÁFICO DO ADMIN ---
                        if "producao_hora" not in st.session_state:
                            st.session_state.producao_hora = []
                            
                        st.session_state.producao_hora = [r for r in st.session_state.producao_hora if r.get("Costureira") != costureira_sel]
                        
                        st.session_state.producao_hora.append({
                            "Costureira": costureira_sel,
                            "9H": int(tabela_hora_editada[0].get("Quantidade Produzida", 0)) + int(tabela_hora_editada[1].get("Quantidade Produzida", 0)),
                            "10H": int(tabela_hora_editada[2].get("Quantidade Produzida", 0)),
                            "11H": int(tabela_hora_editada[3].get("Quantidade Produzida", 0)),
                            "12H": int(tabela_hora_editada[4].get("Quantidade Produzida", 0)),
                            "14H": int(tabela_hora_editada[5].get("Quantidade Produzida", 0)),
                            "15H": int(tabela_hora_editada[6].get("Quantidade Produzida", 0)),
                            "16H": int(tabela_hora_editada[7].get("Quantidade Produzida", 0)),
                            "17H": int(tabela_hora_editada[8].get("Quantidade Produzida", 0))
                        })
                        
                        # Limpa o cache técnico do editor de dados para fechar o aviso amarelo
                        if chave_editor_hora in st.session_state:
                            del st.session_state[chave_editor_hora]
                            
                        st.success(f"🎉 Lançamentos de {costureira_sel} gravados com sucesso na folha do dia!")
                        st.rerun()
                        
                with col_cancelar_h:
                    if st.button("❌ Descartar Mudanças", use_container_width=True, key="btn_cancelar_hora_v25_fixed"):
                        if chave_editor_hora in st.session_state:
                            del st.session_state[chave_editor_hora]
                        st.session_state.versao_editor_hora += 1
                        st.rerun()

# --- MOTOR DO GRÁFICO DE RENDIMENTO MENSAL INDIVIDUAL ---
            st.markdown("<br><hr>", unsafe_allow_html=True)
            st.markdown(f"### 📊 Rendimento Mensal Individual: **{costureira_sel}**")
            st.write(f"Acompanhe o volume de peças concluídas por **{costureira_sel}** dia a dia no mês selecionado:")

            # Cria um dicionário com os 31 dias zerados para iniciar o gráfico limpo
            dados_dias_costureira = {f"Dia {d:02d}": 0 for d in range(1, 32)}

            # Varre o histórico na memória filtrando APENAS pela costureira selecionada no topo
            if "historico_producao_hora" in st.session_state:
                for registro in st.session_state.historico_producao_hora:
                    # FILTRO DE OURO: Só calcula se o registro pertencer à costureira da tela
                    if str(registro.get("Costureira")).strip().lower() == str(costureira_sel).strip().lower():
                        data_reg = registro.get("Data", "") # Formato esperado: "dd/mm/aaaa"
                        tabela_reg = registro.get("Tabela", [])
                        
                        if data_reg and tabela_reg:
                            try:
                                # Corta a data para pegar apenas o número do dia (Ex: "23/09/2026" -> 23)
                                dia_puro = int(data_reg.split("/")[0])
                                chave_dia = f"Dia {dia_puro:02d}"
                                
                                # Acumula as peças produzidas por ela nessa data específica
                                if chave_dia in dados_dias_costureira:
                                    total_desse_dia = sum([int(item.get("Quantidade Produzida", 0)) for item in tabela_reg])
                                    dados_dias_costureira[chave_dia] += total_desse_dia
                            except:
                                pass

            # Transforma os dados no DataFrame do Pandas para o Streamlit desenhar
            import pandas as pd
            df_grafico_individual = pd.DataFrame(list(dados_dias_costureira.items()), columns=["Dia do Mês", "Peças Concluídas"])
            df_grafico_individual.set_index("Dia do Mês", inplace=True)

            # Renderiza o gráfico de barras exclusivo da costureira
            st.bar_chart(df_grafico_individual, use_container_width=True)

    # TELA 2: ENTRADA DE LOTES (CONTROLE DE CARGA DO FORNECEDOR)
    if st.session_state.pagina_man_atual == "📦 Entrada de Lotes (Fornecedor)":
        # Inicializa o interruptor de sub-páginas internas da produção
        if "sub_pagina_lotes" not in st.session_state:
            st.session_state.sub_pagina_lotes = "C.L"
            
        st.markdown("<br>", unsafe_allow_html=True)
        col_b1, col_b2, col_b_vazia = st.columns(3)
        
        with col_b1:
            tipo_cl = "primary" if st.session_state.sub_pagina_lotes == "C.L" else "secondary"
            if st.button("📝 Cadastrar Lote (C.L)", use_container_width=True, type=tipo_cl, key="btn_sub_cl_v21"):
                st.session_state.sub_pagina_lotes = "C.L"
                st.rerun()
        with col_b2:
            tipo_ap = "primary" if st.session_state.sub_pagina_lotes == "A.P" else "secondary"
            if st.button("📈 Andamento de Produção (A.P)", use_container_width=True, type=tipo_ap, key="btn_sub_ap_v21"):
                st.session_state.sub_pagina_lotes = "A.P"
                st.rerun()
                
        st.markdown("---")

        # --- SEÇÃO 1: FORMULÁRIO DE CADASTRO (C.L) ---
        if st.session_state.sub_pagina_lotes == "C.L":
            st.subheader("📦 Cadastro e Recepção de Novos Lotes de Tecido")
            st.write("Preencha os dados da nota do fornecedor para dar entrada oficial na matéria-prima:")
            
            if "lotes_gerais" not in st.session_state:
                st.session_state.lotes_gerais = []
                
            if "contador_form_producao" not in st.session_state:
                st.session_state.contador_form_producao = 0
                
            with st.form(key=f"form_prod_lotes_v21_{st.session_state.contador_form_producao}", clear_on_submit=False):
                fornecedor = st.text_input("Nome do Fornecedor / Marca")
                of_lote = st.text_input("Número da O.F (Ordem de Fabricação)")
                referencia = st.text_input("Referência do Modelo (Peça)")
                
                col_p1, col_p2, col_p3_chegada, col_p3, col_p4 = st.columns(5) # Mudou para 5 colunas
                with col_p1:
                    qtd_prevista = st.number_input("Quantidade Total na Nota", min_value=1, step=10, value=1)
                with col_p2:
                    preco_peca = st.number_input("Preço Unitário (R$)", min_value=0.0, format="%.2f", step=0.50)
                with col_p3_chegada:
                    # NOVO CAMPO: Permite escolher ou alterar a Data de Chegada (Padrão: Hoje)
                    data_chegada_sel = st.date_input("📅 Data de Chegada", value=datetime.now())
                with col_p3:
                    data_entrega = st.date_input("📅 Previsão de Entrega", value=datetime.now())
                with col_p4:
                    prioridade = st.selectbox("🔥 Prioridade?", ["Não", "Sim"])
                    
                registrar_lote = st.form_submit_button("📦 Registrar Entrada do Lote")
                
                if registrar_lote:
                    if not fornecedor.strip() or not of_lote.strip() or not referencia.strip():
                        st.error("❌ Todos os campos de texto são obrigatórios!")
                    elif preco_peca <= 0:
                        st.error("❌ O preço unitário deve ser maior que R$ 0,00.")
                    else:
                        # Converte a data escolhida no calendário para o formato de texto padrão (dia/mês/ano)
                        data_cadastro_escolhida = data_chegada_sel.strftime("%d/%m/%Y")
                        data_entrega_txt = data_entrega.strftime("%d/%m/%Y")
                        
                        st.session_state.lotes_gerais.append({
                            "data_cadastro": data_cadastro_escolhida, # Agora grava a data que você escolheu!
                            "data_inicio_producao": "",
                            "fornecedor": fornecedor.strip(),
                            "of": of_lote.strip(),
                            "referencia": referencia.strip(),
                            "qtd_prevista": int(qtd_prevista),
                            "preco": preco_peca,
                            "data_entrega": data_entrega_txt,
                            "prioridade": prioridade,
                            "status": "Pendente",
                            "porcentagem_pronta": 0
                        })
                        
                        # Tranca de forma vitalícia no banco de dados SQLite do HD
                        super_robo_trancar_memoria_para_hd()
                        
                        st.success(f"🎉 Lote OF {of_lote} registrado com sucesso!")
                        st.session_state.contador_form_producao += 1
                        st.rerun()
                        
                        # --- SEÇÃO 2: ANDAMENTO DE PRODUÇÃO (A.P) ---
        elif st.session_state.sub_pagina_lotes == "A.P":
            st.subheader("📈 Andamento de Produção e Linha do Tempo de Lotes")
            
            # Filtros de Mês e Ano adicionados no topo do A.P para gerenciar o período
            col_m_prod, col_a_prod, col_espaco_prod = st.columns(3)
            with col_m_prod:
                mes_prod_sel = st.selectbox("Filtrar por Mês:", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=8, key="filtro_mes_esteira_ap_manual_v25")
            with col_a_prod:
                ano_prod_sel = st.selectbox("Filtrar por Ano:", ["2026", "2027", "2028", "2029", "2030"], index=0, key="filtro_ano_esteira_ap_manual_v25")
                
            st.markdown("<br>", unsafe_allow_html=True)

            if "lotes_gerais" in st.session_state and st.session_state.lotes_gerais:
                # --- MOTOR DE CÁLCULO DOS 4 CARDS PARA O SETOR MANUAL ---
                qtd_pendentes = 0
                qtd_em_producao = 0
                qtd_vencidos = 0
                qtd_concluidos = 0
                data_hoje_dt = datetime.now().date()
                
                meses_num = {"Janeiro":"01", "Fevereiro":"02", "Março":"03", "Abril":"04", "Maio":"05", "Junho":"06", "Julho":"07", "Agosto":"08", "Setembro":"09", "Outubro":"10", "Novembro":"11", "Dezembro":"12"}
                mes_procurado = meses_num[mes_prod_sel]
                chave_mes_ano_filtro = f"/{mes_procurado}/{ano_prod_sel}"
                
                for item in st.session_state.lotes_gerais:
                    data_cad_str = item.get("data_cadastro", datetime.now().strftime("%d/%m/%Y"))
                    data_ent_str = item.get("data_entrega", "")
                    status_atual = item.get("status", "Pendente")
                    
                    # Filtra de acordo com a regra de rolagem de meses ativos
                    if (chave_mes_ano_filtro in data_cad_str) or (status_atual in ["Pendente", "Em produção", "Em production"]):
                        try: data_entrega_dt = datetime.strptime(data_ent_str, "%d/%m/%Y").date()
                        except: data_entrega_dt = None
                        
                        # Contagem por Status
                        if status_atual == "Pendente":
                            qtd_pendentes += 1
                        elif status_atual in ["Em produção", "Em production"]:
                            qtd_em_producao += 1
                        elif status_atual == "Concluído":
                            qtd_concluidos += 1
                            
                        # Contagem de Vencidos (Passou do prazo e não foi concluído)
                        if data_entrega_dt and status_atual != "Concluído" and data_hoje_dt > data_entrega_dt:
                            qtd_vencidos += 1

                # --- DESENHO DOS 4 CARDS COLORIDOS HORIZONTAIS NO MANUAL ---
                card_m1, card_m2, card_m3, card_m4 = st.columns(4)
                with card_m1:
                    st.markdown(f"<div style='background-color: #EF6C00; padding: 15px; border-radius: 8px; color: white; text-align: center;'><b>Lotes Pendentes</b><br><h2>{qtd_pendentes}</h2></div>", unsafe_allow_html=True)
                with card_m2:
                    st.markdown(f"<div style='background-color: #2E7D32; padding: 15px; border-radius: 8px; color: white; text-align: center;'><b>Em Produção</b><br><h2>{qtd_em_producao}</h2></div>", unsafe_allow_html=True)
                with card_m3:
                    st.markdown(f"<div style='background-color: #C62828; padding: 15px; border-radius: 8px; color: white; text-align: center;'><b>Lotes Vencidos</b><br><h2>{qtd_vencidos}</h2></div>", unsafe_allow_html=True)
                with card_m4:
                    st.markdown(f"<div style='background-color: #1565C0; padding: 15px; border-radius: 8px; color: white; text-align: center;'><b>Concluídos</b><br><h2>{qtd_concluidos}</h2></div>", unsafe_allow_html=True)
                    
                st.markdown("<br><hr>", unsafe_allow_html=True)
                st.write("📝 **Dica do Setor:** Altere entre **Pendente** e **Em produção**. Lotes ativos rolam de mês automaticamente!")

                linhas_tabela_ap = []
                for index, item in enumerate(st.session_state.lotes_gerais):
                    data_cad_str = item.get("data_cadastro", datetime.now().strftime("%d/%m/%Y"))
                    data_ini_str = item.get("data_inicio_producao", "")
                    data_ent_str = item.get("data_entrega", "")
                    status_atual = item.get("status", "Pendente")
                    prioridade_atual = item.get("prioridade", "Não")
                    
                    # Filtro de exibição e rolagem automática de meses
                    pertence_ao_mes_do_filtro = (chave_mes_ano_filtro in data_cad_str)
                    ativo_para_rolagem = (status_atual in ["Pendente", "Em produção"])
                    
                    if pertence_ao_mes_do_filtro or ativo_para_rolagem:
                        try: data_chegada_dt = datetime.strptime(data_cad_str, "%d/%m/%Y").date()
                        except: data_chegada_dt = data_hoje_dt
                        
                        try: data_entrega_dt = datetime.strptime(data_ent_str, "%d/%m/%Y").date()
                        except: data_entrega_dt = None
                        
                        if status_atual == "Pendente":
                            dias_pendencia = (data_hoje_dt - data_chegada_dt).days; dias_producao = 0
                        elif status_atual in ["Em production", "Em produção"]:
                            if not data_ini_str:
                                data_ini_str = datetime.now().strftime("%d/%m/%Y")
                                item["data_inicio_producao"] = data_ini_str
                            try: data_inicio_dt = datetime.strptime(data_ini_str, "%d/%m/%Y").date()
                            except: data_inicio_dt = data_hoje_dt
                            dias_pendencia = (data_inicio_dt - data_chegada_dt).days
                            dias_producao = (data_hoje_dt - data_inicio_dt).days
                        else:
                            dias_pendencia = 0; dias_producao = 0
                            
                        if dias_pendencia < 0: dias_pendencia = 0
                        if dias_producao < 0: dias_producao = 0
                        
                        # Regra das Bolinhas Inteligentes: Concluído apaga tudo!
                        if status_atual == "Concluído":
                            sinalizacao_final = "🔵"
                        else:
                            if data_entrega_dt and data_hoje_dt > data_entrega_dt: bolinha_status = "🔴"
                            elif status_atual == "Pendente": bolinha_status = "🟠"
                            else: bolinha_status = "🟢"
                                
                            if prioridade_atual == "Sim": sinalizacao_final = f"{bolinha_status} {bolinha_status}"
                            else: sinalizacao_final = bolinha_status
                        
                        linhas_tabela_ap.append({
                            "ID_Original": index, "🚨 Alerta": sinalizacao_final,
                            "Nome do fornecedor / Marca": item.get("fornecedor", ""),
                            "Número da O.F (Ordem de Fabricação)": item.get("of", ""),
                            "Referência do Modelo (Peça)": item.get("referencia", ""),
                            "Quantidade Total de Peças na Nota": item.get("qtd_prevista", 0),
                            "Dias em pendência": int(dias_pendencia), "Dias em produção": int(dias_producao),
                            "Data chegada": data_cad_str, "Data para entrega": data_ent_str,
                            "Preço Unitário": float(item.get("preco", item.get("preco_unitario", 0.0))), 
                            "Status": status_atual,
                            "Porcentagem já produzido": f"{item.get('porcentagem_pronta', 0)}%", 
                            "Peças Prontas Reais": int(item.get("qtd_pronta", 0)),
                            "prioridade": prioridade_atual
                        })
                        
             # O editor de dados fica devidamente embutido na parede correta do 'if' de lotes gerais
                if lotes_existentes := linhas_tabela_ap:
                    if "versao_esteira_ap_man" not in st.session_state: 
                        st.session_state.versao_esteira_ap_man = 0
                    chave_tabela_ap = f"tab_ap_manual_v25_v{st.session_state.versao_esteira_ap_man}"
                    
                    tabela_ap_editada = st.data_editor(
                        linhas_tabela_ap,
                        column_config={
                            "ID_Original": None,
                            "🚨 Alerta": st.column_config.TextColumn("🚨 Alerta", disabled=True),
                            "Nome do fornecedor / Marca": st.column_config.TextColumn("Nome do fornecedor / Marca", disabled=True),
                            "Número da O.F (Ordem de Fabricação)": st.column_config.TextColumn("Número da O.F (Ordem de Fabricação)", disabled=True),
                            "Referência do Modelo (Peça)": st.column_config.TextColumn("Referência do Modelo (Peça)", disabled=True),
                            "Quantidade Total de Peças na Nota": st.column_config.NumberColumn("Quantidade Total de Peças na Nota", disabled=True),
                            "Dias em pendência": st.column_config.NumberColumn("Dias em pendência", disabled=True),
                            "Dias em produção": st.column_config.NumberColumn("Dias em produção", disabled=True),
                            "Data chegada": st.column_config.TextColumn("Data chegada", disabled=True),
                            "Data para entrega": st.column_config.TextColumn("Data para entrega", disabled=True),
                            "Preço Unitário": st.column_config.NumberColumn("Preço Unitário", format="R$ %.2f", disabled=True),
                            "Status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Em produção"], required=True),
                            "Porcentagem já produzido": st.column_config.SelectboxColumn("Porcentagem já produzido", options=["0%", "10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%"], required=True),
                            "Peças Prontas Reais": st.column_config.NumberColumn("✅ Peças Prontas Reais", disabled=True),
                            "prioridade": st.column_config.SelectboxColumn("prioridade", options=["Não", "Sim"], required=True)
                        },
                        hide_index=True, use_container_width=True, key=chave_tabela_ap
                    )
                    
                    # --- CAIXINHA DE EXCLUSÃO POSICIONADA COM CHAVE DINÂMICA ---
                    st.markdown("<br>", unsafe_allow_html=True)
                    lista_ofs_excluir = [str(item["Número da O.F (Ordem de Fabricação)"]) for item in linhas_tabela_ap]
                    chave_seletor_lixeira = f"sel_of_excluir_manual_v{st.session_state.versao_esteira_ap_man}"
                    of_selecionada_excluir = st.selectbox("🗑️ Selecione O.F para excluir:", ["Selecionar..."] + lista_ofs_excluir, key=chave_seletor_lixeira)
                    
                    # Inteligência de checagem nativa integrada para tabela e lixeira
                    dados_mudaram_ap = False
                    if (chave_tabela_ap in st.session_state and st.session_state[chave_tabela_ap]["edited_rows"]) or (of_selecionada_excluir != "Selecionar..."):
                        dados_mudaram_ap = True
                        
                    if dados_mudaram_ap:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.warning("⚠️ **Aviso de Alteração:** Mudanças ou exclusões pendentes na produção!")
                        
                        col_salvar_ap, col_cancelar_ap = st.columns(2)
                        with col_salvar_ap:
                            if st.button("💾 Confirmar Alterações e Exclusões", use_container_width=True, type="primary", key="btn_salvar_man_v28_fixed"):
                                idx_global_deletar = None
                                
                                # 1. EXECUTA A EXCLUSÃO DA O.F SELECIONADA
                                if of_selecionada_excluir != "Selecionar...":
                                    for item_visao in linhas_tabela_ap:
                                        if str(item_visao["Número da O.F (Ordem de Fabricação)"]) == of_selecionada_excluir:
                                            idx_global_deletar = item_visao["ID_Original"]
                                            break
                                            
                                    if idx_global_deletar is not None and idx_global_deletar < len(st.session_state.lotes_gerais):
                                        st.session_state.lotes_gerais.pop(idx_global_deletar)
                                
                                # 2. EXECUTA OS SALVAMENTOS DE EDIÇÃO DAS OUTRAS LINHAS
                                if chave_tabela_ap in st.session_state and st.session_state[chave_tabela_ap]["edited_rows"]:
                                    for idx_visao_str, linha_edt in st.session_state[chave_tabela_ap]["edited_rows"].items():
                                        idx_global = linhas_tabela_ap[int(idx_visao_str)]["ID_Original"]
                                        
                                        # Pula a linha se ela acabou de ser deletada
                                        if idx_global_deletar is not None and idx_global == idx_global_deletar:
                                            continue
                                            
                                        original = st.session_state.lotes_gerais[idx_global]
                                        
                                        status_salvar = linha_edt.get("Status", original.get("status", "Pendente"))
                                        prioridade_salvar = linha_edt.get("prioridade", original.get("prioridade", "Não"))
                                        pct_str = linha_edt.get("Porcentagem já produzido", f"{original.get('porcentagem_pronta', 0)}%")
                                        pct_salvar = int(pct_str.replace("%", ""))
                                        
                                        valor_original_conferente = int(original.get("qtd_pronta", 0))
                                        
                                        if status_salvar == "Em produção" and not original.get("data_inicio_producao"):
                                            st.session_state.lotes_gerais[idx_global]["data_inicio_producao"] = datetime.now().strftime("%d/%m/%Y")
                                            
                                        st.session_state.lotes_gerais[idx_global]["status"] = status_salvar
                                        st.session_state.lotes_gerais[idx_global]["porcentagem_pronta"] = pct_salvar
                                        st.session_state.lotes_gerais[idx_global]["qtd_pronta"] = valor_original_conferente
                                        st.session_state.lotes_gerais[idx_global]["prioridade"] = prioridade_salvar
                                    
                                if chave_tabela_ap in st.session_state:
                                    del st.session_state[chave_tabela_ap]
                                st.session_state.versao_esteira_ap_man += 1
                                
                                super_robo_trancar_memoria_para_hd()
                                st.success("🎉 Alterações salvas com sucesso! Dados da DLR protegidos contra qualquer reset!")
                                st.rerun()
                                
                        with col_cancelar_ap:
                            if st.button("❌ Descartar Mudanças e Voltar", use_container_width=True, key="btn_desc_man_v25"):
                                # Limpa o cache técnico da planilha
                                if chave_tabela_ap in st.session_state: 
                                    del st.session_state[chave_tabela_ap]
                                    
                                # CORREÇÃO DE OURO: Atualiza a versão para forçar a lixeira a resetar para "Selecionar..."
                                st.session_state.versao_esteira_ap_man += 1
                                st.rerun()
                else:
                    st.info("💡 Nenhum lote ativo ou cadastrado neste período.")
            else:
                st.info("💡 Nenhum lote de tecido registrado na produção até o momento.")
                    
                                 
    # ==============================================================================
    # SUB-PÁGINA: PEÇAS PRODUZIDAS POR DIA (P.D) — COM RESET AUTOMÁTICO
    # ==============================================================================
    elif st.session_state.pagina_man_atual == "📅 Peças Produzidas por Dia (P.D)":
        st.subheader("📅 Registro de Production Diária Total")
        
        # Filtros de mês e ano para exibição do gráfico
        col_m_pd, col_a_pd = st.columns(2)
        with col_m_pd:
            mes_pd_sel = st.selectbox("Visualizar Gráfico do Mês:", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], index=8, key="pd_mes_grafico")
        with col_a_pd:
            ano_pd_sel = st.selectbox("Visualizar Gráfico do Ano:", ["2026", "2027", "2028", "2029", "2030"], index=0, key="pd_ano_grafico")

        meses_num = {"Janeiro":"01", "Fevereiro":"02", "Março":"03", "Abril":"04", "Maio":"05", "Junho":"06", "Julho":"07", "Agosto":"08", "Setembro":"09", "Outubro":"10", "Novembro":"11", "Dezembro":"12"}
        mes_filtro = meses_num[mes_pd_sel]

        if "banco_producao_diaria" not in st.session_state:
            st.session_state.banco_producao_diaria = {}

        # Inicializa o controlador de reset do formulário se não existir
        if "versao_form_pd" not in st.session_state:
            st.session_state.versao_form_pd = 0

        st.markdown("### 📥 Lançar Fechamento do Dia")
        
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            data_lancamento = st.date_input("📅 Selecione o Dia do Fechamento:", value=datetime.now(), key=f"pd_data_input_v26_{st.session_state.versao_form_pd}")
        with col_l2:
            # Vincula o valor à chave dinâmica para permitir o reset automático para zero
            qtd_pronta_dia = st.number_input("🔢 Quantidade de Peças Produzidas no Dia:", min_value=0, step=1, value=0, key=f"pd_qtd_input_v26_{st.session_state.versao_form_pd}")
            
        data_txt = data_lancamento.strftime("%d/%m/%Y")
        
        # O aviso só aparece se a quantidade digitada na caixinha for maior que zero
        if qtd_pronta_dia > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            st.warning(f"⚠️ **Aviso de Alteração:** Deseja registrar **{qtd_pronta_dia} peças** para a data de **{data_txt}**? Confirme abaixo.")
            
            col_salvar_pd, col_cancelar_pd = st.columns(2)
            with col_salvar_pd:
                if st.button("💾 Confirmar e Salvar Produção do Dia", use_container_width=True, type="primary", key="btn_confirmar_salvar_pd_v26"):
                    # Grava no dicionário estável
                    st.session_state.banco_producao_diaria[data_txt] = int(qtd_pronta_dia)
                    
                    # Tranca direto no arquivo .db do HD
                    super_robo_trancar_memoria_para_hd()
                    
                    # Muda a versão da chave para forçar o campo numérico a voltar para 0
                    st.session_state.versao_form_pd += 1
                    
                    st.success(f"🎉 Sucesso! **{qtd_pronta_dia} peças** foram gravadas em definitivo no HD para o dia {data_txt}!")
                    st.rerun()
                    
            with col_cancelar_pd:
                if st.button("❌ Descartar Lançamento", use_container_width=True, key="btn_cancelar_pd_v26"):
                    st.session_state.versao_form_pd += 1
                    st.rerun()

        # --- CONSTRUÇÃO DO GRÁFICO DIÁRIO CONTENDO TODOS OS DIAS DO MÊS ---
        dados_grafico_pd = []
        
        if mes_filtro in ["01", "03", "05", "07", "08", "10", "12"]: dias_no_mes = 31
        elif mes_filtro in ["04", "06", "09", "11"]: dias_no_mes = 30
        else: dias_no_mes = 28 # Fevereiro
        
        for dia in range(1, dias_no_mes + 1):
            data_formatada = f"{dia:02d}/{mes_filtro}/{ano_pd_sel}"
            total_do_dia = st.session_state.banco_producao_diaria.get(data_formatada, 0)
            
            dados_grafico_pd.append({
                "Dia do Mês": f"Dia {dia:02d}",
                "Peças Prontas (Total Fábrica)": total_do_dia
            })

        # --- EXIBIÇÃO VISUAL DO RENDIMENTO NO GRÁFICO MENSAL ---
        st.markdown(f"#### 📈 Gráfico de Rendimento Global: {mes_pd_sel} de {ano_pd_sel}")
        st.bar_chart(data=dados_grafico_pd, x="Dia do Mês", y="Peças Prontas (Total Fábrica)", use_container_width=True, height=350)
        
        pecas_totais_mes = sum([item["Peças Prontas (Total Fábrica)"] for item in dados_grafico_pd])
        st.info(f"📊 **Fechamento do Período:** O volume total acumulado em {mes_pd_sel} somou **{pecas_totais_mes} peças prontas**!")

# --- ACIONADOR AUTOMÁTICO INVISÍVEL DO SUPER ROBÔ DA DLR ---
super_robo_trancar_memoria_para_hd()                
                   