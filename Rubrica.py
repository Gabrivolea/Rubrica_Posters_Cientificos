import os
import sys
import streamlit as st
import pandas as pd
import base64
import PyPDF2
import io
import math
import json
from collections import Counter

# --- AUTO-LANZADOR MÁGICO ---
if "STREAMLIT_ARRANCADO" not in os.environ:
    os.environ["STREAMLIT_ARRANCADO"] = "1"
    print("Iniciando la rúbrica interactiva multiproyecto CESAG...")
    os.system(f'streamlit run "{sys.argv[0]}"')
    sys.exit()

st.set_page_config(page_title="Rúbrica de Evaluación CESAG", page_icon="📝", layout="wide")

# --- RUTAS ABSOLUTAS PARA ASEGURAR QUE LOS JSON SE GUARDAN EN LA MISMA CARPETA ---
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_EVAL = os.path.join(DIRECTORIO_BASE, "evaluaciones_guardadas.json")
ARCHIVO_CONFIG = os.path.join(DIRECTORIO_BASE, "config_rubrica.json")

# ---------------- FUNCIÓN DE AUTOGUARDADO ----------------
def guardar_datos_en_disco():
    try:
        with open(ARCHIVO_EVAL, "w", encoding="utf-8") as f:
            json.dump(st.session_state.evaluaciones, f, ensure_ascii=False, indent=4)
        with open(ARCHIVO_CONFIG, "w", encoding="utf-8") as f:
            json.dump(st.session_state.rubrica_dinamica, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Error al guardar los archivos JSON: {e}")

# ----- FUNCIÓN AL PULSAR UN BOCADILLO: INSERTA EL TEXTO EN EL ÍTEM -----
def insertar_comentario_bocadillo(item_key, texto_bocadillo, i):
    com_key = f"com_{i}_{item_key}"
    actual = st.session_state.get(com_key, "")
    nuevo_texto = f"{actual} | {texto_bocadillo}".strip(" |") if actual else texto_bocadillo
    st.session_state[com_key] = nuevo_texto

# ---------------- LÓGICA MATEMÁTICA DE PLAGIO LOCAL (COSENO) ----------------
def text_to_vector(text):
    words = [w for w in text.lower().split() if len(w) > 3]
    return Counter(words)

def calcular_similitud_coseno(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator: return 0.0
    else: return float(numerator) / denominator

def extraer_texto_pdf(archivo_bytes):
    try:
        lector = PyPDF2.PdfReader(io.BytesIO(archivo_bytes))
        texto = ""
        for pagina in lector.pages:
            texto += pagina.extract_text() + "\n"
        return texto
    except:
        return ""

# ---------------- GENERADOR DE BOLETÍN HTML ----------------
def generar_html_alumno(eval_actual, rubrica_dinamica, nota_final, total_puntos_max, puntos_obtenidos):
    color_nota = "#27AE60" if nota_final >= 5 else "#E74C3C" 
    color_map = {1: "#E74C3C", 2: "#E67E22", 3: "#F1C40F", 4: "#3498DB", 5: "#27AE60"}
    
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Informe de Evaluación - {eval_actual['alumno']}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #F4F7F6; color: #333; line-height: 1.6; padding: 30px 10px; }}
            .container {{ max-width: 800px; margin: auto; background: #FFFFFF; padding: 40px; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); }}
            .header {{ border-bottom: 3px solid #2980B9; padding-bottom: 20px; margin-bottom: 30px; text-align: center; }}
            .header h1 {{ margin: 0; color: #2C3E50; font-size: 28px; }}
            .header h2 {{ margin: 10px 0 0 0; color: #7F8C8D; font-weight: normal; font-size: 20px; }}
            .score-box {{ display: flex; justify-content: space-around; background: #F8F9FA; padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #E9ECEF; }}
            .score-item {{ text-align: center; }}
            .score-value {{ font-size: 36px; font-weight: bold; color: {color_nota}; }}
            .score-label {{ font-size: 14px; color: #7F8C8D; text-transform: uppercase; letter-spacing: 1px; }}
            .section {{ margin-bottom: 25px; }}
            .section h3 {{ background: #ECF0F1; color: #2980B9; padding: 10px 15px; border-radius: 6px; font-size: 16px; margin-bottom: 15px; }}
            .item {{ margin-bottom: 8px; font-size: 14.5px; display: flex; align-items: flex-start; }}
            .score-badge {{ padding: 3px 8px; border-radius: 4px; font-weight: bold; color: white; margin-right: 12px; font-size: 13px; min-width: 35px; text-align: center; display: inline-block; }}
            .weight-text {{ font-size: 12px; color: #7F8C8D; font-weight: bold; margin-left: 6px; text-transform: uppercase; }}
            .comentario-item {{ margin-top: 4px; margin-bottom: 12px; margin-left: 45px; padding: 6px 12px; background-color: #F8F9F9; border-left: 3px solid #BDC3C7; font-style: italic; color: #5D6D7E; font-size: 13.5px; }}
            .obs-final {{ margin-top: 40px; background: #FEF9E7; padding: 25px; border-radius: 8px; border: 1px solid #F4D03F; }}
            .obs-final h3 {{ margin-top: 0; color: #D4AC0D; font-size: 18px; border-bottom: 1px solid #F1C40F; padding-bottom: 10px; }}
            .obs-text {{ font-size: 15px; color: #555; white-space: pre-line; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>INFORME DE EVALUACIÓN - CESAG</h1>
                <h2>Alumno / Grupo: <strong>{eval_actual['alumno']}</strong></h2>
            </div>
            
            <div class="score-box">
                <div class="score-item">
                    <div class="score-value">{nota_final:.2f} / 10</div>
                    <div class="score-label">Calificación Final</div>
                </div>
                <div class="score-item">
                    <div class="score-value" style="color:#34495E;">{puntos_obtenidos}/{total_puntos_max}</div>
                    <div class="score-label">Puntos Ponderados</div>
                </div>
                <div class="score-item">
                    <div class="score-value" style="color:#E67E22;">{eval_actual.get('plagio', 0)}%</div>
                    <div class="score-label">Similitud (Plagio)</div>
                </div>
                <div class="score-item">
                    <div class="score-value" style="color:#9B59B6;">{eval_actual.get('ia', 0)}%</div>
                    <div class="score-label">Uso de IA</div>
                </div>
            </div>
    """
    for sec in rubrica_dinamica:
        if not sec["visible"]: continue
        criterios_visibles = [c for c in sec["criterios"] if c["visible"]]
        if not criterios_visibles: continue
        
        html += f'<div class="section"><h3>{sec["nombre"]}</h3>'
        for crit in criterios_visibles:
            key = crit["id"]
            texto_criterio = crit["texto"]
            peso = crit.get("peso", 1)
            
            valor_num = eval_actual["respuestas"].get(key, "No evaluado")
            if isinstance(valor_num, bool): valor_num = 5 if valor_num else 1
            
            txt_peso = f"<span class='weight-text'>(Peso: x{peso})</span>" if peso != 1 else ""
            
            if valor_num == "No evaluado":
                html += f'<div class="item"><span class="score-badge" style="background-color: #95A5A6;">N/E</span><span class="text" style="color: #7F8C8D;">{texto_criterio} {txt_peso}</span></div>'
            else:
                badge_color = color_map.get(valor_num, "#7F8C8D")
                html += f'<div class="item"><span class="score-badge" style="background-color: {badge_color};">{valor_num} / 5</span><span class="text">{texto_criterio} {txt_peso}</span></div>'
            
            com_item = eval_actual.get("comentarios_items", {}).get(key, "").strip()
            if com_item:
                html += f'<div class="comentario-item">↳ {com_item}</div>'
        html += '</div>'
        
    obs_finales = eval_actual.get("observaciones", "").strip()
    if obs_finales:
        html += f"""
            <div class="obs-final">
                <h3>Observaciones Finales y Conclusión</h3>
                <div class="obs-text">{obs_finales}</div>
            </div>
        """
    html += "</div></body></html>"
    return html

# ---------------- FUNCIONES DE HISTORIAL OBS ----------------
def aplicar_historial_obs(i):
    sel_key = f"sel_obs_{i}"
    com_key = f"obs_{i}"
    sel = st.session_state.get(sel_key)
    if sel and sel not in ["--- Vacío ---", "Autocompletar..."]:
        actual = st.session_state.get(com_key, "")
        nuevo_texto = f"{actual}\n• {sel}".strip() if actual else f"• {sel}"
        st.session_state[com_key] = nuevo_texto
        st.session_state[sel_key] = "Autocompletar..."

# ---------------- ESTILOS CSS ESTABLES + DISEÑO DE BOCADILLOS ----------------
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    .seccion-titulo { font-size: 16px; font-weight: bold; color: #2E86C1; margin-top: 20px; margin-bottom: 10px; border-bottom: 1px solid #e0e0e0; padding-bottom: 3px; }
    .caja-nota { border: 2px solid #888888; padding: 10px; text-align: center; border-radius: 8px; margin-top: 10px; }
    div[data-testid="InputInstructions"] { display: none !important; visibility: hidden !important; }
    div[data-testid="stTextInput"] input { padding: 4px 10px !important; font-size: 13px !important; }
    
    .edit-row { background-color: #f8f9f9; padding: 8px; border-radius: 6px; margin-bottom: 4px; border: 1px solid #e5e7e9; }
    .edit-section { background-color: #ebf5fb; padding: 10px; border-radius: 6px; margin-top: 15px; margin-bottom: 5px; border-left: 4px solid #3498db; }
    
    /* DISEÑO EXCLUSIVO PARA LOS BOCADILLOS AL LADO DE CADA ÍTEM */
    div[data-testid="stTextInput"] + div div[data-testid="stHorizontalBlock"] button {
        border-radius: 16px !important;
        background-color: #EBF5FB !important;
        color: #2E86C1 !important;
        border: 1px solid #AED6F1 !important;
        font-size: 11.5px !important;
        padding: 2px 8px !important;
        transition: all 0.15s ease !important;
        margin-top: 2px !important;
    }
    div[data-testid="stTextInput"] + div div[data-testid="stHorizontalBlock"] button:hover {
        background-color: #2E86C1 !important;
        color: white !important;
        border-color: #2E86C1 !important;
    }

    .print-only-score { display: none; }
    @media screen { .cabecera-impresion { display: none !important; } }
    @media print {
        header, .stButton, .stFileUploader, iframe, .stProgress, [data-testid="stToolbar"], div[data-testid="stSelectbox"], .stTabs, .stAlert, div[data-testid="stToggle"] { display: none !important; }
        * { color: black !important; background: white !important; font-family: 'Times New Roman', serif !important; }
        body, .stApp, .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
        .stColumn { width: 100% !important; display: block !important; flex: none !important; }
        div[data-testid="stVerticalBlock"] > div > div { height: auto !important; max-height: none !important; overflow: visible !important; }
        textarea, input { border: none !important; background: transparent !important; resize: none !important; box-shadow: none !important; padding-left: 0 !important; padding-top: 0 !important; }
        textarea:empty, input[value=""] { display: none !important; }
        .seccion-titulo { color: black !important; border-bottom: 1px solid black !important; font-size: 12pt !important; margin-top: 15px !important; }
        .caja-nota { border: 2px solid black !important; }
        .print-only-score { display: inline-block !important; font-weight: bold; margin-right: 10px; font-size: 12pt; border: 1px solid black; padding: 2px 6px; border-radius: 4px; }
        .cabecera-impresion { display: block !important; text-align: center; font-size: 18pt; font-weight: bold; border-bottom: 3px solid black; margin-bottom: 20px; padding-bottom: 10px; }
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- NUEVA DATA BASE ORIGINAL ----------------
rubrica_base = {
    "1. Portada y título": [
        "1. El título está alineado con los objetivos y la metodología de estudio",
        "2. Incluye un título corto (< 25 palabras) y no presenta errores en el título o en el nombre del departamento."
    ],
    "2. Formato y presentación": [
        "1. Utiliza la plantilla",
        "2. Incluye todos los epígrafes",
        "3. El trabajo presenta orden y claridad"
    ],
    "3. Estructura general": [
        "1. Incluye el apartado de introducción, Objetivos",
        "2. Incluye el apartado de Metodología",
        "3. Incluye Resultados y Discusión",
        "4. Incluye Conclusiones"
    ],
    "4. Introducción y marco teórico (I)": [
        "1. Incluye los antecedentes del tema estudiado",
        "2. Formula y explica claramente el problema de estudio y lo justifica",
        "4. Describe la importancia de la investigación y presenta los propósitos del estudio",
        "6. Incluye referencias bibliográficas"
    ],
    "5. Objetivos e hipótesis": [
        "1. Los objetivos principales incluyen una o dos variables dependientes y una o dos variables independientes",
        "2. El objetivo menciona la población diana",
        "3. Usa los verbos adecuados, en función del tipo de investigación (de comparación, de correlación o de causalidad)"
    ],
    "6. Métodos (estructura general)": [
        "1. Incluye un apartado de Diseño de Investigación",
        "2. Incluye un apartado de Muestra",
        "3. Incluye un apartado de Procedimientos e Instrumentos"
    ],
    "7. Métodos (procedimientos e instrumentos)": [
        "1. Contiene la información necesaria para poder ser replicado",
        "2. Se detallan las características de los instrumentos utilizados"
    ],
    "8. Métodos (muestra)": [
        "1. Se mencionan datos sociodemográficos y antropométricos de la muestra (edad, sexo, peso, altura, IMC, etc.)"
    ],
    "9. Métodos (análisis estadístico)": [
        "1. Se describe la estadística descriptiva utilizada",
        "2. Se habla sobre las pruebas estadísticas inferenciales empleadas (t-test o equivalente no paramétrico) y correlaciones",
        "3. La estadística es la correcta para los objetivos de estudio"
    ],
    "10. Resultados (estructura general)": [
        "1. Ordena la información en tablas y figuras",
        "2. Aporta datos de centralidad y varianza (medias y DE) de cada una de las variables"
    ],
    "11. Resultados (tablas y figuras)": [
        "1. Auto explicativas",
        "2. Incluyen las unidades de las variables",
        "3. No aparecen pixeladas (recomendable que sean vectoriales)"
    ],
    "12. Discusión": [
        "1. Se diferencia claramente de los resultados (se aportan justificaciones y explicaciones a los hallazgos)",
        "2. No incluye explicaciones basadas en su propia experiencia",
        "3. Incluye un buen número de fuentes bibliográficas (más de 5 fuentes) y/o citas a sus propias figuras y tablas.",
        "5. Se discuten todos los resultados relevantes, alineados con el objetivo"
    ],
    "13. Conclusiones": [
        "1. Responden directamente a los objetivos planteados",
        "2. No incluyen referencias bibliográficas"
    ],
    "14. Referencias bibliográficas": [
        "1. Proporciona referencias bibliográficas según la normativa APA (sangría francesa, revistas en cursiva, etc).",
        "2. Todas las referencias están citadas en el texto",
        "3. Todas las citas del texto están referenciadas en la lista de referencias bibliográficas",
        "4. Las referencias son de publicaciones de calidad (SJR)"
    ],
    "15. Redacción y uso del lenguaje": [
        "1. Párrafos largos, que incluyen ideas bien diferencias",
        "2. Emplea frases cortas fáciles de comprender, simplificando el lenguaje y no abusando de las frases subordinadas",
        "3. No usa sinónimos para las variables y otros términos importantes (es preciso con la terminología)"
    ],
    "16. Presentación del póster científico": [
        "1. Lo presenta en el formato adecuado (PowerPoint y A4)",
        "2. Incluye todos los apartados (esquema IMRC)",
        "3. Presenta orden y claridad",
        "4. Usa más figuras que tablas en la presentación de los resultados",
        "5. Los gráficos y figuras son vectoriales, no capturas de pantalla",
        "6. Las cartelas se separan de los bordes del papel",
        "7. Combina colores y formas",
        "8. No hay demasiados espacios blancos",
        "9. Emplea elementos conectores o al menos se aprecia el orden de lectura",
        "10. Letra sin serifa (Verdana, Tahoma, Calibri, Arial)",
        "11. La letra tiene el tamaño adecuado",
        "12. Las figuras y tablas son autoexpllicativas e incluyen todos los elementos",
        "13. Se marcan las ideas más importantes de alguna manera (otro color, con negrita,)"
    ]
}

# ---------------- INICIALIZACIÓN Y CARGA DESDE JSON ----------------
if 'rubrica_dinamica' not in st.session_state:
    if os.path.exists(ARCHIVO_CONFIG):
        try:
            with open(ARCHIVO_CONFIG, "r", encoding="utf-8") as f:
                st.session_state.rubrica_dinamica = json.load(f)
        except: pass

if 'rubrica_dinamica' not in st.session_state:
    rubrica_dinamica = []
    for i, (sec_nombre, criterios) in enumerate(rubrica_base.items()):
        seccion = {"id": f"sec_{i}", "nombre": sec_nombre, "visible": True, "criterios": []}
        for j, crit_texto in enumerate(criterios):
            seccion["criterios"].append({"id": f"crit_{i}_{j}", "texto": crit_texto, "visible": True, "peso": 1})
        rubrica_dinamica.append(seccion)
    st.session_state.rubrica_dinamica = rubrica_dinamica

if 'evaluaciones' not in st.session_state:
    if os.path.exists(ARCHIVO_EVAL):
        try:
            with open(ARCHIVO_EVAL, "r", encoding="utf-8") as f:
                st.session_state.evaluaciones = json.load(f)
        except: pass

if 'evaluaciones' not in st.session_state:
    st.session_state.evaluaciones = [{"alumno": "Trabajo 1", "observaciones": "", "respuestas": {}, "comentarios_items": {}, "plagio": 0, "ia": 0}]

if 'idx' not in st.session_state: st.session_state.idx = 0
if 'pdf_actual' not in st.session_state: st.session_state.pdf_actual = None
if 'texto_extraido' not in st.session_state: st.session_state.texto_extraido = ""

if st.session_state.idx >= len(st.session_state.evaluaciones):
    st.session_state.idx = len(st.session_state.evaluaciones) - 1

idx = st.session_state.idx
eval_actual = st.session_state.evaluaciones[idx]
if "comentarios_items" not in eval_actual: eval_actual["comentarios_items"] = {}

# =========================================================
# INTERFAZ GRÁFICA
# =========================================================
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.info("💡 **Navegación:** Usa las **pestañas de aquí abajo** para alternar entre la corrección individual y el detector de plagio de toda la clase.")
with col_head2:
    st.success(f"💾 Guardado automático en: \n\n`{DIRECTORIO_BASE}`")

tab_evaluacion, tab_plagio_cross = st.tabs(["📝 Corrección e Informe Individual", "🔍 Matriz Cruzada de Plagio (Toda la Clase)"])

# ---------------- PESTAÑA 1: EVALUACIÓN INDIVIDUAL ----------------
with tab_evaluacion:
    activar_visor = st.toggle("🖥️ Activar Visor de PDF (Doble Pantalla)", value=False, help="Activa esto si quieres ver el PDF integrado a la derecha.")
    
    if activar_visor:
        col_rubrica, col_visor = st.columns([0.95, 2.05])
    else:
        col_rubrica = st.container()

    if activar_visor:
        with col_visor:
            if st.session_state.pdf_actual is None:
                st.subheader("Visor del Trabajo (PDF)")
                archivo_pdf = st.file_uploader("Sube el PDF del alumno para leerlo aquí", type=["pdf"], key="single_pdf_uploader")
                if archivo_pdf is not None:
                    bytes_pdf = archivo_pdf.read()
                    st.session_state.pdf_actual = base64.b64encode(bytes_pdf).decode('utf-8')
                    st.session_state.texto_extraido = extraer_texto_pdf(bytes_pdf)
                    st.rerun()
            else:
                col_btn, col_exp = st.columns([1, 2])
                with col_btn:
                    if st.button("🔄 Cambiar PDF (Subir otro)", help="Quita el PDF actual para evaluar otro trabajo"):
                        st.session_state.pdf_actual = None
                        st.session_state.texto_extraido = ""
                        st.rerun()
                with col_exp:
                    with st.expander("📋 Copiar texto para escanear similitudes online"):
                        st.text_area("Copia y pega en la herramienta de tu universidad:", st.session_state.texto_extraido, height=150, label_visibility="collapsed")
                    
                pdf_display = f'<iframe src="data:application/pdf;base64,{st.session_state.pdf_actual}#toolbar=1&navpanes=0&view=FitH" width="100%" height="850" style="border: 1px solid #ccc; border-radius: 5px;" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)

    with col_rubrica:
        st.markdown(f"<div class='cabecera-impresion'>INFORME DE EVALUACIÓN<br><span style='font-size: 14pt; font-weight: normal;'>Alumno/Grupo: {eval_actual['alumno']}</span></div>", unsafe_allow_html=True)
        
        modo_edicion = st.toggle("⚙️ Configurar Rúbrica (Modificar textos, Ocultar y Cambiar Pesos)", value=False)
        
        if modo_edicion:
            st.warning("⚠️ **Modo Configuración.** Modifica textos, oculta apartados (`👁️`) o ajusta el **Peso**. Todo se autoguarda.")
            with st.container(height=650):
                for i, sec in enumerate(st.session_state.rubrica_dinamica):
                    st.markdown(f"<div class='edit-section'>", unsafe_allow_html=True)
                    c1, c2 = st.columns([0.05, 0.95])
                    sec["visible"] = c1.checkbox("👁️", value=sec["visible"], key=f"edit_vis_sec_{sec['id']}", help="Ocultar toda la sección")
                    sec["nombre"] = c2.text_input("Título de Sección", value=sec["nombre"], key=f"edit_nom_sec_{sec['id']}", label_visibility="collapsed")
                    
                    if sec["visible"]:
                        for j, crit in enumerate(sec["criterios"]):
                            st.markdown(f"<div class='edit-row'>", unsafe_allow_html=True)
                            cc1, cc2, cc3 = st.columns([0.05, 0.80, 0.15])
                            crit["visible"] = cc1.checkbox("👁️", value=crit.get("visible", True), key=f"edit_vis_crit_{crit['id']}", help="Ocultar este ítem")
                            crit["texto"] = cc2.text_input("Ítem", value=crit["texto"], key=f"edit_nom_crit_{crit['id']}", label_visibility="collapsed")
                            crit["peso"] = cc3.number_input("Peso (x)", min_value=0, max_value=10, value=int(crit.get("peso", 1)), key=f"edit_p_crit_{crit['id']}", step=1)
                            st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<h3 style='margin-top: -15px;'>Hoja de Evaluación</h3>", unsafe_allow_html=True)
            eval_actual["alumno"] = st.text_input("Nombre del Alumno / Grupo", value=eval_actual["alumno"])
            
            total_puntos_max = 0
            puntos_obtenidos = 0
            
            with st.container(height=650):
                for sec in st.session_state.rubrica_dinamica:
                    if not sec["visible"]: continue 
                    criterios_visibles = [c for c in sec["criterios"] if c["visible"]]
                    if not criterios_visibles: continue
                    
                    st.markdown(f"<div class='seccion-titulo'>🔹 {sec['nombre']}</div>", unsafe_allow_html=True)
                    
                    for crit in criterios_visibles:
                        key = crit["id"]
                        texto_criterio = crit["texto"]
                        peso = int(crit.get("peso", 1))
                        
                        sel_key = f"sel_{idx}_{key}"
                        com_key = f"com_{idx}_{key}"
                        
                        val_previo = eval_actual["respuestas"].get(key, "No evaluado")
                        if isinstance(val_previo, bool): val_previo = 5 if val_previo else 1
                        if sel_key not in st.session_state: st.session_state[sel_key] = val_previo
                        val_actual = st.session_state.get(sel_key, "No evaluado")
                        
                        if com_key not in st.session_state: 
                            st.session_state[com_key] = eval_actual["comentarios_items"].get(key, "")
                        
                        # Extraer el historial específico de ESTE ÍTEM concreto
                        historial_item = set()
                        for ev in st.session_state.evaluaciones:
                            com_previo = ev.get("comentarios_items", {}).get(key, "").strip()
                            if com_previo:
                                for linea in com_previo.split('|'):
                                    linea_limpia = linea.strip()
                                    if linea_limpia: historial_item.add(linea_limpia)
                        
                        ancho_izq = 8.5 if not activar_visor else 5.5
                        col_txt, col_val = st.columns([ancho_izq, 1.5])
                        
                        txt_peso = f" (Peso: x{peso})" if peso != 1 else ""
                        texto_nota = f"[{val_actual}/5]{txt_peso}" if val_actual != "No evaluado" else f"[N/E]{txt_peso}"
                        color_etiqueta = "#2E86C1" if val_actual != "No evaluado" else "#95A5A6"
                        
                        with col_txt:
                            st.markdown(f"<div style='display:flex; align-items:flex-start; margin-bottom: 2px;'><span class='print-only-score'>{texto_nota} </span><span style='color: {color_etiqueta}; font-weight: bold; margin-right: 8px; font-size: 14px;'>{texto_nota}</span><p style='font-size: 13.5px; margin-top: 0px; margin-bottom: 0px; line-height: 1.2;'>{texto_criterio}</p></div>", unsafe_allow_html=True)
                            st.text_input("Comentario", key=com_key, placeholder="📝 Escribe una nota para este ítem...", label_visibility="collapsed")
                            
                            # --- BOCADILLOS INTERACTIVOS AL LADO DE CADA ÍTEM ---
                            if historial_item:
                                lista_pills = sorted(list(historial_item))
                                chunks = [lista_pills[x:x+3] for x in range(0, len(lista_pills), 3)]
                                for c_idx, chunk in enumerate(chunks):
                                    cols_bocadillos = st.columns(len(chunk))
                                    for idx_pill, texto_pill in enumerate(chunk):
                                        with cols_bocadillos[idx_pill]:
                                            st.button(f"💬 {texto_pill}", key=f"pill_{idx}_{key}_{texto_pill}_{c_idx}_{idx_pill}", on_click=insertar_comentario_bocadillo, args=(key, texto_pill, idx), use_container_width=True)
                                
                        with col_val:
                            st.selectbox("Nota", options=["No evaluado", 1, 2, 3, 4, 5], key=sel_key, label_visibility="collapsed")
                        
                        val_final = st.session_state[sel_key]
                        eval_actual["respuestas"][key] = val_final
                        eval_actual["comentarios_items"][key] = st.session_state[com_key]
                        
                        if val_final != "No evaluado":
                            total_puntos_max += (5 * peso)
                            puntos_obtenidos += (int(val_final) * peso)
                        
                        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
                            
            if not modo_edicion:
                st.markdown("<div class='seccion-titulo'>🔹 Originalidad e IA</div>", unsafe_allow_html=True)
                p_key = f"plagio_{idx}"
                ia_key = f"ia_{idx}"
                if p_key not in st.session_state: st.session_state[p_key] = int(eval_actual.get("plagio", 0))
                if ia_key not in st.session_state: st.session_state[ia_key] = int(eval_actual.get("ia", 0))
                
                col_p, col_ia = st.columns(2)
                with col_p: st.number_input("% Plagio detectado", min_value=0, max_value=100, key=p_key, step=1)
                with col_ia: st.number_input("% Uso IA detectado", min_value=0, max_value=100, key=ia_key, step=1)
                eval_actual["plagio"] = st.session_state[p_key]
                eval_actual["ia"] = st.session_state[ia_key]

                obs_key = f"obs_{idx}"
                if obs_key not in st.session_state: st.session_state[obs_key] = eval_actual.get("observaciones", "")
                    
                historial_obs = set()
                for ev in st.session_state.evaluaciones:
                    obs_previa = ev.get("observaciones", "").strip()
                    if obs_previa: 
                        for linea in obs_previa.split('\n'):
                            linea_limpia = linea.replace('•', '').strip()
                            if linea_limpia: historial_obs.add(linea_limpia)
                        
                col_título, col_hist_obs = st.columns([3, 1.5])
                with col_título: st.markdown("<div class='seccion-titulo'>🔹 Observaciones Finales</div>", unsafe_allow_html=True)
                with col_hist_obs:
                    opciones_obs = ["Autocompletar..."] + sorted(list(historial_obs)) if historial_obs else ["--- Vacío ---"]
                    st.selectbox("🕒 Autocompletar:", options=opciones_obs, key=f"sel_obs_{idx}", on_change=aplicar_historial_obs, args=(idx,))
                        
                st.text_area("📝 Escribe tus conclusiones globales aquí:", key=obs_key, height=120)
                eval_actual["observaciones"] = st.session_state[obs_key]

    if not modo_edicion:
        st.divider()
        nota_final = (puntos_obtenidos / total_puntos_max) * 10 if total_puntos_max > 0 else 0
        html_boletin = generar_html_alumno(eval_actual, st.session_state.rubrica_dinamica, nota_final, total_puntos_max, puntos_obtenidos)
        
        st.download_button(
            label="📥 Descargar Boletín de este Alumno (Diseño Web)",
            data=html_boletin.encode('utf-8'),
            file_name=f"Boletin_CESAG_{eval_actual['alumno'].replace(' ', '_')}.html",
            mime="text/html",
            use_container_width=True,
            type="primary"
        )
        st.markdown(f"<div class='caja-nota'><h2>Nota Final: {nota_final:.2f} / 10</h2><p><strong>Puntos ponderados obtenidos:</strong> {puntos_obtenidos} de {total_puntos_max} posibles.</p></div>", unsafe_allow_html=True)

        col_prev, col_cent, col_next = st.columns([1, 1, 1])
        with col_prev:
            if st.button("⬅️ Guardar y ver Anterior", use_container_width=True) and idx > 0:
                st.session_state.idx -= 1
                st.rerun()
        with col_cent:
            if st.button("➕ Crear Nueva Evaluación", use_container_width=True):
                nuevo_id = len(st.session_state.evaluaciones) + 1
                st.session_state.evaluaciones.append({"alumno": f"Trabajo {nuevo_id}", "observaciones": "", "respuestas": {}, "comentarios_items": {}, "plagio": 0, "ia": 0})
                st.session_state.idx = len(st.session_state.evaluaciones) - 1
                st.session_state.pdf_actual = None 
                st.session_state.texto_extraido = ""
                st.rerun()
        with col_next:
            if st.button("Guardar y ver Siguiente ➡️", use_container_width=True) and idx < len(st.session_state.evaluaciones) - 1:
                st.session_state.idx += 1
                st.rerun()

        st.write(f"Trabajo {idx + 1} de {len(st.session_state.evaluaciones)} evaluados.")
        st.divider()
        
        # EXPORTACIÓN EXCEL LIMPIA (SOLO NOTAS, SEP PUNTO Y COMA)
        datos_csv = []
        for ev in st.session_state.evaluaciones:
            fila = {"Alumno": ev["alumno"], "% Plagio": f"{ev.get('plagio', 0)}%", "% Uso IA": f"{ev.get('ia', 0)}%", "Observaciones Finales": ev["observaciones"]}
            tot_max, cump = 0, 0
            
            for sec in st.session_state.rubrica_dinamica:
                if not sec["visible"]: continue
                for crit in sec["criterios"]:
                    if not crit["visible"]: continue
                    
                    k = crit["id"]
                    texto = crit["texto"]
                    peso = int(crit.get("peso", 1))
                    sec_nombre = sec["nombre"]
                    
                    valor_num = ev["respuestas"].get(k, "No evaluado")
                    if isinstance(valor_num, bool): valor_num = 5 if valor_num else 1
                    
                    # Guardamos la nota limpia en el Excel. Prescindimos de la columna de comentarios de ítems.
                    fila[f"[{sec_nombre[:12]}...] {texto[:40]}"] = valor_num
                    
                    if valor_num != "No evaluado":
                        tot_max += (5 * peso)
                        cump += (int(valor_num) * peso)
                        
            fila["NOTA FINAL"] = round((cump / tot_max) * 10, 2) if tot_max > 0 else 0
            datos_csv.append(fila)
            
        df_excel = pd.DataFrame(datos_csv)
        st.download_button(
            label="📊 Descargar Resultados de todos los alumnos (Excel/CSV)",
            data=df_excel.to_csv(index=False, sep=';').encode('utf-8-sig'),
            file_name="Evaluaciones_CESAG.csv",
            mime="text/csv",
            use_container_width=True
        )

# ---------------- PESTAÑA 2: MATRIZ CRUZADA DE PLAGIO ----------------
with tab_plagio_cross:
    st.header("🔍 Detector de Copia entre Alumnos (Matriz Cruzada)")
    st.markdown("""
    Arrastra **todos los trabajos de la clase a la vez** en la caja inferior. 
    El sistema comparará todos contra todos matemáticamente y te mostrará una **tabla de doble entrada** indicando el porcentaje de vocabulario idéntico compartido.
    """)
    
    archivos_multiples = st.file_uploader(
        "Sube TODOS los PDFs de la clase juntos (.pdf)", 
        type=["pdf"], 
        accept_multiple_files=True, 
        key="cross_plagiarism_uploader"
    )
    
    if archivos_multiples:
        num_archivos = len(archivos_multiples)
        if num_archivos < 2:
            st.info("Sube al menos 2 archivos para poder cruzarlos y buscar similitudes.")
        else:
            with st.spinner("Analizando documentos y calculando similitudes de la clase..."):
                textos_completos = {}
                vectores_completos = {}
                
                for f in archivos_multiples:
                    nombre_corto = f.name.replace(".pdf", "")
                    texto = extraer_texto_pdf(f.read())
                    textos_completos[nombre_corto] = texto
                    vectores_completos[nombre_corto] = text_to_vector(texto)
                
                nombres = list(textos_completos.keys())
                matriz_datos = []
                
                for fila_nom in nombres:
                    fila_resultado = {"Trabajo / Alumno": fila_nom}
                    for col_nom in nombres:
                        if fila_nom == col_nom:
                            fila_resultado[col_nom] = "100.0%"
                        else:
                            sim = calcular_similitud_coseno(vectores_completos[fila_nom], vectores_completos[col_nom])
                            fila_resultado[col_nom] = f"{sim * 100:.1f}%"
                    matriz_datos.append(fila_resultado)
                
                df_matriz = pd.DataFrame(matriz_datos)
                df_matriz.set_index("Trabajo / Alumno", inplace=True)
                
                st.subheader("📊 Tabla de Similitudes Cruzadas (%)")
                st.markdown("**Cómo leerla:** Busca porcentajes altos. Si la celda supera el **30-40%**, indica que hay una coincidencia de vocabulario inusualmente alta.")
                
                st.dataframe(df_matriz, use_container_width=True)
                
                st.markdown("### 🚨 Sospechas detectadas:")
                sospechas = False
                for i in range(len(nombres)):
                    for j in range(i + 1, len(nombres)):
                        n1 = nombres[i]
                        n2 = nombres[j]
                        sim_val = calcular_similitud_coseno(vectores_completos[n1], vectores_completos[n2]) * 100
                        if sim_val > 30.0:
                            st.warning(f"⚠️ **Alta coincidencia:** El trabajo de **{n1}** y el de **{n2}** comparten un **{sim_val:.1f}%** de similitud.")
                            sospechas = True
                
                if not sospechas:
                    st.success("✅ Todo limpio: No se han encontrado trabajos cruzados con coincidencias críticas.")

# =========================================================
# EJECUTAR GUARDADO AL FINAL DE CADA INTERACCIÓN
# =========================================================
guardar_datos_en_disco()