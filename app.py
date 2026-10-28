import io
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import qrcode
import streamlit as st
import streamlit.components.v1 as components
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "patrimonio_demo.db"
SCANNER_DIR = APP_DIR / "qr_scanner"

st.set_page_config(page_title="Vistoria Patrimonial", page_icon="🔎", layout="wide")


def connect_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                department_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Ativo',
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_id INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL DEFAULT 'Em andamento',
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inspection_reads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_id INTEGER NOT NULL,
                asset_id INTEGER,
                scanned_value TEXT NOT NULL,
                result TEXT NOT NULL,
                read_at TEXT NOT NULL,
                FOREIGN KEY (inspection_id) REFERENCES inspections(id),
                FOREIGN KEY (asset_id) REFERENCES assets(id)
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0]
        if count == 0:
            conn.execute("INSERT INTO departments(name) VALUES (?)", ("Administração",))
            conn.execute("INSERT INTO departments(name) VALUES (?)", ("Tecnologia da Informação",))
            conn.execute("INSERT INTO departments(name) VALUES (?)", ("Almoxarifado",))
            departments = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM departments")}
            demo_assets = [
                ("PAT-0001", "Notebook demonstrativo", "Equipamento de informática para teste", departments["Tecnologia da Informação"]),
                ("PAT-0002", "Monitor demonstrativo", "Monitor para teste de leitura", departments["Tecnologia da Informação"]),
                ("PAT-0003", "Mesa de escritório", "Mobiliário de demonstração", departments["Administração"]),
                ("PAT-0004", "Cadeira giratória", "Mobiliário de demonstração", departments["Administração"]),
                ("PAT-0005", "Estante metálica", "Item demonstrativo de almoxarifado", departments["Almoxarifado"]),
            ]
            conn.executemany(
                "INSERT INTO assets(asset_code, name, description, department_id) VALUES (?, ?, ?, ?)",
                demo_assets,
            )


def get_departments():
    with connect_db() as conn:
        return conn.execute("SELECT id, name FROM departments ORDER BY name").fetchall()


def get_assets(department_id=None):
    with connect_db() as conn:
        if department_id is None:
            rows = conn.execute("""
                SELECT a.*, d.name AS department_name
                FROM assets a JOIN departments d ON d.id = a.department_id
                ORDER BY a.asset_code
            """).fetchall()
        else:
            rows = conn.execute("""
                SELECT a.*, d.name AS department_name
                FROM assets a JOIN departments d ON d.id = a.department_id
                WHERE a.department_id = ? ORDER BY a.asset_code
            """, (department_id,)).fetchall()
        return [dict(r) for r in rows]


def make_qr_png(value):
    img = qrcode.make(value)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def build_pdf(inspection, department_name, rows):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Relatório demonstrativo de vistoria patrimonial", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"<b>Departamento:</b> {department_name}", styles["Normal"]),
        Paragraph(f"<b>Vistoria:</b> #{inspection['id']}", styles["Normal"]),
        Paragraph(f"<b>Início:</b> {inspection['started_at']}", styles["Normal"]),
        Paragraph(f"<b>Status:</b> {inspection['status']}", styles["Normal"]),
        Spacer(1, 14),
    ]
    data = [["Código", "Bem", "Resultado da leitura", "Data/hora"]]
    for row in rows:
        data.append([
            str(row.get("asset_code") or row["scanned_value"]),
            str(row.get("name") or "Não identificado"),
            str(row["result"]),
            str(row["read_at"]),
        ])
    if len(data) == 1:
        data.append(["—", "Nenhuma leitura registrada", "—", "—"])
    table = Table(data, colWidths=[100, 220, 220, 150], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263746")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F4F6")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Observação: este relatório registra leituras realizadas no protótipo. "
        "Ausência de leitura não comprova ausência física do bem; exige conferência humana.",
        styles["Italic"],
    ))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def scanner_component(key="scanner_v1"):
    scanner = components.declare_component(
        "zxing_qr_scanner",
        path=str(SCANNER_DIR)
    )
    return scanner(key=key)


init_db()
st.title("🔎 Vistoria Patrimonial")
st.caption("Protótipo de portfólio — leitura de QR Code, consulta SQL, painel e relatório PDF.")

with st.sidebar:
    st.header("Navegação")
    page = st.radio("Abrir", ["Realizar vistoria", "Patrimônio e QR Codes", "Painel e relatórios", "Sobre o protótipo"])
    st.divider()
    st.caption("Dados exclusivamente demonstrativos. O armazenamento SQLite na nuvem não é persistente.")

