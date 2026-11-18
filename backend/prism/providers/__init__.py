"""Swappable providers.

Transcription and generation each sit behind one interface. The concrete class is
chosen by an app setting (PRISM_TRANSCRIPTION_PROVIDER / PRISM_GENERATION_PROVIDER),
so moving to another model or vendor is a config change plus one new module.
"""
