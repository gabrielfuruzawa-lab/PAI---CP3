"""
TechStore Smart Support — Assistente Inteligente de Suporte ao Cliente
FIAP · Checkpoint 03 · Prompt Engineering & AI
Grupo: WeAreTheSix
Membros: Alice Soares Lima, André Henrique Camponucci, Dante Daher Garçon,
         Gabriel Kenishi Furuzawa, Jéssica Karolina Xavier Cavalcante, Carlos Marques

Uso:
  python main.py           → modo interativo
  python main.py --eval    → modo avaliação (roda datasets)
"""

import sys
import json
from src.guardrails import GuardrailSystem
from src.chain import AssistantChain

BANNER = """
╔══════════════════════════════════════════════════════╗
║        TechStore Smart Support  🛒                   ║
║     Assistente Inteligente — Alexandra               ║
║       Grupo: WeAreTheSix · FIAP CP03                 ║
║  Digite 'sair' para encerrar | '--eval' para avaliar ║
╚══════════════════════════════════════════════════════╝
"""


def modo_interativo():
    print(BANNER)
    guardrail = GuardrailSystem()
    chain = AssistantChain()

    while True:
        try:
            user_input = input("\n🧑 Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nAté logo! 👋")
            break

        if not user_input:
            continue

        if user_input.lower() in ("sair", "exit", "quit"):
            print("Até logo! 👋")
            break

        # ── CAMADA 1: Input Guard ──
        safe, motivo = guardrail.validar_input(user_input)
        if not safe:
            print(f"\n🛡  Mensagem bloqueada: {motivo}")
            continue

        print("\n⏳ Processando...\n")

        try:
            # ── PIPELINE (3 etapas) ──
            resultado = chain.processar(user_input)

            resposta_texto = resultado["resposta_final"]["resposta"]
            confianca = resultado["resposta_final"]["confianca"]
            acao = resultado["resposta_final"]["acao_sugerida"]
            tipo = resultado["classificacao"]["tipo"]
            urgencia = resultado["classificacao"]["urgencia"]

            # ── CAMADA 3: Output Guard ──
            safe_out, motivo_out = guardrail.validar_output(resposta_texto)
            if not safe_out:
                print("🤖 Alexandra: Olá! Recebemos sua mensagem. Em breve um de nossos atendentes entrará em contato.")
                print(f"   [Sistema: output bloqueado — {motivo_out}]")
                continue

            print(f"🤖 Alexandra: {resposta_texto}")
            print(f"\n   📌 Tipo: {tipo} | Urgência: {urgencia} | Confiança: {confianca}")
            print(f"   ➡️  Ação sugerida: {acao}")

        except ConnectionError as e:
            print(f"\n❌ Erro de conexão: {e}")
            break
        except Exception as e:
            print(f"\n⚠️  Erro inesperado: {e}")


def modo_avaliacao():
    from src.evaluator import rodar_avaliacao
    rodar_avaliacao()


if __name__ == "__main__":
    if "--eval" in sys.argv:
        modo_avaliacao()
    else:
        modo_interativo()