if page == "Realizar vistoria":
    st.subheader("1. Selecione o departamento")
    departments = get_departments()
    dept_by_name = {d["name"]: d["id"] for d in departments}
    dept_name = st.selectbox("Departamento da vistoria", list(dept_by_name.keys()))
    dept_id = dept_by_name[dept_name]

    if "inspection_id" not in st.session_state:
        st.session_state.inspection_id = None
    if "inspection_department" not in st.session_state:
        st.session_state.inspection_department = None
    if "last_scan" not in st.session_state:
        st.session_state.last_scan = ""

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("Iniciar nova vistoria", type="primary", use_container_width=True):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with connect_db() as conn:
                cur = conn.execute(
                    "INSERT INTO inspections(department_id, started_at) VALUES (?, ?)",
                    (dept_id, now),
                )
                st.session_state.inspection_id = cur.lastrowid
                st.session_state.inspection_department = dept_id
                st.session_state.last_scan = ""
            st.rerun()
    with c2:
        if st.session_state.inspection_id:
            st.info(f"Vistoria ativa #{st.session_state.inspection_id} — departamento selecionado: {dept_name}")
            if st.session_state.inspection_department != dept_id:
                st.warning("A vistoria ativa pertence a outro departamento. Inicie uma nova vistoria para trocar de departamento.")
        else:
            st.info("Inicie uma vistoria antes de ler etiquetas.")

    if st.session_state.inspection_id and st.session_state.inspection_department == dept_id:
        st.subheader("2. Leia a etiqueta do patrimônio")
        st.write("Permita o acesso à câmera. A leitura é processada nesta página; não há redirecionamento para outro site.")
        scan_value = scanner_component(key="scanner_v1")
        manual_value = st.text_input("Ou digite o código manualmente (modo de teste)", placeholder="Ex.: PAT-0001")
        received = (scan_value or "").strip()
        if manual_value.strip():
            received = manual_value.strip()

        if received and received != st.session_state.last_scan:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with connect_db() as conn:
                asset = conn.execute("""
                    SELECT a.*, d.name AS department_name
                    FROM assets a JOIN departments d ON d.id = a.department_id
                    WHERE a.asset_code = ?
                """, (received,)).fetchone()
                if asset is None:
                    result = "Código não cadastrado — identificação pendente"
                    asset_id = None
                    st.warning(f"QR lido: `{received}`. Não existe patrimônio cadastrado com esse código.")
                elif asset["department_id"] != dept_id:
                    result = "Bem cadastrado em outro departamento — possível divergência"
                    asset_id = asset["id"]
                    st.warning(f"{asset['name']} está cadastrado em **{asset['department_name']}**, não em **{dept_name}**.")
                else:
                    result = "Leitura confirmada"
                    asset_id = asset["id"]
                    st.success(f"Leitura confirmada: **{asset['asset_code']} — {asset['name']}**")
                conn.execute("""
                    INSERT INTO inspection_reads(inspection_id, asset_id, scanned_value, result, read_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (st.session_state.inspection_id, asset_id, received, result, now))
            st.session_state.last_scan = received
            st.rerun()

        with connect_db() as conn:
            read_rows = conn.execute("""
                SELECT ir.*, a.asset_code, a.name
                FROM inspection_reads ir LEFT JOIN assets a ON a.id = ir.asset_id
                WHERE ir.inspection_id = ? ORDER BY ir.id DESC
            """, (st.session_state.inspection_id,)).fetchall()
        st.subheader("3. Leituras desta vistoria")
        if read_rows:
            st.dataframe(pd.DataFrame([dict(r) for r in read_rows]), use_container_width=True, hide_index=True)
        else:
            st.caption("Nenhuma leitura registrada nesta vistoria.")

        if st.button("Finalizar vistoria"):
            with connect_db() as conn:
                conn.execute(
                    "UPDATE inspections SET finished_at = ?, status = ? WHERE id = ?",
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Finalizada", st.session_state.inspection_id),
                )
            st.success("Vistoria finalizada. O PDF pode ser gerado na página Painel e relatórios.")
            st.session_state.inspection_id = None
            st.session_state.inspection_department = None
            st.rerun()

elif page == "Patrimônio e QR Codes":
    st.subheader("Cadastro demonstrativo de patrimônio")
    st.caption("A base inicial já contém registros fictícios. Use o formulário para acrescentar bens durante a demonstração.")
    departments = get_departments()
    dept_by_name = {d["name"]: d["id"] for d in departments}
    with st.form("new_asset"):
        asset_code = st.text_input("Código único do patrimônio", placeholder="Ex.: PAT-0100")
        asset_name = st.text_input("Nome do bem", placeholder="Ex.: Notebook")
        description = st.text_input("Descrição")
        dept_name = st.selectbox("Departamento", list(dept_by_name.keys()))
        submitted = st.form_submit_button("Cadastrar patrimônio")
    if submitted:
        if not asset_code.strip() or not asset_name.strip():
            st.error("Informe o código e o nome do bem.")
        else:
            try:
                with connect_db() as conn:
                    conn.execute(
                        "INSERT INTO assets(asset_code, name, description, department_id) VALUES (?, ?, ?, ?)",
                        (asset_code.strip(), asset_name.strip(), description.strip(), dept_by_name[dept_name]),
                    )
                st.success("Patrimônio cadastrado.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Esse código já existe. Informe um código único.")
    assets = get_assets()
    st.dataframe(pd.DataFrame(assets), use_container_width=True, hide_index=True)
    st.subheader("Gerar QR Code para imprimir")
    if assets:
        options = {f"{a['asset_code']} — {a['name']} ({a['department_name']})": a for a in assets}
        selected = st.selectbox("Escolha o patrimônio", list(options.keys()))
        asset = options[selected]
        qr_bytes = make_qr_png(asset["asset_code"])
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(qr_bytes, caption=asset["asset_code"], width=220)
            st.download_button(
                "Baixar QR Code (PNG)",
                data=qr_bytes,
                file_name=f"qr_{asset['asset_code']}.png",
                mime="image/png",
            )
        with col2:
            st.markdown(f"**{asset['name']}**")
            st.write(f"Código: `{asset['asset_code']}`")
            st.write(f"Departamento: {asset['department_name']}")
            st.caption("Imprima a etiqueta e cole no item correspondente. Este protótipo usa o código do patrimônio como conteúdo do QR.")

elif page == "Painel e relatórios":
    st.subheader("Painel de vistorias")
    with connect_db() as conn:
        inspections = conn.execute("""
            SELECT i.*, d.name AS department_name
            FROM inspections i JOIN departments d ON d.id = i.department_id
            ORDER BY i.id DESC
        """).fetchall()
    if not inspections:
        st.info("Ainda não existem vistorias. Vá para 'Realizar vistoria' para começar.")
    else:
        ins_by_label = {
            f"#{i['id']} — {i['department_name']} — {i['started_at']} ({i['status']})": dict(i)
            for i in inspections
        }
        selected_label = st.selectbox("Selecione a vistoria", list(ins_by_label.keys()))
        inspection = ins_by_label[selected_label]
        with connect_db() as conn:
            rows = conn.execute("""
                SELECT ir.*, a.asset_code, a.name
                FROM inspection_reads ir LEFT JOIN assets a ON a.id = ir.asset_id
                WHERE ir.inspection_id = ? ORDER BY ir.id
            """, (inspection["id"],)).fetchall()
            expected = conn.execute(
                "SELECT COUNT(*) FROM assets WHERE department_id = ? AND status = 'Ativo'",
                (inspection["department_id"],),
            ).fetchone()[0]
        records = [dict(r) for r in rows]
        confirmed = sum(1 for r in records if r["result"] == "Leitura confirmada")
        pending = sum(1 for r in records if "pendente" in r["result"].lower())
        divergences = sum(1 for r in records if "divergência" in r["result"].lower())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Bens cadastrados no setor", expected)
        c2.metric("Leituras confirmadas", confirmed)
        c3.metric("Identificações pendentes", pending)
        c4.metric("Possíveis divergências", divergences)
        if records:
            st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
        else:
            st.info("Esta vistoria ainda não tem leituras.")
        pdf = build_pdf(inspection, inspection["department_name"], records)
        st.download_button(
            "Gerar / baixar relatório PDF",
            data=pdf,
            file_name=f"relatorio_vistoria_{inspection['id']}.pdf",
            mime="application/pdf",
            type="primary",
        )
        st.caption("O protótipo não considera a falta de leitura como prova de ausência física. Evidências fotográficas e revisão humana podem ser incorporadas em etapas futuras.")

else:
    st.subheader("Sobre o protótipo")
    st.markdown("""
**Objetivo:** demonstrar um fluxo de vistoria patrimonial com leitura de QR Code, consulta SQL, registro de ocorrências, painel e relatório PDF.

**Fluxo técnico**
1. O usuário seleciona o departamento e inicia a vistoria.
2. O componente JavaScript acessa a câmera do dispositivo após autorização.
3. A biblioteca `@zxing/browser` decodifica o QR Code.
4. O valor decodificado é devolvido ao Streamlit.
5. Python consulta o SQLite com parâmetros SQL, valida o departamento e registra a leitura.
6. O resultado aparece na tela e pode compor um relatório PDF.

**Limitações**
- Os dados são fictícios e o banco SQLite é local ao processo/ambiente de demonstração.
- O armazenamento do Streamlit Community Cloud não deve ser tratado como persistente; os dados podem ser perdidos.
- Não é um sistema pronto para uso institucional, não inclui autenticação corporativa, controle de permissões, trilha de auditoria robusta nem política de backup.
- Uma leitura de QR confirma o código lido, não a condição física do bem nem sua autenticidade.
- O protótipo não usa reconhecimento por IA de fotografias; essa possibilidade pode ser avaliada em uma etapa futura.
""")
    st.info("Para implantação real, use uma arquitetura com banco persistente, servidor e armazenamento adequados ao ambiente de trabalho. Consulte o README para o escopo da Versão 2.")


# Note: component declares a value on every render; clear a stale value after a read via last_scan session state.
