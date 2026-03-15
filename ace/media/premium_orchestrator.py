from typing import Dict, Tuple, List, Optional
import os
import uuid
import datetime

class PremiumMediaOrchestrator:
    """
    Orquestra a geração de mídia premium (vídeo, imagem, carrossel, voz).
    Usa direção criativa, hipóteses e intenções do ciclo para produzir
    conteúdo de nível cinematográfico. Os métodos de geração são placeholders
    prontos para integração com APIs externas (Sora 2, Runway Gen-4.5, ElevenLabs).
    """

    def __init__(self, output_dir: str = "ace_media_output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    # --------------------------------------------------
    # Helper para criar nomes únicos de mídia
    # --------------------------------------------------
    def _media_filename(self, prefix: str, ext: str) -> str:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}_{uuid.uuid4().hex[:8]}.{ext}"

    # --------------------------------------------------
    # Geração de imagem premium (carrossel ou story)
    # --------------------------------------------------
    def generate_image(self, intent: Dict) -> str:
        """
        Gera uma imagem estática de alta qualidade (usado para carrossel ou story).
        Placeholder para integração com modelos de imagem generativa.
        """
        # coletar parâmetros
        palette = intent.get("palette", "gold_black")
        visual_mood = intent.get("visual_mood", "cinematic_dark")
        text = intent.get("trend", "disciplina e prosperidade")
        style = intent.get("style", "autoridade")

        # em um sistema real, chamar API de imagem aqui
        # ex.: image_path = call_image_api(text, palette, visual_mood, style)

        # placeholder: criar arquivo vazio
        filename = self._media_filename("image", "jpg")
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "wb") as f:
            f.write(b"\x00")  # placeholder

        return filepath

    # --------------------------------------------------
    # Geração de vídeo premium (reel)
    # --------------------------------------------------
    def generate_video(self, intent: Dict) -> str:
        """
        Gera um vídeo premium com voz e música. Placeholder para integração.
        """
        trend = intent.get("trend", "disciplina e prosperidade")
        style = intent.get("style", "autoridade")
        visual_mood = intent.get("visual_mood", "cinematic_dark")
        hook = intent.get("angle", "verdade")

        # In real implementation, call external video generation API
        # e.g. video_path = call_video_api(trend, style, visual_mood, hook)

        # Placeholder: create empty mp4 file
        filename = self._media_filename("video", "mp4")
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "wb") as f:
            f.write(b"\x00")

        return filepath

    # --------------------------------------------------
    # Geração de carrossel premium
    # --------------------------------------------------
    def generate_carousel(self, intent: Dict) -> List[str]:
        """
        Gera múltiplas imagens para um carrossel de 5 slides.
        """
        slides = []
        for i in range(5):
            # adapt slide text conforme índice (hook, problema, insight, solução, CTA)
            sub_intent = intent.copy()
            sub_intent["slide_index"] = i
            slide_path = self.generate_image(sub_intent)
            slides.append(slide_path)
        return slides

    # --------------------------------------------------
    # Função principal de orquestração
    # --------------------------------------------------
    def build_media_package(self, intent: Dict) -> Tuple[str, Optional[List[str]]]:
        """
        Constrói um pacote de mídia com base no tipo de conteúdo solicitado:
        - reel: gera vídeo
        - carrossel: gera lista de imagens
        - story: gera uma imagem única (pode ser reaproveitada)
        Retorna o caminho do vídeo e/ou a lista de slides.
        """
        content_type = intent.get("content_type", "reel")
        if content_type == "reel":
            video_path = self.generate_video(intent)
            return (video_path, None)

        if content_type == "carrossel":
            slides = self.generate_carousel(intent)
            return ("", slides)

        if content_type == "story":
            img_path = self.generate_image(intent)
            return ("", [img_path])

        # default fallback
        img_path = self.generate_image(intent)
        return ("", [img_path])


# Instância global (opcional)
premium_media_orchestrator: Optional[PremiumMediaOrchestrator] = None

def install_premium_media_orchestrator(ace_runtime: Any, output_dir: str = "ace_media_output") -> PremiumMediaOrchestrator:
    """
    Instala o premium orchestrator no runtime.
    Deve ser chamado no boot após instalar cycle governor e integrator.
    """
    global premium_media_orchestrator
    premium_media_orchestrator = PremiumMediaOrchestrator(output_dir)
    ace_runtime.premium_media_orchestrator = premium_media_orchestrator
    return premium_media_orchestrator
