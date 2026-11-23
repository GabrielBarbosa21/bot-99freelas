"""Visualizador do Dashboard e Kanban em modo terminal interativo."""

from bot_99freelas.dashboard.service import dashboard_service
from bot_99freelas.dashboard.kanban import kanban_manager
from bot_99freelas.dashboard.models import TaskStatus


def render_dashboard() -> None:
    metrics = dashboard_service.calculate_metrics()
    columns = kanban_manager.get_board_columns()

    print("\n" + "=" * 65)
    print(" 📊 PAINEL DE CONTROLE - BOT 99FREELAS")
    print("=" * 65)

    print("\n📈 [MÉTRICAS FINANCEIRAS E CONVERSÃO]")
    print(f"  • Faturamento Acumulado: R$ {metrics.total_revenue_earned:,.2f}")
    print(f"  • Pipeline em Negociação: R$ {metrics.pipeline_value:,.2f}")
    print(f"  • Propostas Enviadas: {metrics.proposals_sent_count} | Aceitas: {metrics.accepted_projects_count}")
    print(f"  • Taxa de Conversão: {metrics.conversion_rate_percent}%")

    print("\n🔌 [GESTÃO DE CONEXÕES DIÁRIAS (99FREELAS)]")
    print(f"  • Conexões Gastas Hoje: {metrics.connections_used_today}")
    print(f"  • Conexões Disponíveis Hoje: {metrics.connections_remaining_today}")

    print("\n📋 [QUADRO KANBAN DE PROJETOS E TAREFAS]")
    col_labels = {
        TaskStatus.TODO.value: "📌 A FAZER",
        TaskStatus.IN_PROGRESS.value: "⚡ EM ANDAMENTO",
        TaskStatus.REVIEW.value: "🔍 REVISÃO & HOMOLOGAÇÃO",
        TaskStatus.DONE.value: "✅ CONCLUÍDO",
    }

    for col_key, label in col_labels.items():
        tasks = columns.get(col_key, [])
        print(f"\n--- {label} ({len(tasks)}) ---")
        if not tasks:
            print("    (Nenhuma tarefa nesta etapa)")
        for t in tasks:
            print(f"    [{t.id}] {t.title}")

    print("\n" + "=" * 65 + "\n")


if __name__ == "__main__":
    render_dashboard()
