import streamlit as st
from pathlib import Path
import os
from main import speach_to_text, text_analysis, generate_image

# Configuration de la page
st.set_page_config(
    page_title="Synthétiseur de rêves",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé pour un look professionnel
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .step-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        color: #2c3e50;
    }
    .step-card h3 {
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    .step-card p {
        color: #34495e;
        margin-bottom: 0;
    }
    .transcription-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #e1e8ed;
        font-size: 16px;
        line-height: 1.6;
        color: #2c3e50;
    }
    .emotion-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin: 0.5rem;
        transition: transform 0.2s;
        color: #2c3e50;
    }
    .emotion-card:hover {
        transform: translateY(-5px);
    }
    .emotion-card h4 {
        color: #2c3e50;
        margin: 0.5rem 0;
        font-weight: 600;
    }
    .success-message {
        background: linear-gradient(135deg, #a8e6cf 0%, #7fcdcd 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: #2c3e50;
        border-left: 4px solid #27ae60;
    }
    .info-message {
        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: #2c3e50;
        border-left: 4px solid #f39c12;
        font-weight: 500;
    }
    .image-container {
        text-align: center;
        margin: 2rem 0;
    }
    .image-container img {
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
        max-width: 100%;
        height: auto;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.7rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
    }
    .reset-button > button {
        background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 20px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

def remove_temp_file(path: Path):
    try:
        if path.exists():
            path.unlink()
    except Exception as e:
        st.warning(f"⚠️ Impossible de supprimer le fichier temporaire : {e}")

# Initialisation des variables dans session_state
if "texte" not in st.session_state:
    st.session_state.texte = None
if "emotions" not in st.session_state:
    st.session_state.emotions = None
if "image_path" not in st.session_state:
    st.session_state.image_path = None
if "audio_saved_path" not in st.session_state:
    st.session_state.audio_saved_path = None
if "stats_shown" not in st.session_state:
    st.session_state.stats_shown = False

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🌙 Synthétiseur de rêves</h1>
    <p>Transformez vos rêves en images grâce à l'intelligence artificielle</p>
</div>
""", unsafe_allow_html=True)

# Étape 1 : Upload du fichier audio
st.markdown("""
<div class="step-card">
    <h3>📁 Étape 1 : Enregistrement de votre rêve</h3>
    <p>Téléchargez votre fichier audio contenant la description de votre rêve</p>
</div>
""", unsafe_allow_html=True)

audio_file = st.file_uploader(
    "Choisissez votre fichier audio", 
    type=["wav", "mp3", "m4a"],
    help="Formats supportés : WAV, MP3, M4A"
)

# Sauvegarder audio dans temp si uploadé ET pas déjà sauvegardé
if audio_file is not None and st.session_state.audio_saved_path is None:
    temp_audio_dir = Path("temp_audio")
    temp_audio_dir.mkdir(exist_ok=True)
    temp_audio_path = temp_audio_dir / audio_file.name
    with open(temp_audio_path, "wb") as f:
        f.write(audio_file.read())
    st.session_state.audio_saved_path = temp_audio_path

if st.session_state.audio_saved_path and not st.session_state.stats_shown:
    st.markdown("""
    <div class="success-message">
        ✅ Fichier audio téléchargé avec succès !
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**🎵 Aperçu de votre enregistrement :**")
    st.audio(st.session_state.audio_saved_path)

# Étape 2 : Transcription et analyse
if st.session_state.audio_saved_path and not st.session_state.stats_shown:
    st.markdown("""
    <div class="step-card">
        <h3>🔍 Étape 2 : Analyse de votre rêve</h3>
        <p>Lancez la transcription et l'analyse émotionnelle de votre rêve</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Analyser le rêve", key="analyze"):
            with st.spinner("🎯 Transcription du rêve en cours..."):
                try:
                    texte = speach_to_text(str(st.session_state.audio_saved_path), language="fr")
                    st.session_state.texte = texte
                except Exception as e:
                    st.error(f"❌ Erreur lors de la transcription : {e}")
                    remove_temp_file(st.session_state.audio_saved_path)
                    st.session_state.audio_saved_path = None
                    st.stop()

            with st.spinner("🧠 Analyse émotionnelle en cours..."):
                emotions = text_analysis(st.session_state.texte)
                if emotions:
                    st.session_state.emotions = emotions
                    st.session_state.stats_shown = True
                    st.success("✅ Analyse terminée avec succès !")
                    st.rerun()
                else:
                    st.error("❌ Impossible de réaliser l'analyse émotionnelle.")
                    remove_temp_file(st.session_state.audio_saved_path)
                    st.session_state.audio_saved_path = None
                    st.stop()

# Affichage résultats texte et émotions après transcription
if st.session_state.stats_shown:
    st.markdown("---")
    
    # Transcription
    st.markdown("### 📝 Transcription de votre rêve")
    st.markdown(f"""
    <div class="transcription-box">
        {st.session_state.texte}
    </div>
    """, unsafe_allow_html=True)
    
    # Analyse émotionnelle
    st.markdown("### 🎭 Analyse émotionnelle")
    
    cols = st.columns(len(st.session_state.emotions))
    emojis = {
        "heureux": "😊",
        "triste": "😢", 
        "stressé": "😰",
        "fatigué": "😴",
        "neutre": "😐",
        "excité": "🤩",
        "calme": "😌",
        "anxieux": "😟",
        "joyeux": "😄",
        "mélancolique": "😔"
    }
    
    for idx, (emotion, pct) in enumerate(st.session_state.emotions.items()):
        with cols[idx]:
            st.markdown(f"""
            <div class="emotion-card">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">
                    {emojis.get(emotion, '🎭')}
                </div>
                <h4>{emotion.capitalize()}</h4>
                <div style="margin: 1rem 0;">
            """, unsafe_allow_html=True)
            st.progress(min(int(pct), 100))
            st.markdown(f"""
                </div>
                <div style="font-size: 1.2rem; font-weight: bold; color: #667eea;">
                    {pct:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Étape 3 : Génération d'image
    st.markdown("---")
    st.markdown("""
    <div class="step-card">
        <h3>🎨 Étape 3 : Génération de l'image</h3>
        <p>Créez une représentation visuelle de votre rêve</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎨 Générer l'image du rêve", key="generate"):
            with st.spinner("🎯 Génération de l'image en cours..."):
                try:
                    image_path = generate_image(st.session_state.texte)
                    if image_path:
                        st.session_state.image_path = image_path
                        st.success("✅ Image générée avec succès !")
                        st.rerun()
                    else:
                        st.error("❌ La génération de l'image a échoué.")
                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération de l'image : {e}")

# Affichage image générée
if st.session_state.image_path:
    st.markdown("---")
    st.markdown("### 🖼️ Votre rêve visualisé")
    st.markdown(f"""
    <div class="image-container">
        <img src="data:image/png;base64,{st.session_state.image_path}" 
             alt="Image générée à partir de votre rêve"
             style="max-width: 80%; border-radius: 15px; box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);">
    </div>
    """, unsafe_allow_html=True)
    
    if Path(st.session_state.image_path).exists():
        st.image(st.session_state.image_path, caption="🎨 Image générée à partir de votre rêve")

# Messages d'information
if audio_file is None:
    st.markdown("""
    <div class="info-message">
        ℹ️ Veuillez télécharger un fichier audio pour commencer votre analyse de rêve.
    </div>
    """, unsafe_allow_html=True)
elif st.session_state.audio_saved_path and not st.session_state.stats_shown:
    st.markdown("""
    <div class="info-message">
        ℹ️ Cliquez sur "Analyser le rêve" pour démarrer la transcription et l'analyse.
    </div>
    """, unsafe_allow_html=True)
elif st.session_state.stats_shown and not st.session_state.image_path:
    st.markdown("""
    <div class="info-message">
        ℹ️ Cliquez sur "Générer l'image du rêve" pour créer la visualisation.
    </div>
    """, unsafe_allow_html=True)

# Bouton de réinitialisation
st.markdown("---")
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    st.markdown('<div class="reset-button">', unsafe_allow_html=True)
    if st.button("🔄 Nouveau rêve", key="reset"):
        if st.session_state.audio_saved_path:
            remove_temp_file(st.session_state.audio_saved_path)
        # Réinitialiser complètement tous les états
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # Forcer le rechargement complet de la page
        st.markdown(
            '<meta http-equiv="refresh" content="0">',
            unsafe_allow_html=True
        )
        st.stop()
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
    <p>🌙 Synthétiseur de rêves - Powered by AI</p>
    <p><small>Transformez vos rêves en art numérique</small></p>
</div>
""", unsafe_allow_html=True)