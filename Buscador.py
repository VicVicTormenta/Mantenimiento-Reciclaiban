import streamlit as st
import pandas as pd
import os
import glob

st.set_page_config(page_title="RECICLAIBAN - Gestión", layout="wide")
st.title("🛠️ Buscador de Mantenimiento - RECICLAIBAN")

st.info(f"📂 **Ruta de trabajo:** `{os.getcwd()}`")

def encontrar_cabecera(df_hoja):
    for i in range(min(len(df_hoja), 40)):
        fila = df_hoja.iloc[i].astype(str).values
        if any('Medidas preventivas' in str(s) for s in fila):
            return i
    return None

@st.cache_data
def cargar_datos_completos():
    archivos_excel = glob.glob("*.xlsx")
    archivo_real = next((f for f in archivos_excel if "fichasmantenimiento" in f.lower()), None)
    
    if not archivo_real:
        return None, None
        
    try:
        dict_hojas = pd.read_excel(archivo_real, sheet_name=None, header=None, engine='openpyxl')
        lista_total = []
        
        for nombre_hoja, df_raw in dict_hojas.items():
            idx = encontrar_cabecera(df_raw)
            if idx is not None:
                df = df_raw.iloc[idx:].copy()
                df.columns = df.iloc[0]
                df = df[1:]
                
                # Limpiar nombres de columnas
                df.columns = df.columns.astype(str).str.replace('\n', ' ').str.strip()
                
                # Mapeo de columnas incluyendo Modos de Fallo
                col_fallo = next((c for c in df.columns if "Modos" in c or "Fallo" in c), None)
                col_tareas = next((c for c in df.columns if "Medidas" in c), None)
                col_crit = next((c for c in df.columns if "Crit" in c or "idad" in c), None)
                col_esp = next((c for c in df.columns if "Esp" in c or "E p" in c), None)
                col_frec = next((c for c in df.columns if c.strip() == "F"), None)
                col_form = next((c for c in df.columns if "Form" in c or "F o r m" in c), None)

                if col_tareas:
                    temp_df = pd.DataFrame({
                        'Equipo': nombre_hoja.upper(),
                        'Modo de Fallo': df[col_fallo] if col_fallo else "N/A",
                        'Tarea': df[col_tareas],
                        'Criticidad': df[col_crit] if col_crit else None,
                        'Esp': df[col_esp] if col_esp else None,
                        'F': df[col_frec] if col_frec else None,
                        'Form': df[col_form] if col_form else None
                    })

                    # --- CORRECCIÓN DE CELDAS COMBINADAS ---
                    # Ahora rellenamos también el Modo de Fallo hacia abajo
                    cols_a_rellenar = ['Modo de Fallo', 'Criticidad', 'Esp', 'F', 'Form']
                    temp_df[cols_a_rellenar] = temp_df[cols_a_rellenar].ffill()

                    # Eliminar filas sin tarea real
                    temp_df = temp_df.dropna(subset=['Tarea'])
                    
                    # Limpieza de textos
                    for col in cols_a_rellenar:
                        temp_df[col] = temp_df[col].fillna("N/A").astype(str).str.strip()
                    
                    lista_total.append(temp_df)
        
        return pd.concat(lista_total, ignore_index=True) if lista_total else pd.DataFrame(), archivo_real
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(), None

# --- CARGA Y RENDER ---
df, nombre_fich = cargar_datos_completos()

if df is not None and not df.empty:
    st.success(f"✅ Datos cargados de: `{nombre_fich}`")
    
    # Buscador de texto
    busqueda = st.text_input("🔍 Buscar por fallo o tarea (ej: 'patinaje', 'motor', 'aceite')...")
    
    # Filtros laterales o en columnas
    c1, c2, c3 = st.columns(3)
    with c1:
        esp_sel = st.multiselect("Especialista", sorted(df['Esp'].unique()), default=df['Esp'].unique())
    with c2:
        crit_sel = st.multiselect("Criticidad", sorted(df['Criticidad'].unique()), default=df['Criticidad'].unique())
    with c3:
        form_sel = st.radio("¿Formación?", ["Todos", "S", "N"], horizontal=True)

    # Filtrado lógico
    # Buscamos la palabra tanto en la Tarea como en el Modo de Fallo
    mask = (df['Tarea'].str.contains(busqueda, case=False, na=False)) | \
           (df['Modo de Fallo'].str.contains(busqueda, case=False, na=False))
    
    mask &= df['Esp'].isin(esp_sel) & df['Criticidad'].isin(crit_sel)
    
    if form_sel != "Todos":
        mask &= (df['Form'] == form_sel)

    # Mostrar tabla final
    st.dataframe(df[mask], use_container_width=True, hide_index=True)
    
    st.caption(f"Mostrando {len(df[mask])} tareas de mantenimiento.")
else:
    st.warning("No se han encontrado datos. Comprueba que el Excel tenga la columna 'Modos de Fallo'.")