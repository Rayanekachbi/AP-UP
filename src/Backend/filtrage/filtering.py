# ============================================================
# filtering.py - Module 5 : Filtrage et Sécurité
# Contient : FilteringPipeline
# ============================================================

from src.Backend.filtrage.validators import FilterResult, InputValidator, OutputValidator
from config.settings import MESSAGE_QUESTION_BLOQUEE, MESSAGE_REPONSE_BLOQUEE


# ============================================================
# CLASSE : FilteringPipeline
# C'est le chef d'orchestre du module 5.
# Elle appelle d'abord InputValidator, puis OutputValidator.
# Si la question est bloquée en entrée, on s'arrête là.
# ============================================================

class FilteringPipeline:
    def __init__(self):
        # On instancie les deux validators
        self.input_validator = InputValidator()
        self.output_validator = OutputValidator()

    def validate_input(self, question: str, chunk_vectors: list) -> FilterResult:
        """
        Vérifie que la question est liée au corpus du module.

        Paramètres :
        - question      : le texte de la question posée par l'étudiant
        - chunk_vectors : liste des vecteurs de tous les chunks du module

        Retourne un FilterResult.
        """
        return self.input_validator.validate(question, chunk_vectors)

    def validate_output(self, response: str, chunks: list) -> FilterResult:
        """
        Vérifie que la réponse générée est bien ancrée dans le cours.

        Paramètres :
        - response : le texte de la réponse générée par le LLM
        - chunks   : liste des chunks sources avec leurs textes et vecteurs

        Retourne un FilterResult.
        """
        return self.output_validator.validate(response, chunks)

    def run(self, question: str, chunk_vectors: list, response: str, chunks: list) -> FilterResult:
        """
        Méthode orchestratrice principale.
        Appelle validate_input puis validate_output dans l'ordre.
        S'arrête dès le premier échec.

        Paramètres :
        - question      : le texte de la question posée par l'étudiant
        - chunk_vectors : liste des vecteurs de tous les chunks du module
        - response      : le texte de la réponse générée par le LLM
        - chunks        : liste des chunks sources avec leurs textes et vecteurs

        Retourne un FilterResult.
        """

        # --------------------------------------------------
        # ÉTAPE 1 : Filtrage en entrée (validation question)
        # --------------------------------------------------
        input_result = self.validate_input(question, chunk_vectors)

        if not input_result.is_valid:
            # La question est hors-sujet → on s'arrête ici
            # Le RAG n'est pas sollicité
            print(f"[FILTRAGE ENTRÉE] Question bloquée. Score : {input_result.score:.2f}")
            return input_result

        print(f"[FILTRAGE ENTRÉE] Question acceptée. Score : {input_result.score:.2f}")

        # --------------------------------------------------
        # ÉTAPE 2 : Filtrage en sortie (validation réponse)
        # --------------------------------------------------
        output_result = self.validate_output(response, chunks)

        if not output_result.is_valid:
            # La réponse est hallucinée ou non ancrée → on la bloque
            print(f"[FILTRAGE SORTIE] Réponse bloquée. Score : {output_result.score:.2f} | Méthode : {output_result.method}")
            return output_result

        print(f"[FILTRAGE SORTIE] Réponse validée. Score : {output_result.score:.2f} | Méthode : {output_result.method}")

        # --------------------------------------------------
        # ÉTAPE 3 : Tout est valide → on retourne le résultat
        # --------------------------------------------------
        return output_result