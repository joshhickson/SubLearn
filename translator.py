import deepl
import pysubs2
import logging

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
    try:
        subs = pysubs2.load(filepath)
        original_texts = [line.text for line in subs]
    except Exception as e:
        logging.error(f"Error reading or parsing subtitle file: {filepath}", exc_info=True)
        return None

    if not original_texts:
        logging.warning("Subtitle file contains no text to translate.")
        return []

    try:
        translator = deepl.Translator(api_key)
        logging.info(f"Sending {len(original_texts)} lines to DeepL API for translation to {target_lang}...")

        supported_formality_langs = ["DE", "FR", "IT", "ES", "NL", "PL", "PT-PT", "PT-BR", "RU"]
        if target_lang.upper() in supported_formality_langs:
            result = translator.translate_text(original_texts, target_lang=target_lang, formality="more")
        else:
            result = translator.translate_text(original_texts, target_lang=target_lang)

        translated_texts = [res.text for res in result]
        logging.info("Translation successful.")
        return translated_texts

    except deepl.DeepLException as e:
        logging.error(f"An error occurred with the DeepL API: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during translation: {e}", exc_info=True)
        return None
