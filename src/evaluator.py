import json
import csv
import os
from datetime import datetime
from src.chain import AssistantChain
from src.guardrails import GuardrailSystem

OUTPUT_DIR = "output"
GRAFICOS_DIR = os.path.join(OUTPUT_DIR, "graficos")


def _salvar_csv(resultados: list, caminho: str):
    if not resultados:
        return
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=resultados[0].keys())
        writer.writeheader()
        writer.writerows(resultados)


def _gerar_graficos(metricas: dict):
    try:
        import matplotlib.pyplot as plt

        os.makedirs(GRAFICOS_DIR, exist_ok=True)

        labels = [
            "Acurácia\nClassificação",
            "JSON Válido\n(%)",
            "Bloqueio\nAtaques (%)",
            "Falso\nPositivo (%)",
            "Consistência\n(%)",
        ]
        valores = [
            metricas.get("acuracia_classificacao", 0) * 100,
            metricas.get("taxa_json_valido", 0) * 100,
            metricas.get("taxa_bloqueio_ataques", 0) * 100,
            metricas.get("taxa_falso_positivo", 0) * 100,
            metricas.get("consistencia", 0) * 100,
        ]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(labels, valores, color=["#4CAF50", "#2196F3", "#FF5722", "#FF9800", "#9C27B0"])
        ax.set_ylim(0, 110)
        ax.set_ylabel("Porcentagem (%)")
        ax.set_title("TechStore Smart Support — Métricas de Avaliação")
        for bar, val in zip(bars, valores):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{val:.1f}%",
                ha="center",
                va="bottom",
                fontweight="bold",
            )
        plt.tight_layout()
        plt.savefig(os.path.join(GRAFICOS_DIR, "metricas_gerais.png"), dpi=150)
        plt.close()
        print(f"  Gráfico salvo em {GRAFICOS_DIR}/metricas_gerais.png")
    except ImportError:
        print("  matplotlib não instalado, pulando gráficos.")


def rodar_avaliacao():
    print("\n" + "=" * 60)
    print("   AVALIAÇÃO — TechStore Smart Support · WeAreTheSix")
    print("=" * 60)

    chain = AssistantChain()
    guardrail = GuardrailSystem()

    with open("data/test_dataset.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    with open("data/attack_dataset.json", "r", encoding="utf-8") as f:
        attack_cases = json.load(f)

    resultados = []
    total_corretos = 0
    total_json_valido = 0
    total_testes = len(test_cases)

    print(f"\nRodando {total_testes} casos de teste...\n")

    for i, caso in enumerate(test_cases, 1):
        print(f"  [{i:02d}/{total_testes}] {caso['texto'][:60]}...")
        resultado = {"id": i, "texto": caso["texto"], "tipo_esperado": caso["tipo_esperado"]}

        try:
            saida = chain.processar(caso["texto"])
            tipo_obtido = saida["classificacao"]["tipo"]
            resultado["tipo_obtido"] = tipo_obtido
            resultado["acerto"] = tipo_obtido == caso["tipo_esperado"]
            resultado["json_valido"] = True
            resultado["erro"] = ""

            if resultado["acerto"]:
                total_corretos += 1
            total_json_valido += 1

            status = "✅" if resultado["acerto"] else "❌"
            print(f"     {status} esperado: {caso['tipo_esperado']} | obtido: {tipo_obtido}")

        except Exception as e:
            resultado["tipo_obtido"] = "erro"
            resultado["acerto"] = False
            resultado["json_valido"] = False
            resultado["erro"] = str(e)
            print(f"     erro: {e}")

        resultados.append(resultado)

    print("\nTestando consistência (3x a mesma pergunta)...")
    pergunta_consistencia = "qual o prazo de entrega pra SP?"
    tipos_obtidos = []
    for _ in range(3):
        try:
            saida = chain.processar(pergunta_consistencia)
            tipos_obtidos.append(saida["classificacao"]["tipo"])
        except Exception:
            tipos_obtidos.append("erro")

    consistencia = len(set(tipos_obtidos)) == 1
    print(f"  resultados: {tipos_obtidos} → {'consistente' if consistencia else 'inconsistente'}")

    print(f"\nTestando {len(attack_cases)} ataques...\n")
    ataques_bloqueados = 0
    falsos_positivos = 0
    resultados_ataque = []

    for ataque in attack_cases:
        safe, motivo = guardrail.validar_input(ataque["texto"])
        bloqueado = not safe
        esperado_bloqueado = ataque["esperado"] == "BLOQUEADO"

        if bloqueado and esperado_bloqueado:
            ataques_bloqueados += 1
            status = "✅ bloqueado"
        elif not bloqueado and not esperado_bloqueado:
            status = "✅ passou"
        elif not bloqueado and esperado_bloqueado:
            falsos_positivos += 1
            status = "❌ deveria bloquear"
        else:
            falsos_positivos += 1
            status = "⚠️ falso positivo"

        print(f"  {status}: {ataque['texto'][:60]}...")
        resultados_ataque.append({
            "texto": ataque["texto"],
            "tipo_ataque": ataque["tipo_ataque"],
            "esperado": ataque["esperado"],
            "bloqueado": bloqueado,
            "motivo": motivo,
        })

    metricas = {
        "acuracia_classificacao": total_corretos / total_testes if total_testes else 0,
        "taxa_json_valido": total_json_valido / total_testes if total_testes else 0,
        "taxa_bloqueio_ataques": ataques_bloqueados / len(attack_cases) if attack_cases else 0,
        "taxa_falso_positivo": falsos_positivos / (len(attack_cases) + total_testes),
        "consistencia": 1.0 if consistencia else 0.0,
        "timestamp": datetime.now().isoformat(),
    }

    _salvar_csv(resultados, os.path.join(OUTPUT_DIR, "eval_results.csv"))
    _salvar_csv(resultados_ataque, os.path.join(OUTPUT_DIR, "attack_results.csv"))
    _gerar_graficos(metricas)

    with open(os.path.join(OUTPUT_DIR, "metricas.json"), "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("   MÉTRICAS FINAIS")
    print("=" * 60)
    print(f"  1. Acurácia de classificação : {metricas['acuracia_classificacao']*100:.1f}%")
    print(f"  2. Taxa de JSON válido        : {metricas['taxa_json_valido']*100:.1f}%")
    print(f"  3. Taxa de bloqueio (ataques) : {metricas['taxa_bloqueio_ataques']*100:.1f}%")
    print(f"  4. Taxa de falso positivo     : {metricas['taxa_falso_positivo']*100:.1f}%")
    print(f"  5. Consistência               : {metricas['consistencia']*100:.1f}%")
    print("=" * 60)
    print(f"\nResultados em: {OUTPUT_DIR}/\n")

    return metricas
