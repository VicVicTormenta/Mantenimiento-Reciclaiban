import streamlit as st
import pandas as pd
import os
import glob

st.set_page_config(page_title="RECICLAIBAN - Gestión", layout="wide")
st.title("🛠️ Buscador de Mantenimiento - RECICLAIBAN")

# Muestra la ruta de trabajo (en la nube verás algo como /mount/src/...)
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
                
                # Mapeo de columnas
                col_fallo = next((c for c in df.columns if "Modos" in c or "Fallo" in c), None)
                col_tareas = next((c for c in df.columns if "Medidas" in c), None)
                col_crit = next((c for c in df.columns if "Crit" in c or "idad" in c), None)
                col_esp = next((c for c in df.columns if "Esp" in c or "E p" in c), None)
                col_frec = next((c for c in df.columns if c.strip() == "F" or "Periodicidad" in c), None)
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

                    # Rellenar celdas combinadas
                    cols_a_rellenar = ['Modo de Fallo', 'Criticidad', 'Esp', 'F', 'Form']
                    temp_df[cols_a_rellenar] = temp_df[cols_a_rellenar].ffill()

                    # Limpieza de filas vacías y textos
                    temp_df = temp_df.dropna(subset=['Tarea'])
                    for col in cols_a_rellenar:
                        temp_df[col] = temp_df[col].fillna("N/A").astype(str).str.strip()
                    
                    lista_total.append(temp_df)
        
        if not lista_total:
            return pd.DataFrame(), archivo_real
            
        return pd.concat(lista_total, ignore_index=True), archivo_real
    except Exception as e:
        st.error(f"Error al leer el Excel: {e}")
        return pd.DataFrame(), None

# --- CARGA ---
df, nombre_fich = cargar_datos_completos()

if df is not None and not df.empty:
    st.success(f"✅ Datos cargados con éxito")
    
    # 1. Buscador de texto
    busqueda = st.text_input("🔍 Buscar por fallo o tarea...")
    
    # 2. Configuración de filtros en 4 columnas
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        esp_sel = st.multiselect("⚙️ Especialista", sorted(df['Esp'].unique()), default=df['Esp'].unique())
    with c2:
        # AQUÍ ESTÁ EL FILTRO DE PERIODICIDAD (F)
        frec_sel = st.multiselect("📅 Periodicidad (F)", sorted(df['F'].unique()), default=df['F'].unique())
    with c3:
        crit_sel = st.multiselect("⚠️ Criticidad", sorted(df['Criticidad'].unique()), default=df['Criticidad'].unique())
    with c4:
        form_sel = st.radio("🎓 ¿Formación?", ["Todos", "S", "N"], horizontal=True)

    # 3. Lógica de filtrado (Máscara)
    # Filtro de texto
    mask = (df['Tarea'].str.contains(busqueda, case=False, na=False)) | \
           (df['Modo de Fallo'].str.contains(busqueda, case=False, na=False))
    
    # Aplicar multiselects (incluyendo el de frecuencia F)
    mask &= df['Esp'].isin(esp_sel) 
    mask &= df['F'].isin(frec_sel) 
    mask &= df['Criticidad'].isin(crit_sel)
    
    # Filtro de radio button
    if form_sel != "Todos":
        mask &= (df['Form'] == form_sel)

    # 4. Mostrar resultados
    df_filtrado = df[mask]
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    
    st.caption(f"Mostrando {len(df_filtrado)} tareas de mantenimiento.")

    # Botón extra para tu TFG: Descargar lo que se está viendo
    csv = df_filtrado.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Descargar esta selección (CSV)", csv, "plan_mantenimiento.csv", "text/csv")

else:
    st.warning("No se han encontrado datos. Verifica el archivo Excel en GitHub.")


