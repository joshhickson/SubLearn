import deepl
import pysubs2

def translate_subtitle_file(filepath: str, target_lang: str, api_key: str) -> list[str] | None:
    """
    Translates the text content of a subtitle file to a target language.

    Args:
        filepath: The path to the .srt file to be translated.
        target_lang: The target language code (e.g., "EN-US", "DE", "FR").
        api_key: The DeepL API authentication key.

    Returns:
        A list of translated text strings, or None if translation fails.
    """
    print(f"Translating subtitle file: {filepath}")

    try:
        # Load the subtitle file using pysubs2 to easily extract text
        subs = pysubs2.load(filepath)
        original_texts = [line.text for line in subs]
    except Exception as e:
        print(f"Error reading or parsing subtitle file: {e}")
        return None

    if not original_texts:
        print("Subtitle file contains no text to translate.")
        return []

    try:
        # Initialize the DeepL translator
        translator = deepl.Translator(api_key)

        # Translate the text
        # Sending the text as a list is more efficient (one API call)
        print(f"Sending {len(original_texts)} lines to DeepL API for translation to {target_lang}...")
        result = translator.translate_text(
            original_texts,
            target_lang=target_lang,
            formality="more" # As per the project blueprint for a more literal translation
        )

        # Extract the translated text from the result objects
        translated_texts = [res.text for res in result]
        print("Translation successful.")

        return translated_texts

    except deepl.DeepLException as e:
        print(f"An error occurred with the DeepL API: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during translation: {e}")
        return None
