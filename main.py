import os
import re
import json
import math
import requests
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def softmax(predictions: dict) -> dict:
    """
    Applique le softmax à un dictionnaire de prédictions brutes.
    Renvoie un dictionnaire avec les mêmes clés et des valeurs en pourcentage (somme = 100).
    """
    exp_values = [math.exp(v) for v in predictions.values()]
    total = sum(exp_values)

    output = {}
    for (sentiment, value), exp_val in zip(predictions.items(), exp_values):
        output[sentiment] = (exp_val / total) * 10

    return output


def speach_to_text(audio_path: str, language="fr") -> str:
    """
    Transcrit l'audio en texte via l'API Groq Whisper.
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=file,
            model="whisper-large-v3-turbo",
            prompt="Extrait le texte de l'audio de la manière la plus factuelle possible",
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"],
            language=language,
            temperature=0.0
        )
        return transcription.text


def clean_json_response(text: str) -> str:
    """
    Supprime les éventuelles balises markdown comme ``` ou ```json dans la réponse du modèle.
    """
    cleaned = re.sub(r"```.*?```", "", text, flags=re.DOTALL).strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    return cleaned


def text_analysis(text: str) -> dict | None:
    """
    Analyse émotionnelle du texte avec Groq.
    Retourne un dict {emotion: pourcentage} ou None si erreur.
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    system_prompt = (
        "Tu es un assistant d'analyse émotionnelle. "
        "Ton but est d'analyser le texte fourni et d'en extraire un score de probabilité pour chaque émotion suivante : "
        "heureux, triste, stressé, fatigué, neutre. "
        "Réponds STRICTEMENT en JSON pur sans balises Markdown ni explications. "
        "Format exact : "
        '{"heureux": 0.0, "triste": 0.0, "stressé": 0.0, "fatigué": 0.0, "neutre": 0.0}'
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyse ce texte : {text}"}
    ]

    print("Envoi au modèle Groq ...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )

    raw_response = response.choices[0].message.content
    print("Réponse brute du modèle :")
    print(raw_response)

    cleaned_response = clean_json_response(raw_response)
    print("Réponse nettoyée :")
    print(cleaned_response)

    try:
        predictions = json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        print("\n❌ Erreur: la réponse du modèle n'est pas un JSON valide.")
        print("Exception:", e)
        print("Réponse reçue (après nettoyage):")
        print(cleaned_response)
        return None

    return softmax(predictions)


def generate_image(prompt: str) -> str | None:
    """
    Génère une image à partir du texte via l'API ClipDrop.
    Retourne le chemin local de l'image sauvegardée, ou None si échec.
    """
    url = "https://clipdrop-api.co/text-to-image/v1"
    headers = {
        "x-api-key": os.environ.get("CLIPDROP_API_KEY"),
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
    }

    print("Envoi du prompt à l'API ClipDrop pour génération d'image ...")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        img_data = response.content
        img_path = "generated_image.png"
        with open(img_path, "wb") as f:
            f.write(img_data)
        print(f"Image générée et sauvegardée dans : {img_path}")
        return img_path
    else:
        print(f"❌ Erreur génération image : {response.status_code} - {response.text}")
        return None


if __name__ == "__main__":
    audio_path = "Enregistrement.m4a"  # Modifie ici si besoin

    print("Extraction de texte en cours ...")
    text = speach_to_text(audio_path, language="fr")
    print(f"✅ Texte extrait : {text}")

    print("\nAnalyse émotionnelle en cours ...")
    analysis = text_analysis(text)

    if analysis:
        print("\n✅ Résultat (pourcentages par émotion) :")
        for emotion, percent in analysis.items():
            print(f"- {emotion}: {percent:.2f}%")

        print("\nGénération de l'image du rêve ...")
        image_path = generate_image(text)
        if image_path:
            print(f"Image disponible ici : {image_path}")
        else:
            print("❌ La génération de l'image a échoué.")
    else:
        print("\n❌ L'analyse n'a pas pu être réalisée.")
